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

    # 创建 reference_node 多对多关联表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reference_node (
            reference_id INTEGER NOT NULL REFERENCES reference(id) ON DELETE CASCADE,
            node_id      INTEGER NOT NULL REFERENCES structure_node(id) ON DELETE CASCADE,
            PRIMARY KEY (reference_id, node_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rn_ref  ON reference_node(reference_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rn_node ON reference_node(node_id)")

    # 将已有 reference.node_id 迁移到 reference_node
    existing = conn.execute("SELECT id, node_id FROM reference WHERE node_id IS NOT NULL").fetchall()
    for r in existing:
        conn.execute(
            "INSERT OR IGNORE INTO reference_node (reference_id, node_id) VALUES (?, ?)",
            (r["id"], r["node_id"]),
        )

    # 更新 reference.type CHECK 约束：支持新的类型分类
    sql = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reference'").fetchone()
    if sql and "'系统图'" in sql["sql"]:
        # 先更新旧数据到新类型，避免 INSERT 时违反新 CHECK
        conn.execute("UPDATE reference SET type = '文档' WHERE type IN ('规格书', '系统图', '分析报告')")
        conn.execute("UPDATE reference SET type = '其他' WHERE type NOT IN ('链接', '文档', '图片', '其他')")
        conn.execute("""
            CREATE TABLE reference_new (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
                node_id     INTEGER REFERENCES structure_node(id) ON DELETE SET NULL,
                title       TEXT    NOT NULL,
                type        TEXT    NOT NULL DEFAULT '其他' CHECK(type IN ('链接', '文档', '图片', '其他')),
                file_path   TEXT    DEFAULT '',
                url         TEXT    DEFAULT '',
                notes       TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.execute("INSERT INTO reference_new SELECT * FROM reference")
        conn.execute("DROP TABLE reference")
        conn.execute("ALTER TABLE reference_new RENAME TO reference")
