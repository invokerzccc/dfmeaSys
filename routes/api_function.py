"""功能项 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from models import function as func_model

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


class BatchCreate(BaseModel):
    text: str = Field(..., min_length=1, description="每行一个功能描述")


@router.get("/nodes/{node_id}/functions")
def list_functions(node_id: int):
    return func_model.list_functions(node_id)


@router.post("/nodes/{node_id}/functions", status_code=201)
def create_function(node_id: int, body: FunctionCreate):
    return func_model.create_function(
        node_id=node_id,
        function_desc=body.function_desc,
        requirement=body.requirement,
        performance_spec=body.performance_spec,
        interface_desc=body.interface_desc,
    )


@router.post("/nodes/{node_id}/functions/batch", status_code=201)
def batch_create_functions(node_id: int, body: BatchCreate):
    lines = body.text.strip().split("\n")
    created = func_model.batch_create(node_id, lines)
    return {"count": len(created), "items": created}


@router.put("/functions/{func_id}")
def update_function(func_id: int, body: FunctionUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    f = func_model.update_function(func_id, **updates)
    if f is None:
        raise HTTPException(status_code=404, detail="功能项不存在")
    return f


@router.delete("/functions/{func_id}")
def delete_function(func_id: int):
    func_model.delete_function(func_id)
    return {"ok": True}
