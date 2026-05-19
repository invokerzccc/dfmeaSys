"""操作审计日志。"""

from db.database import get_db


def log_action(project_id: int, user, action: str, entity_type: str, entity_id: int | None, detail: str = "") -> None:
    if not project_id:
        return
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO audit_log (project_id, user_id, username, action, entity_type, entity_id, detail)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                user.get("id") if user else None,
                user.get("username", "") if user else "",
                action,
                entity_type,
                entity_id,
                detail,
            ),
        )
        conn.commit()
    finally:
        conn.close()
