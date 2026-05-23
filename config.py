import os
import pathlib
import subprocess
from urllib.parse import quote_plus

BASE_DIR = pathlib.Path(__file__).resolve().parent


def _get_version():
    try:
        tags = subprocess.check_output(
            ["git", "tag", "-l", "--sort=-version:refname"],
            cwd=str(BASE_DIR), stderr=subprocess.DEVNULL,
        ).decode().strip().split()
        return tags[0].lstrip("v") if tags else "1.1.0"
    except Exception:
        return "1.1.0"

# 数据目录 — 独立于代码，便于备份
DB_DIR = pathlib.Path(os.environ.get("DFMEA_DB_DIR", str(pathlib.Path.home() / "dfmea_db")))
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = str(DB_DIR / "dfmea.db")
UPLOAD_DIR = str(DB_DIR / "uploads")
pathlib.Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# 数据库后端：sqlite / postgres
DB_BACKEND = os.environ.get("DFMEA_DB_BACKEND", "sqlite").lower()
POSTGRES_DB = os.environ.get("DFMEA_POSTGRES_DB", "dfmea")
POSTGRES_USER = os.environ.get("DFMEA_POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("DFMEA_POSTGRES_PASSWORD", os.environ.get("PGPASSWORD", ""))
POSTGRES_HOST = os.environ.get("DFMEA_POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("DFMEA_POSTGRES_PORT", "5432")
DATABASE_URL = os.environ.get(
    "DFMEA_DATABASE_URL",
    "postgresql://{}:{}@{}:{}/{}".format(
        quote_plus(POSTGRES_USER),
        quote_plus(POSTGRES_PASSWORD),
        POSTGRES_HOST,
        POSTGRES_PORT,
        POSTGRES_DB,
    ),
)

# 数据库 init 脚本路径
SCHEMA_SQL = str(BASE_DIR / "db" / "schema.sql")
SEED_SQL = str(BASE_DIR / "db" / "seed.sql")

# 应用
APP_TITLE = "DFMEA 记录系统"
APP_VERSION = _get_version()

# 初始管理员账号：仅在数据库中还没有任何账号时自动创建
INITIAL_ADMIN_USERNAME = os.environ.get("DFMEA_ADMIN_USERNAME", "admin")
INITIAL_ADMIN_PASSWORD = os.environ.get("DFMEA_ADMIN_PASSWORD", "admin123456")

# 会话与上传限制
SESSION_DAYS = int(os.environ.get("DFMEA_SESSION_DAYS", "7"))
MAX_UPLOAD_MB = int(os.environ.get("DFMEA_MAX_UPLOAD_MB", "50"))
MAX_IMPORT_MB = int(os.environ.get("DFMEA_MAX_IMPORT_MB", "20"))
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".csv", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".bmp", ".svg", ".zip", ".7z",
}
