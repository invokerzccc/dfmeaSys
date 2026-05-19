"""项目数据访问"""

import sqlite3
from db.database import get_db


class VersionConflict(Exception):
    """记录已被其他用户更新。"""


def list_projects(user=None):
    """列出所有未删除的项目，含统计"""
    conn = get_db()
    try:
        where = "p.is_deleted = 0"
        rows = conn.execute("""
            SELECT p.*,
                   (SELECT COUNT(*) FROM structure_node WHERE project_id = p.id) AS node_count,
                   (SELECT COUNT(*) FROM function_item fi
                    JOIN structure_node sn ON fi.node_id = sn.id
                    WHERE sn.project_id = p.id) AS function_count,
                   (SELECT COUNT(*) FROM failure_mode fm
                    JOIN function_item fi ON fm.function_item_id = fi.id
                    JOIN structure_node sn ON fi.node_id = sn.id
                    WHERE sn.project_id = p.id AND (fm.rpn >= 100 OR fm.action_priority = 'H')) AS high_risk_count
            FROM project p
            WHERE {where}
            ORDER BY p.updated_at DESC
        """.format(where=where)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_project(project_id: int):
    """获取单个项目详情"""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM project WHERE id = ? AND is_deleted = 0", (project_id,)
        ).fetchone()
        if row is None:
            return None
        d = dict(row)

        # 统计
        d["node_count"] = conn.execute(
            "SELECT COUNT(*) FROM structure_node WHERE project_id = ?", (project_id,)
        ).fetchone()[0]
        return d
    finally:
        conn.close()


def create_project(name: str, description: str = "", template_id: int = None, actor_id: int | None = None):
    """创建项目，可选从已有项目复制结构"""
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO project (name, description) VALUES (?, ?)",
            (name, description),
        )
        project_id = cur.lastrowid

        # 从模板项目复制结构树
        if template_id:
            _copy_structure(conn, template_id, project_id)

        if actor_id:
            conn.execute(
                "INSERT OR IGNORE INTO project_member (project_id, user_id, role) VALUES (?, ?, 'owner')",
                (project_id, actor_id),
            )

        conn.commit()
        return get_project(project_id)
    finally:
        conn.close()


def update_project(project_id: int, name: str, description: str, expected_version: int | None = None):
    """更新项目信息"""
    conn = get_db()
    try:
        if expected_version is None:
            cur = conn.execute(
                """UPDATE project
                   SET name = ?, description = ?, version = version + 1, updated_at = datetime('now','localtime')
                   WHERE id = ?""",
                (name, description, project_id),
            )
        else:
            cur = conn.execute(
                """UPDATE project
                   SET name = ?, description = ?, version = version + 1, updated_at = datetime('now','localtime')
                   WHERE id = ? AND version = ?""",
                (name, description, project_id, expected_version),
            )
        conn.commit()
        if cur.rowcount == 0 and get_project(project_id):
            raise VersionConflict()
        return get_project(project_id)
    finally:
        conn.close()


def delete_project(project_id: int):
    """软删除项目"""
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE project SET is_deleted = 1, version = version + 1, updated_at = datetime('now','localtime') WHERE id = ?",
            (project_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_trash():
    """列出回收站中的项目"""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM project WHERE is_deleted = 1 ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def restore_project(project_id: int):
    """从回收站恢复项目"""
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE project SET is_deleted = 0, updated_at = datetime('now','localtime') WHERE id = ? AND is_deleted = 1",
            (project_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def permanent_delete_project(project_id: int):
    """永久删除项目及其所有关联数据"""
    conn = get_db()
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.execute("DELETE FROM project WHERE id = ? AND is_deleted = 1", (project_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_trash():
    """列出回收站中的项目"""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM project WHERE is_deleted = 1 ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def restore_project(project_id: int):
    """从回收站恢复项目"""
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE project SET is_deleted = 0, updated_at = datetime('now','localtime') WHERE id = ? AND is_deleted = 1",
            (project_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def permanent_delete_project(project_id: int):
    """永久删除项目及其所有关联数据"""
    conn = get_db()
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.execute("DELETE FROM project WHERE id = ? AND is_deleted = 1", (project_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def _copy_structure(conn: sqlite3.Connection, from_project: int, to_project: int):
    """
    从模板项目复制整个结构树到新项目。
    注意：仅复制结构节点，不复制功能项和失效数据。
    """
    # 复制顶层节点
    top_nodes = conn.execute(
        "SELECT * FROM structure_node WHERE project_id = ? AND parent_id IS NULL ORDER BY order_index",
        (from_project,),
    ).fetchall()

    for node in top_nodes:
        _copy_node_recursive(conn, node["id"], None, to_project)


def _copy_node_recursive(conn: sqlite3.Connection, src_node_id: int, new_parent_id: int | None, to_project: int):
    """递归复制节点及其子节点"""
    src = conn.execute("SELECT * FROM structure_node WHERE id = ?", (src_node_id,)).fetchone()
    if src is None:
        return

    cur = conn.execute(
        """INSERT INTO structure_node (project_id, parent_id, name, type, part_number, description, order_index)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (to_project, new_parent_id, src["name"], src["type"], src["part_number"], src["description"], src["order_index"]),
    )
    new_id = cur.lastrowid

    # 递归复制子节点
    children = conn.execute(
        "SELECT * FROM structure_node WHERE parent_id = ? ORDER BY order_index", (src_node_id,)
    ).fetchall()

    for child in children:
        _copy_node_recursive(conn, child["id"], new_id, to_project)
