"""项目权限检查。"""

from fastapi import HTTPException, status

from db.database import get_db

WRITE_ROLES = {"owner", "editor"}
MANAGE_MEMBER_ROLES = {"owner"}


def require_project_access(project_id: int, user, write: bool = False) -> None:
    if not can_access_project(project_id, user, write):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该项目")


def can_access_project(project_id: int, user, write: bool = False) -> bool:
    if not write:
        return True
    if user.get("is_admin"):
        return True
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT role FROM project_member WHERE project_id = ? AND user_id = ?",
            (project_id, user["id"]),
        ).fetchone()
        if not row:
            return False
        return row["role"] in WRITE_ROLES if write else True
    finally:
        conn.close()


def get_project_role(project_id: int, user) -> str | None:
    if user.get("is_admin"):
        return "admin"
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT role FROM project_member WHERE project_id = ? AND user_id = ?",
            (project_id, user["id"]),
        ).fetchone()
        return row["role"] if row else None
    finally:
        conn.close()


def can_manage_project_members(project_id: int, user) -> bool:
    if user.get("is_admin"):
        return True
    role = get_project_role(project_id, user)
    return role in MANAGE_MEMBER_ROLES


def require_project_member_management(project_id: int, user) -> None:
    if not can_manage_project_members(project_id, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要项目负责人或管理员权限")


def require_entity_access(entity_type: str, entity_id: int, user, write: bool = False) -> int:
    project_id = project_id_for_entity(entity_type, entity_id)
    if project_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对象不存在")
    require_project_access(project_id, user, write)
    return project_id


def project_id_for_entity(entity_type: str, entity_id: int):
    sql_map = {
        "node": "SELECT project_id FROM structure_node WHERE id = ?",
        "function": """
            SELECT sn.project_id
            FROM function_item fi
            JOIN structure_node sn ON fi.node_id = sn.id
            WHERE fi.id = ?
        """,
        "failure": """
            SELECT sn.project_id
            FROM failure_mode fm
            JOIN function_item fi ON fm.function_item_id = fi.id
            JOIN structure_node sn ON fi.node_id = sn.id
            WHERE fm.id = ?
        """,
        "reference": "SELECT project_id FROM reference WHERE id = ?",
    }
    sql = sql_map.get(entity_type)
    if not sql:
        return None
    conn = get_db()
    try:
        row = conn.execute(sql, (entity_id,)).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def ensure_function_in_node(function_item_id: int, node_id: int) -> None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM function_item WHERE id = ? AND node_id = ?",
            (function_item_id, node_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="功能项不属于当前节点")
    finally:
        conn.close()


def get_project_members(project_id: int):
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT u.id, u.username, u.display_name, u.is_admin, u.is_active, pm.role
               FROM project_member pm
               JOIN user_account u ON pm.user_id = u.id
               WHERE pm.project_id = ?
               ORDER BY pm.role, u.username""",
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def set_project_member(project_id: int, user_id: int, role: str):
    if role not in {"owner", "editor", "viewer"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效角色")
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO project_member (project_id, user_id, role)
               VALUES (?, ?, ?)
               ON CONFLICT(project_id, user_id) DO UPDATE SET role = excluded.role""",
            (project_id, user_id, role),
        )
        conn.commit()
    finally:
        conn.close()


def remove_project_member(project_id: int, user_id: int):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM project_member WHERE project_id = ? AND user_id = ?",
            (project_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()
