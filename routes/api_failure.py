"""失效模式（DFMEA 工作表）API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from models import failure_mode as fm_model

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


@router.get("/nodes/{node_id}/failures")
def list_failures(node_id: int):
    """获取节点下所有失效模式（含关联功能描述）"""
    return fm_model.list_failures(node_id)


@router.post("/nodes/{node_id}/failures", status_code=201)
def create_failure(node_id: int, body: FailureCreate):
    """创建失效模式行"""
    return fm_model.create_failure(
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


@router.put("/failures/{fm_id}")
def update_failure(fm_id: int, body: FailureUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    f = fm_model.update_failure(fm_id, **updates)
    if f is None:
        raise HTTPException(status_code=404, detail="失效模式不存在")
    return f


@router.delete("/failures/{fm_id}")
def delete_failure(fm_id: int):
    fm_model.delete_failure(fm_id)
    return {"ok": True}
