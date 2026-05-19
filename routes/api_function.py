"""功能项 API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from models import function as func_model
from models.project import VersionConflict
from services import access as access_svc
from services import auth as auth_svc
from services.audit import log_action

router = APIRouter(prefix="/api/v1")


class FunctionCreate(BaseModel):
    function_desc: str = Field(..., min_length=1, max_length=2000)
    requirement: str = ""
    performance_spec: str = ""
    interface_desc: str = ""


class FunctionUpdate(BaseModel):
    function_desc: str | None = None
    requirement: str | None = None
    performance_spec: str | None = None
    interface_desc: str | None = None
    order_index: int | None = None
    expected_version: int | None = None


class BatchCreate(BaseModel):
    text: str = Field(..., min_length=1, description="每行一个功能描述")


@router.get("/nodes/{node_id}/functions")
def list_functions(node_id: int, user=Depends(auth_svc.require_current_user)):
    access_svc.require_entity_access("node", node_id, user)
    return func_model.list_functions(node_id)


@router.post("/nodes/{node_id}/functions", status_code=201)
def create_function(node_id: int, body: FunctionCreate, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("node", node_id, user, write=True)
    f = func_model.create_function(
        node_id=node_id,
        function_desc=body.function_desc,
        requirement=body.requirement,
        performance_spec=body.performance_spec,
        interface_desc=body.interface_desc,
    )
    log_action(project_id, user, "CREATE", "function", f["id"], f["function_desc"])
    return f


@router.post("/nodes/{node_id}/functions/batch", status_code=201)
def batch_create_functions(node_id: int, body: BatchCreate, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("node", node_id, user, write=True)
    lines = body.text.strip().split("\n")
    created = func_model.batch_create(node_id, lines)
    log_action(project_id, user, "CREATE", "function", None, f"批量创建 {len(created)} 条功能")
    return {"count": len(created), "items": created}


@router.put("/functions/{func_id}")
def update_function(func_id: int, body: FunctionUpdate, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("function", func_id, user, write=True)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        f = func_model.update_function(func_id, **updates)
    except VersionConflict:
        raise HTTPException(status_code=409, detail="功能项已被其他用户修改，请刷新后再保存")
    if f is None:
        raise HTTPException(status_code=404, detail="功能项不存在")
    log_action(project_id, user, "UPDATE", "function", func_id, f["function_desc"])
    return f


@router.delete("/functions/{func_id}")
def delete_function(func_id: int, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("function", func_id, user, write=True)
    func_model.delete_function(func_id)
    log_action(project_id, user, "DELETE", "function", func_id, "删除功能项")
    return {"ok": True}
