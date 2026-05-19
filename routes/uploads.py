"""鉴权后的上传文件访问。"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

import config
from db.database import get_db
from services import access as access_svc
from services import auth as auth_svc

router = APIRouter()


@router.get("/uploads/{file_path:path}")
def get_upload(file_path: str, user=Depends(auth_svc.require_current_user)):
    rel = file_path.replace("\\", "/").lstrip("/")
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT project_id, title FROM reference WHERE file_path = ?",
            (rel,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="文件不存在")
    access_svc.require_project_access(row["project_id"], user)

    upload_root = Path(config.UPLOAD_DIR).resolve()
    full_path = (upload_root / rel).resolve()
    if upload_root not in full_path.parents and full_path != upload_root:
        raise HTTPException(status_code=400, detail="无效文件路径")
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(full_path), filename=full_path.name)
