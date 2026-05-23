"""数据库初始化与连接管理。"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import sqlite3

import config


def get_db():
    """获取数据库连接。"""
    if config.DB_BACKEND == "postgres":
        return _get_postgres()
    conn = sqlite3.connect(config.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    """初始化数据库：建表 + 迁移 + 导入初始数据。"""
    conn = get_db()
    try:
        with open(config.SCHEMA_SQL, encoding="utf-8") as f:
            conn.executescript(f.read())

        _migrate(conn)

        with open(config.SEED_SQL, encoding="utf-8") as f:
            conn.executescript(f.read())

        conn.commit()
    finally:
        conn.close()


def _get_postgres():
    try:
        import psycopg2
    except ImportError as err:
        raise RuntimeError("使用 PostgreSQL 需要安装 psycopg2 或 psycopg2-binary") from err
    return PostgresConnection(psycopg2.connect(config.DATABASE_URL))


class DbRow:
    """同时支持 row['name'] 和 row[0] 的轻量行对象。
    PostgreSQL 会将列名转为小写，因此字符串键查找时做大小写不敏感匹配。
    """

    def __init__(self, columns, values):
        self._columns = list(columns)
        self._values = tuple(values)
        self._data = dict(zip(self._columns, self._values))
        self._lower_map = {k.lower(): k for k in self._data}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        lower = key.lower()
        if lower in self._lower_map:
            return self._data[self._lower_map[lower]]
        raise KeyError(key)

    def __iter__(self):
        return iter(self._columns)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def get(self, key, default=None):
        lower = key.lower()
        if lower in self._lower_map:
            return self._data[self._lower_map[lower]]
        return default


class CursorResult:
    def __init__(self, cursor, lastrowid=None):
        self._cursor = cursor
        self.lastrowid = lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in self._cursor.description]
        return DbRow(cols, row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        cols = [d[0] for d in self._cursor.description]
        return [DbRow(cols, row) for row in rows]


class PostgresConnection:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        sql, was_insert, table = _translate_sql(sql)
        if not sql.strip():
            return _EmptyResult()
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        lastrowid = None
        if was_insert and table:
            lastrowid = self._last_insert_id(table)
        return CursorResult(cur, lastrowid)

    def executescript(self, script: str):
        result = _EmptyResult()
        for statement in _split_sql_script(_strip_pragma_lines(script)):
            sql, _, _ = _translate_sql(statement)
            if sql.strip():
                cur = self._conn.cursor()
                cur.execute(sql)
                result = CursorResult(cur)
        return result

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def _last_insert_id(self, table: str):
        if table not in {
            "project", "structure_node", "function_item", "failure_mode", "reference",
            "audit_log", "user_account", "ap_matrix", "rating_criteria",
        }:
            return None
        cur = self._conn.cursor()
        cur.execute("SELECT currval(pg_get_serial_sequence(%s, 'id'))", (table,))
        return cur.fetchone()[0]


class _EmptyResult:
    rowcount = 0
    lastrowid = None

    def fetchone(self):
        return None

    def fetchall(self):
        return []


def _translate_script(script: str) -> str:
    sql, _, _ = _translate_sql(script)
    lines = []
    for line in sql.splitlines():
        if line.strip().upper().startswith("PRAGMA "):
            continue
        lines.append(line)
    return "\n".join(lines)


def _strip_pragma_lines(script: str) -> str:
    return "\n".join(
        line for line in script.splitlines()
        if not line.strip().upper().startswith("PRAGMA ")
    )


def _split_sql_script(script: str) -> list[str]:
    statements = []
    current = []
    in_quote = False
    prev = ""
    for ch in script:
        if ch == "'" and prev != "\\":
            in_quote = not in_quote
        if ch == ";" and not in_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(ch)
        prev = ch
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def _translate_sql(sql: str):
    original = sql
    text = sql.strip()
    if text.upper().startswith("PRAGMA "):
        return "", False, None

    sql = re.sub(
        r"\bid\s+INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
        "id SERIAL PRIMARY KEY",
        sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
    sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
    sql = sql.replace("insert or ignore into", "insert into")
    sql = re.sub(
        r"datetime\('now'\s*,\s*'localtime'\)",
        "to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')",
        sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(
        r"DEFAULT\s*\(\s*to_char\(CURRENT_TIMESTAMP,\s*'YYYY-MM-DD HH24:MI:SS'\)\s*\)",
        "DEFAULT to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')",
        sql,
        flags=re.IGNORECASE,
    )
    sql = sql.replace("?", "%s")

    was_ignore = "INSERT OR IGNORE INTO" in original.upper()
    was_insert = bool(re.match(r"\s*INSERT\s+INTO\s+", sql, flags=re.IGNORECASE))
    table = None
    m = re.match(r"\s*INSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)", sql, flags=re.IGNORECASE)
    if m:
        table = m.group(1)
    if was_ignore and "ON CONFLICT" not in sql.upper():
        sql = _append_on_conflict_do_nothing(sql)
    return sql, was_insert, table


def _append_on_conflict_do_nothing(sql: str) -> str:
    stripped = sql.rstrip()
    suffix = ";" if stripped.endswith(";") else ""
    if suffix:
        stripped = stripped[:-1].rstrip()
    return stripped + " ON CONFLICT DO NOTHING" + suffix


def _table_columns(conn, table: str) -> set[str]:
    if config.DB_BACKEND == "postgres":
        rows = conn.execute(
            """SELECT column_name
               FROM information_schema.columns
               WHERE table_schema = 'public' AND table_name = %s""",
            (table,),
        ).fetchall()
        return {r["column_name"] for r in rows}
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _migrate(conn):
    """数据库迁移。"""
    _migrate_auth(conn)

    cols = _table_columns(conn, "failure_mode")
    if "local_effect" not in cols:
        conn.execute("ALTER TABLE failure_mode ADD COLUMN local_effect TEXT DEFAULT ''")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reference_node (
            reference_id INTEGER NOT NULL REFERENCES reference(id) ON DELETE CASCADE,
            node_id      INTEGER NOT NULL REFERENCES structure_node(id) ON DELETE CASCADE,
            PRIMARY KEY (reference_id, node_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rn_ref  ON reference_node(reference_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rn_node ON reference_node(node_id)")

    if "node_id" in _table_columns(conn, "reference"):
        existing = conn.execute("SELECT id, node_id FROM reference WHERE node_id IS NOT NULL").fetchall()
        for r in existing:
            conn.execute(
                "INSERT OR IGNORE INTO reference_node (reference_id, node_id) VALUES (?, ?)",
                (r["id"], r["node_id"]),
            )

    if config.DB_BACKEND != "postgres":
        sql = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reference'").fetchone()
        if sql and "'系统图'" in sql["sql"]:
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

    _migrate_versions(conn)


def _migrate_auth(conn):
    """认证、权限和会话表。"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_account (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name  TEXT DEFAULT '',
            is_admin      INTEGER DEFAULT 0,
            is_active     INTEGER DEFAULT 1,
            created_at    TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at    TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_member (
            project_id INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
            user_id    INTEGER NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
            role       TEXT NOT NULL DEFAULT 'editor' CHECK(role IN ('owner', 'editor', 'viewer')),
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            PRIMARY KEY (project_id, user_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pm_user ON project_member(user_id)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_session (
            token_hash TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session_user ON auth_session(user_id)")

    audit_cols = _table_columns(conn, "audit_log")
    if audit_cols:
        if "user_id" not in audit_cols:
            conn.execute("ALTER TABLE audit_log ADD COLUMN user_id INTEGER")
        if "username" not in audit_cols:
            conn.execute("ALTER TABLE audit_log ADD COLUMN username TEXT DEFAULT ''")

    user_count = conn.execute("SELECT COUNT(*) FROM user_account").fetchone()[0]
    if user_count == 0:
        conn.execute(
            """INSERT INTO user_account (username, password_hash, display_name, is_admin)
               VALUES (?, ?, ?, 1)""",
            (
                config.INITIAL_ADMIN_USERNAME,
                _hash_password(config.INITIAL_ADMIN_PASSWORD),
                "管理员",
            ),
        )


def _migrate_versions(conn):
    """为多人编辑补充基础乐观锁字段。"""
    table_defaults = {
        "project": ["version INTEGER DEFAULT 1"],
        "structure_node": ["version INTEGER DEFAULT 1"],
        "function_item": [
            "version INTEGER DEFAULT 1",
            "created_at TEXT",
            "updated_at TEXT",
        ],
        "failure_mode": [
            "version INTEGER DEFAULT 1",
            "created_at TEXT",
            "updated_at TEXT",
        ],
        "reference": [
            "version INTEGER DEFAULT 1",
            "updated_at TEXT",
        ],
    }
    for table, definitions in table_defaults.items():
        cols = _table_columns(conn, table)
        for definition in definitions:
            name = definition.split()[0]
            if name not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")
        refreshed_cols = _table_columns(conn, table)
        now_sql = "to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')" if config.DB_BACKEND == "postgres" else "datetime('now', 'localtime')"
        if "created_at" in refreshed_cols:
            conn.execute(f"UPDATE {table} SET created_at = COALESCE(created_at, {now_sql})")
        if "updated_at" in refreshed_cols:
            conn.execute(f"UPDATE {table} SET updated_at = COALESCE(updated_at, {now_sql})")


def _hash_password(password: str) -> str:
    """初始化管理员使用的 PBKDF2 哈希，运行时验证逻辑在 services.auth 中。"""
    iterations = 260000
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )
