"""认证、用户和项目成员 API。"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from services import access as access_svc
from services import auth as auth_svc
from services.audit import log_action

router = APIRouter(prefix="/api/v1")


class LoginBody(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=80)
    password: str = Field(..., min_length=8, max_length=200)
    display_name: str = Field(default="", max_length=120)
    is_admin: bool = False


class UserUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=120)
    is_admin: bool | None = None
    is_active: bool | None = None


class MemberUpdate(BaseModel):
    user_id: int
    role: str = Field(default="editor")


@router.post("/auth/login")
def login(body: LoginBody, response: Response):
    user = auth_svc.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    auth_svc.create_session(response, user["id"])
    return {"ok": True, "user": user}


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    auth_svc.clear_session(request, response)
    return {"ok": True}


@router.get("/auth/me")
def me(user=Depends(auth_svc.require_current_user)):
    return user


@router.get("/admin/users")
def list_users(user=Depends(auth_svc.require_admin)):
    return auth_svc.list_users()


@router.post("/admin/users", status_code=201)
def create_user(body: UserCreate, user=Depends(auth_svc.require_admin)):
    try:
        created = auth_svc.create_user(
            username=body.username,
            password=body.password,
            display_name=body.display_name,
            is_admin=body.is_admin,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="用户名已存在")
    log_action(0, user, "CREATE", "user", created["id"], f"创建账号 {created['username']}")
    return created


@router.put("/admin/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, user=Depends(auth_svc.require_admin)):
    updated = auth_svc.update_user(user_id, **body.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="用户不存在")
    log_action(0, user, "UPDATE", "user", user_id, f"更新账号 {updated['username']}")
    return updated


@router.get("/projects/{project_id}/members")
def list_project_members(project_id: int, user=Depends(auth_svc.require_current_user)):
    access_svc.require_project_member_management(project_id, user)
    return access_svc.get_project_members(project_id)


@router.get("/projects/{project_id}/member-candidates")
def list_project_member_candidates(project_id: int, user=Depends(auth_svc.require_current_user)):
    access_svc.require_project_member_management(project_id, user)
    return auth_svc.list_users()


@router.get("/projects/{project_id}/permissions")
def get_project_permissions(project_id: int, user=Depends(auth_svc.require_current_user)):
    access_svc.require_project_access(project_id, user)
    role = access_svc.get_project_role(project_id, user)
    return {
        "role": role,
        "can_edit": access_svc.can_access_project(project_id, user, write=True),
        "can_manage_members": access_svc.can_manage_project_members(project_id, user),
    }


@router.put("/projects/{project_id}/members")
def set_project_member(project_id: int, body: MemberUpdate, user=Depends(auth_svc.require_current_user)):
    access_svc.require_project_member_management(project_id, user)
    access_svc.set_project_member(project_id, body.user_id, body.role)
    log_action(project_id, user, "UPDATE", "member", body.user_id, f"设置项目角色 {body.role}")
    return {"ok": True}


@router.delete("/projects/{project_id}/members/{user_id}")
def remove_project_member(project_id: int, user_id: int, user=Depends(auth_svc.require_current_user)):
    access_svc.require_project_member_management(project_id, user)
    access_svc.remove_project_member(project_id, user_id)
    log_action(project_id, user, "DELETE", "member", user_id, "移除项目成员")
    return {"ok": True}
