"""DFMEA 个人记录系统 — FastAPI 入口"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db.database import init_db
from routes.pages import router as pages_router
from routes.api_project import router as api_project_router
from routes.api_structure import router as api_structure_router
from routes.api_function import router as api_function_router
from routes.api_failure import router as api_failure_router
from routes.api_reference import router as api_reference_router
from routes.api_export import router as api_export_router
import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动：初始化数据库"""
    init_db()
    yield


app = FastAPI(
    title=config.APP_TITLE,
    version=config.APP_VERSION,
    lifespan=lifespan,
)

# 静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 上传文件目录（外部数据盘）
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")

# 路由注册
app.include_router(pages_router)
app.include_router(api_project_router)
app.include_router(api_structure_router)
app.include_router(api_function_router)
app.include_router(api_failure_router)
app.include_router(api_reference_router)
app.include_router(api_export_router)
