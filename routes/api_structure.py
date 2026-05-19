"""结构树 API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from models import structure as struct_model
from models.project import VersionConflict
from services import access as access_svc
from services import auth as auth_svc
from services.audit import log_action

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
    expected_version: int | None = None


@router.get("/projects/{project_id}/structure")
def get_structure(project_id: int, user=Depends(auth_svc.require_current_user)):
    """获取项目完整结构树"""
    access_svc.require_project_access(project_id, user)
    return struct_model.get_tree(project_id)


@router.post("/projects/{project_id}/structure", status_code=201)
def create_node(project_id: int, body: NodeCreate, user=Depends(auth_svc.require_current_user)):
    """添加结构节点"""
    access_svc.require_project_access(project_id, user, write=True)
    if body.parent_id is not None and access_svc.project_id_for_entity("node", body.parent_id) != project_id:
        raise HTTPException(status_code=400, detail="父节点不属于当前项目")
    n = struct_model.create_node(
        project_id=project_id,
        parent_id=body.parent_id,
        name=body.name,
        type=body.type,
    )
    log_action(project_id, user, "CREATE", "node", n["id"], n["name"])
    return n


@router.get("/structure/{node_id}")
def get_node(node_id: int, user=Depends(auth_svc.require_current_user)):
    access_svc.require_entity_access("node", node_id, user)
    n = struct_model.get_node(node_id)
    if n is None:
        raise HTTPException(status_code=404, detail="节点不存在")
    return n


@router.put("/structure/{node_id}")
def update_node(node_id: int, body: NodeUpdate, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("node", node_id, user, write=True)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        n = struct_model.update_node(node_id, **updates)
    except VersionConflict:
        raise HTTPException(status_code=409, detail="节点已被其他用户修改，请刷新后再保存")
    if n is None:
        raise HTTPException(status_code=404, detail="节点不存在")
    log_action(project_id, user, "UPDATE", "node", node_id, n["name"])
    return n


class NodeMove(BaseModel):
    new_parent_id: int | None = None
    new_index: int = 0


@router.put("/structure/{node_id}/move")
def move_node(node_id: int, body: NodeMove, user=Depends(auth_svc.require_current_user)):
    """移动节点到新位置（拖拽排序）"""
    project_id = access_svc.require_entity_access("node", node_id, user, write=True)
    n = struct_model.move_node(node_id, body.new_parent_id, body.new_index)
    if n is None:
        raise HTTPException(status_code=404, detail="节点不存在")
    log_action(project_id, user, "UPDATE", "node", node_id, "移动节点")
    return n


@router.delete("/structure/{node_id}")
def delete_node(node_id: int, user=Depends(auth_svc.require_current_user)):
    project_id = access_svc.require_entity_access("node", node_id, user, write=True)
    struct_model.delete_node(node_id)
    log_action(project_id, user, "DELETE", "node", node_id, "删除节点")
    return {"ok": True}
