"""数据库初始化与连接管理"""

import sqlite3
import config


def get_db() -> sqlite3.Connection:
    """获取数据库连接（WAL 模式，row factory = Row）"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """初始化数据库：建表 + 迁移 + 导入初始数据"""
    conn = get_db()
    try:
        # 建表
        with open(config.SCHEMA_SQL, encoding="utf-8") as f:
            conn.executescript(f.read())

        # 迁移：添加 local_effect 列（v0.2+）
        _migrate(conn)

        # 初始数据（仅在表为空时插入，防止重复）
        cnt = conn.execute("SELECT COUNT(*) FROM rating_criteria").fetchone()[0]
        if cnt == 0:
            with open(config.SEED_SQL, encoding="utf-8") as f:
                conn.executescript(f.read())

        conn.commit()
    finally:
        conn.close()


def _migrate(conn):
    """数据库迁移"""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(failure_mode)").fetchall()}
    if "local_effect" not in cols:
        conn.execute("ALTER TABLE failure_mode ADD COLUMN local_effect TEXT DEFAULT ''")
