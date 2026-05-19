"""导入导出 API"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
from urllib.parse import quote

from services import export as export_svc
from services import importer as import_svc
from db.database import get_db
from services import access as access_svc
from services import auth as auth_svc
from services.audit import log_action
import config

router = APIRouter(prefix="/api/v1")


@router.get("/criteria")
def get_criteria(user=Depends(auth_svc.require_current_user)):
    """获取 S/O/D 评分准则"""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT type, score, title, description FROM rating_criteria ORDER BY type, score"
        ).fetchall()
        result = {"S": [], "O": [], "D": []}
        for r in rows:
            result[r["type"]].append({"score": r["score"], "title": r["title"], "description": r["description"]})
        return result
    finally:
        conn.close()


@router.get("/projects/{project_id}/export/xlsx")
def export_xlsx(project_id: int, user=Depends(auth_svc.require_current_user)):
    """导出项目 DFMEA 数据为 Excel 文件"""
    access_svc.require_project_access(project_id, user)
    try:
        data = export_svc.export_xlsx(project_id)
        conn = get_db()
        try:
            proj = conn.execute("SELECT name FROM project WHERE id = ?", (project_id,)).fetchone()
        finally:
            conn.close()
        safe_name = proj['name'] if proj else f"project_{project_id}"
        fname = f"DFMEA_{safe_name}.xlsx"
        encoded = quote(fname, safe='')
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/template")
def export_template(user=Depends(auth_svc.require_current_user)):
    """下载空 DFMEA 模板"""
    data = export_svc.export_template()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=DFMEA_template.xlsx"},
    )


@router.get("/projects/{project_id}/export/json")
def export_json(project_id: int, user=Depends(auth_svc.require_current_user)):
    """导出项目完整数据为 JSON"""
    access_svc.require_project_access(project_id, user)
    try:
        data = export_svc.export_json(project_id)
        return StreamingResponse(
            io.BytesIO(data.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=DFMEA_project_{project_id}.json"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/import/json")
async def import_json(
    file: UploadFile = File(...),
    project_name: str = Form(None),
    user=Depends(auth_svc.require_admin),
):
    """从 JSON 文件恢复项目"""
    try:
        content = await file.read()
        if len(content) > config.MAX_IMPORT_MB * 1024 * 1024:
            raise ValueError(f"文件不能超过 {config.MAX_IMPORT_MB} MB")
        new_id = import_svc.import_json(content.decode("utf-8"), project_name)
        access_svc.set_project_member(new_id, user["id"], "owner")
        log_action(new_id, user, "CREATE", "project", new_id, "JSON 恢复项目")
        return {"ok": True, "project_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/import/xlsx")
async def import_xlsx(project_id: int, file: UploadFile = File(...), user=Depends(auth_svc.require_current_user)):
    """从 Excel 文件导入失效模式行"""
    access_svc.require_project_access(project_id, user, write=True)
    try:
        content = await file.read()
        if len(content) > config.MAX_IMPORT_MB * 1024 * 1024:
            raise ValueError(f"文件不能超过 {config.MAX_IMPORT_MB} MB")
        count = import_svc.import_xlsx(content, project_id)
        log_action(project_id, user, "CREATE", "failure", None, f"Excel 导入 {count} 条")
        return {"ok": True, "imported": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
