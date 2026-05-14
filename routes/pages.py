"""页面路由 — 返回 HTML"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import config

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def index(request: Request):
    """首页仪表盘"""
    return templates.TemplateResponse(request, "index.html", {
        "title": config.APP_TITLE,
    })


@router.get("/project/{project_id}")
async def project_detail(request: Request, project_id: int):
    """项目详情页"""
    return templates.TemplateResponse(request, "project.html", {
        "title": config.APP_TITLE,
        "project_id": project_id,
    })
