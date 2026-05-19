"""参考材料 API（含文件上传）"""

import os
import uuid
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from models import reference as ref_model
from models.project import VersionConflict
from services import access as access_svc
from services import auth as auth_svc
from services.audit import log_action
import config

router = APIRouter(prefix="/api/v1")


class ReferenceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    type: str = "其他"
    node_ids: list[int] = []
    failure_mode_ids: list[int] = []
    url: str = ""
    notes: str = ""


class ReferenceUpdate(BaseModel):
    title: str | None = None
    type: str | None = None
    node_ids: list[int] | None = None
    failure_mode_ids: list[int] | None = None
    url: str | None = None
    notes: str | None = None
    expected_version: int | None = None


@router.get("/projects/{project_id}/references")
def list_references(project_id: int, node_id: int = None, user=Depends(auth_svc.require_current_user)):
    access_svc.require_project_access(project_id, user)
    return ref_model.list_references(project_id, node_id)


@router.get("/references/{ref_id}")
def get_reference(ref_id: int, user=Depends(auth_svc.require_current_user)):
    access_svc.require_entity_access("reference", ref_id, user)
    r = ref_model.get_reference(ref_id)
    if r is None:
        raise HTTPException(status_code=404, detail="参考材料不存在")
    return r


@router.post("/projects/{project_id}/references", status_code=201)
def create_reference(project_id: int, body: ReferenceCreate, user=Depends(auth_svc.require_current_user)):
    access_svc.require_project_access(project_id, user, write=True)
    _validate_reference_links(project_id, body.node_ids, body.failure_mode_ids)
    r = ref_model.create_reference(
        project_id=project_id,
        title=body.title,
        type=body.type,
        node_ids=body.node_ids,
        failure_mode_ids=body.failure_mode_ids,
        url=body.url,
        notes=body.notes,
    )
    log_action(project_id, user, "CREATE", "reference", r["id"], r["title"])
    return r


@router.post("/projects/{project_id}/references/upload", status_code=201)
async def upload_reference(
    project_id: int,
    title: str = Form(...),
    type: str = Form("其他"),
    node_ids: str = Form("[]"),
    failure_mode_ids: str = Form("[]"),
    notes: str = Form(""),
    file: UploadFile = File(...),
    user=Depends(auth_svc.require_current_user),
):
    """上传文件作为参考材料"""
    access_svc.require_project_access(project_id, user, write=True)
    ext = Path(file.filename).suffix if file.filename else ""
    if ext.lower() not in config.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    ids = json.loads(node_ids) if node_ids else []
    fm_ids = json.loads(failure_mode_ids) if failure_mode_ids else []
    _validate_reference_links(project_id, ids, fm_ids)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    project_dir = Path(config.UPLOAD_DIR) / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    file_path = project_dir / safe_name

    content = await file.read()
    if len(content) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"文件不能超过 {config.MAX_UPLOAD_MB} MB")
    with open(file_path, "wb") as f:
        f.write(content)

    rel_path = f"{project_id}/{safe_name}"
    r = ref_model.create_reference(
        project_id=project_id,
        title=title,
        type=type,
        node_ids=ids,
        failure_mode_ids=fm_ids,
        file_path=rel_path,
        notes=notes,
    )
    log_action(project_id, user, "CREATE", "reference", r["id"], r["title"])
    return r


@router.put("/references/{ref_id}")
def update_reference(ref_id: int, body: ReferenceUpdate, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("reference", ref_id, user, write=True)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    _validate_reference_links(project_id, updates.get("node_ids"), updates.get("failure_mode_ids"))
    try:
        r = ref_model.update_reference(ref_id, **updates)
    except VersionConflict:
        raise HTTPException(status_code=409, detail="参考资料已被其他用户修改，请刷新后再保存")
    if r is None:
        raise HTTPException(status_code=404, detail="参考材料不存在")
    log_action(project_id, user, "UPDATE", "reference", ref_id, r["title"])
    return r


@router.delete("/references/{ref_id}")
def delete_reference(ref_id: int, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("reference", ref_id, user, write=True)
    file_path = ref_model.delete_reference(ref_id)
    if file_path:
        full_path = Path(config.UPLOAD_DIR) / file_path
        if full_path.exists():
            full_path.unlink()
    log_action(project_id, user, "DELETE", "reference", ref_id, "删除参考资料")
    return {"ok": True}


def _validate_reference_links(project_id: int, node_ids, failure_mode_ids) -> None:
    for node_id in node_ids or []:
        if access_svc.project_id_for_entity("node", node_id) != project_id:
            raise HTTPException(status_code=400, detail="参考资料关联了其他项目的节点")
    for fm_id in failure_mode_ids or []:
        if access_svc.project_id_for_entity("failure", fm_id) != project_id:
            raise HTTPException(status_code=400, detail="参考资料关联了其他项目的失效模式")
