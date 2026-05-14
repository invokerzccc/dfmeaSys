"""导入导出 API"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

from services import export as export_svc
from services import importer as import_svc
from db.database import get_db

router = APIRouter(prefix="/api/v1")


@router.get("/criteria")
def get_criteria():
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
def export_xlsx(project_id: int):
    """导出项目 DFMEA 数据为 Excel 文件"""
    try:
        data = export_svc.export_xlsx(project_id)
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=DFMEA_project_{project_id}.xlsx"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/template")
def export_template():
    """下载空 DFMEA 模板"""
    data = export_svc.export_template()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=DFMEA_template.xlsx"},
    )


@router.get("/projects/{project_id}/export/json")
def export_json(project_id: int):
    """导出项目完整数据为 JSON"""
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
async def import_json(file: UploadFile = File(...), project_name: str = Form(None)):
    """从 JSON 文件恢复项目"""
    try:
        content = await file.read()
        new_id = import_svc.import_json(content.decode("utf-8"), project_name)
        return {"ok": True, "project_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/import/xlsx")
async def import_xlsx(project_id: int, file: UploadFile = File(...)):
    """从 Excel 文件导入失效模式行"""
    try:
        content = await file.read()
        count = import_svc.import_xlsx(content, project_id)
        return {"ok": True, "imported": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
