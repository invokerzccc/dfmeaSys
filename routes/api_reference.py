"""参考材料 API（含文件上传）"""

import os
import uuid
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from models import reference as ref_model
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


@router.get("/projects/{project_id}/references")
def list_references(project_id: int, node_id: int = None):
    return ref_model.list_references(project_id, node_id)


@router.get("/references/{ref_id}")
def get_reference(ref_id: int):
    r = ref_model.get_reference(ref_id)
    if r is None:
        raise HTTPException(status_code=404, detail="参考材料不存在")
    return r


@router.post("/projects/{project_id}/references", status_code=201)
def create_reference(project_id: int, body: ReferenceCreate):
    return ref_model.create_reference(
        project_id=project_id,
        title=body.title,
        type=body.type,
        node_ids=body.node_ids,
        failure_mode_ids=body.failure_mode_ids,
        url=body.url,
        notes=body.notes,
    )


@router.post("/projects/{project_id}/references/upload", status_code=201)
async def upload_reference(
    project_id: int,
    title: str = Form(...),
    type: str = Form("其他"),
    node_ids: str = Form("[]"),
    failure_mode_ids: str = Form("[]"),
    notes: str = Form(""),
    file: UploadFile = File(...),
):
    """上传文件作为参考材料"""
    ext = Path(file.filename).suffix if file.filename else ""
    safe_name = f"{uuid.uuid4().hex}{ext}"
    project_dir = Path(config.UPLOAD_DIR) / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    file_path = project_dir / safe_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    rel_path = f"{project_id}/{safe_name}"
    ids = json.loads(node_ids) if node_ids else []
    fm_ids = json.loads(failure_mode_ids) if failure_mode_ids else []
    return ref_model.create_reference(
        project_id=project_id,
        title=title,
        type=type,
        node_ids=ids,
        failure_mode_ids=fm_ids,
        file_path=rel_path,
        notes=notes,
    )


@router.put("/references/{ref_id}")
def update_reference(ref_id: int, body: ReferenceUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    r = ref_model.update_reference(ref_id, **updates)
    if r is None:
        raise HTTPException(status_code=404, detail="参考材料不存在")
    return r


@router.delete("/references/{ref_id}")
def delete_reference(ref_id: int):
    file_path = ref_model.delete_reference(ref_id)
    if file_path:
        full_path = Path(config.UPLOAD_DIR) / file_path
        if full_path.exists():
            full_path.unlink()
    return {"ok": True}
