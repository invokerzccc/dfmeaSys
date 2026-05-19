"""失效模式（DFMEA 工作表）API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from models import failure_mode as fm_model
from models.project import VersionConflict
from services import access as access_svc
from services import auth as auth_svc
from services.audit import log_action

router = APIRouter(prefix="/api/v1")


class FailureCreate(BaseModel):
    function_item_id: int
    mode_desc: str = ""
    local_effect: str = ""
    potential_effect: str = ""
    severity_S: int = Field(default=1, ge=1, le=10)
    classification: str = ""
    potential_cause: str = ""
    occurrence_O: int = Field(default=1, ge=1, le=10)
    prevention_control: str = ""
    detection_control: str = ""
    detection_D: int = Field(default=1, ge=1, le=10)
    recommended_action: str = ""
    action_owner: str = ""
    action_due_date: str = ""
    action_status: str = "未开始"
    action_effect: str = ""
    revised_S: int | None = None
    revised_O: int | None = None
    revised_D: int | None = None
    revised_RPN: int | None = None
    notes: str = ""
    reference_ids: list[int] = []


class FailureUpdate(BaseModel):
    mode_desc: str | None = None
    local_effect: str | None = None
    potential_effect: str | None = None
    severity_S: int | None = Field(default=None, ge=1, le=10)
    classification: str | None = None
    potential_cause: str | None = None
    occurrence_O: int | None = Field(default=None, ge=1, le=10)
    prevention_control: str | None = None
    detection_control: str | None = None
    detection_D: int | None = Field(default=None, ge=1, le=10)
    recommended_action: str | None = None
    action_owner: str | None = None
    action_due_date: str | None = None
    action_status: str | None = None
    action_effect: str | None = None
    revised_S: int | None = None
    revised_O: int | None = None
    revised_D: int | None = None
    revised_RPN: int | None = None
    notes: str | None = None
    order_index: int | None = None
    function_item_id: int | None = None
    reference_ids: list[int] | None = None
    expected_version: int | None = None


@router.get("/projects/{project_id}/failures/all")
def list_all_failures(project_id: int, user=Depends(auth_svc.require_current_user)):
    """获取项目下所有失效模式（扁平列表，用于关联选择）"""
    access_svc.require_project_access(project_id, user)
    return fm_model.list_all_failures_flat(project_id)


@router.get("/nodes/{node_id}/failures")
def list_failures(node_id: int, user=Depends(auth_svc.require_current_user)):
    """获取节点下所有失效模式（含关联功能描述）"""
    access_svc.require_entity_access("node", node_id, user)
    return fm_model.list_failures(node_id)


@router.post("/nodes/{node_id}/failures", status_code=201)
def create_failure(node_id: int, body: FailureCreate, user=Depends(auth_svc.require_current_user)):
    """创建失效模式行"""
    project_id = access_svc.require_entity_access("node", node_id, user, write=True)
    access_svc.ensure_function_in_node(body.function_item_id, node_id)
    f = fm_model.create_failure(
        function_item_id=body.function_item_id,
        mode_desc=body.mode_desc,
        local_effect=body.local_effect,
        potential_effect=body.potential_effect,
        severity_S=body.severity_S,
        classification=body.classification,
        potential_cause=body.potential_cause,
        occurrence_O=body.occurrence_O,
        prevention_control=body.prevention_control,
        detection_control=body.detection_control,
        detection_D=body.detection_D,
        recommended_action=body.recommended_action,
        action_owner=body.action_owner,
        action_due_date=body.action_due_date,
        action_status=body.action_status,
        action_effect=body.action_effect,
        revised_S=body.revised_S,
        revised_O=body.revised_O,
        revised_D=body.revised_D,
        revised_RPN=body.revised_RPN,
        notes=body.notes,
        reference_ids=body.reference_ids,
    )
    log_action(project_id, user, "CREATE", "failure", f["id"], f["mode_desc"])
    return f


@router.put("/failures/{fm_id}")
def update_failure(fm_id: int, body: FailureUpdate, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("failure", fm_id, user, write=True)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        if updates.get("function_item_id") is not None:
            target_project_id = access_svc.project_id_for_entity("function", updates["function_item_id"])
            if target_project_id != project_id:
                raise HTTPException(status_code=400, detail="功能项不属于当前项目")
        f = fm_model.update_failure(fm_id, **updates)
    except VersionConflict:
        raise HTTPException(status_code=409, detail="失效模式已被其他用户修改，请刷新后再保存")
    if f is None:
        raise HTTPException(status_code=404, detail="失效模式不存在")
    log_action(project_id, user, "UPDATE", "failure", fm_id, f["mode_desc"])
    return f


@router.delete("/failures/{fm_id}")
def delete_failure(fm_id: int, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("failure", fm_id, user, write=True)
    fm_model.delete_failure(fm_id)
    log_action(project_id, user, "DELETE", "failure", fm_id, "删除失效模式")
    return {"ok": True}
