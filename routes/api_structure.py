"""结构树 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from models import structure as struct_model

router = APIRouter(prefix="/api/v1")


class NodeCreate(BaseModel):
    parent_id: int | None = None
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default="部件")


class NodeUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    part_number: str | None = None
    description: str | None = None
    parent_id: int | None = None
    order_index: int | None = None


@router.get("/projects/{project_id}/structure")
def get_structure(project_id: int):
    """获取项目完整结构树"""
    return struct_model.get_tree(project_id)


@router.post("/projects/{project_id}/structure", status_code=201)
def create_node(project_id: int, body: NodeCreate):
    """添加结构节点"""
    return struct_model.create_node(
        project_id=project_id,
        parent_id=body.parent_id,
        name=body.name,
        type=body.type,
    )


@router.get("/structure/{node_id}")
def get_node(node_id: int):
    n = struct_model.get_node(node_id)
    if n is None:
        raise HTTPException(status_code=404, detail="节点不存在")
    return n


@router.put("/structure/{node_id}")
def update_node(node_id: int, body: NodeUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    n = struct_model.update_node(node_id, **updates)
    if n is None:
        raise HTTPException(status_code=404, detail="节点不存在")
    return n


class NodeMove(BaseModel):
    new_parent_id: int | None = None
    new_index: int = 0


@router.put("/structure/{node_id}/move")
def move_node(node_id: int, body: NodeMove):
    """移动节点到新位置（拖拽排序）"""
    n = struct_model.move_node(node_id, body.new_parent_id, body.new_index)
    if n is None:
        raise HTTPException(status_code=404, detail="节点不存在")
    return n


@router.delete("/structure/{node_id}")
def delete_node(node_id: int):
    struct_model.delete_node(node_id)
    return {"ok": True}
