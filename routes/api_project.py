"""项目 API"""

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from pydantic import BaseModel, Field
from models import project as project_model
from services import access as access_svc
from services import auth as auth_svc
from services.audit import log_action

router = APIRouter(prefix="/api/v1")


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    description: str = Field(default="", max_length=2000, description="项目描述")
    template_id: int | None = Field(default=None, description="从已有项目复制结构")


class ProjectUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    expected_version: int | None = None


@router.get("/projects")
def list_projects(user=Depends(auth_svc.require_current_user)):
    """获取所有项目列表（含统计信息）"""
    return project_model.list_projects(user)


@router.get("/projects/trash/list")
def list_trash(user=Depends(auth_svc.require_admin)):
    """列出回收站中的项目"""
    return project_model.list_trash()


@router.get("/projects/{project_id}")
def get_project(project_id: int, user=Depends(auth_svc.require_current_user)):
    """获取单个项目详情"""
    access_svc.require_project_access(project_id, user)
    p = project_model.get_project(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return p


@router.post("/projects", status_code=201)
def create_project(body: ProjectCreate, user=Depends(auth_svc.require_admin)):
    """创建新项目"""
    if body.template_id:
        access_svc.require_project_access(body.template_id, user)
    p = project_model.create_project(
        name=body.name,
        description=body.description,
        template_id=body.template_id,
        actor_id=user["id"],
    )
    log_action(p["id"], user, "CREATE", "project", p["id"], p["name"])
    return p


@router.put("/projects/{project_id}")
def update_project(project_id: int, body: ProjectUpdate, user=Depends(auth_svc.require_current_user)):
    """更新项目信息"""
    access_svc.require_project_access(project_id, user, write=True)
    try:
        p = project_model.update_project(project_id, body.name, body.description, body.expected_version)
    except project_model.VersionConflict:
        raise HTTPException(status_code=409, detail="项目已被其他用户修改，请刷新后再保存")
    if p is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    log_action(project_id, user, "UPDATE", "project", project_id, p["name"])
    return p


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, user=Depends(auth_svc.require_current_user)):
    """删除项目（软删除，移入回收站）"""
    access_svc.require_project_access(project_id, user, write=True)
    ok = project_model.delete_project(project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="项目不存在")
    log_action(project_id, user, "DELETE", "project", project_id, "移入回收站")
    return {"ok": True}


@router.post("/projects/{project_id}/restore")
def restore_project(project_id: int, user=Depends(auth_svc.require_admin)):
    """从回收站恢复项目"""
    ok = project_model.restore_project(project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="项目不存在或不在回收站")
    return {"ok": True}


@router.delete("/projects/{project_id}/permanent")
def permanent_delete_project(project_id: int, user=Depends(auth_svc.require_admin)):
    """永久删除项目"""
    ok = project_model.permanent_delete_project(project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="项目不存在或不在回收站")
    return {"ok": True}
