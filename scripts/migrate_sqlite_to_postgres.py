"""一次性将当前 SQLite 数据迁移到 PostgreSQL。"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote_plus

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TABLES = [
    "ap_matrix",
    "rating_criteria",
    "user_account",
    "project",
    "project_member",
    "structure_node",
    "function_item",
    "failure_mode",
    "reference",
    "reference_node",
    "failure_mode_reference",
    "audit_log",
]

ID_TABLES = {
    "ap_matrix",
    "rating_criteria",
    "user_account",
    "project",
    "structure_node",
    "function_item",
    "failure_mode",
    "reference",
    "audit_log",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", default=None, help="SQLite 数据库路径")
    parser.add_argument("--host", default=os.environ.get("DFMEA_POSTGRES_HOST", "localhost"))
    parser.add_argument("--port", default=os.environ.get("DFMEA_POSTGRES_PORT", "5432"))
    parser.add_argument("--user", default=os.environ.get("DFMEA_POSTGRES_USER", "postgres"))
    parser.add_argument("--password", default=os.environ.get("DFMEA_POSTGRES_PASSWORD", os.environ.get("PGPASSWORD", "")))
    parser.add_argument("--database", default=os.environ.get("DFMEA_POSTGRES_DB", "dfmea"))
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite or Path.home() / "dfmea_db" / "dfmea.db")
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite 数据库不存在: {sqlite_path}")
    if not args.password:
        raise SystemExit("缺少 PostgreSQL 密码，请传 --password 或设置 DFMEA_POSTGRES_PASSWORD/PGPASSWORD")

    create_database_if_needed(args)
    db_url = "postgresql://{}:{}@{}:{}/{}".format(
        quote_plus(args.user),
        quote_plus(args.password),
        args.host,
        args.port,
        args.database,
    )

    os.environ["DFMEA_DB_BACKEND"] = "postgres"
    os.environ["DFMEA_DATABASE_URL"] = db_url

    from db.database import init_db

    init_db()
    migrate(sqlite_path, db_url)
    print(f"迁移完成: {sqlite_path} -> PostgreSQL/{args.database}")


def create_database_if_needed(args) -> None:
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        dbname="postgres",
    )
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (args.database,))
        if not cur.fetchone():
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(args.database)))
            print(f"已创建数据库: {args.database}")
    finally:
        conn.close()


def migrate(sqlite_path: Path, db_url: str) -> None:
    src = sqlite3.connect(sqlite_path)
    src.row_factory = sqlite3.Row
    dst = psycopg2.connect(db_url)
    try:
        src_tables = table_names(src)
        dst_tables = pg_table_names(dst)
        tables = [t for t in TABLES if t in src_tables and t in dst_tables]

        with dst:
            with dst.cursor() as cur:
                cur.execute(
                    "TRUNCATE TABLE {} RESTART IDENTITY CASCADE".format(
                        ", ".join(f'"{t}"' for t in reversed(tables))
                    )
                )

            for table in tables:
                copy_table(src, dst, table)

            with dst.cursor() as cur:
                for table in tables:
                    if table in ID_TABLES:
                        cur.execute(
                            "SELECT setval(pg_get_serial_sequence(%s, 'id'), COALESCE((SELECT MAX(id) FROM \"{}\"), 1), (SELECT COUNT(*) FROM \"{}\") > 0)".format(
                                table,
                                table,
                            ),
                            (table,),
                        )
    finally:
        src.close()
        dst.close()


def table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row["name"] for row in rows}


def pg_table_names(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        return {row[0] for row in cur.fetchall()}


def sqlite_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def pg_columns(conn, table: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT column_name
               FROM information_schema.columns
               WHERE table_schema = 'public' AND table_name = %s
               ORDER BY ordinal_position""",
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def copy_table(src: sqlite3.Connection, dst, table: str) -> None:
    src_cols = sqlite_columns(src, table)
    dst_cols = pg_columns(dst, table)
    columns = [c for c in dst_cols if c in src_cols]
    if not columns:
        return

    rows = src.execute(
        f"SELECT {', '.join(quote_sqlite(c) for c in columns)} FROM {quote_sqlite(table)}"
    ).fetchall()
    if not rows:
        print(f"{table}: 0")
        return

    insert = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in columns),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )
    with dst.cursor() as cur:
        cur.executemany(insert, [tuple(row[c] for c in columns) for row in rows])
    print(f"{table}: {len(rows)}")


def quote_sqlite(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


if __name__ == "__main__":
    main()
