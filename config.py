import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent

# 数据目录 — 独立于代码，便于备份
DB_DIR = pathlib.Path(os.environ.get("DFMEA_DB_DIR", r"C:\Users\invok\dfmea_db"))
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = str(DB_DIR / "dfmea.db")
UPLOAD_DIR = str(DB_DIR / "uploads")
pathlib.Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# 数据库 init 脚本路径
SCHEMA_SQL = str(BASE_DIR / "db" / "schema.sql")
SEED_SQL = str(BASE_DIR / "db" / "seed.sql")

# 应用
APP_TITLE = "DFMEA 个人记录系统"
APP_VERSION = "0.1.0"
