"""页面路由 — 返回 HTML"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import config
from services.auth import get_current_user_from_request

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login")
async def login_page(request: Request):
    """登录页"""
    user = get_current_user_from_request(request)
    if user:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {
        "title": config.APP_TITLE,
        "app_version": config.APP_VERSION,
    })


@router.get("/")
async def index(request: Request):
    """首页仪表盘"""
    user = get_current_user_from_request(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "index.html", {
        "title": config.APP_TITLE,
        "current_user": user,
        "app_version": config.APP_VERSION,
    })


@router.get("/project/{project_id}")
async def project_detail(request: Request, project_id: int):
    """项目详情页"""
    user = get_current_user_from_request(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "project.html", {
        "title": config.APP_TITLE,
        "project_id": project_id,
        "current_user": user,
        "app_version": config.APP_VERSION,
    })


@router.get("/admin")
async def admin_page(request: Request):
    """账号管理页"""
    user = get_current_user_from_request(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not user["is_admin"]:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "admin.html", {
        "title": config.APP_TITLE,
        "current_user": user,
        "app_version": config.APP_VERSION,
    })
