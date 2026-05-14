"""参考材料数据访问"""

from db.database import get_db


def list_references(project_id: int, node_id: int = None):
    """列出项目的参考材料，可按节点筛选"""
    conn = get_db()
    try:
        if node_id:
            rows = conn.execute(
                """SELECT r.*, sn.name AS node_name
                   FROM reference r
                   LEFT JOIN structure_node sn ON r.node_id = sn.id
                   WHERE r.project_id = ? AND r.node_id = ?
                   ORDER BY r.created_at DESC""",
                (project_id, node_id),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT r.*, sn.name AS node_name
                   FROM reference r
                   LEFT JOIN structure_node sn ON r.node_id = sn.id
                   WHERE r.project_id = ?
                   ORDER BY r.created_at DESC""",
                (project_id,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_reference(ref_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT r.*, sn.name AS node_name
               FROM reference r
               LEFT JOIN structure_node sn ON r.node_id = sn.id
               WHERE r.id = ?""",
            (ref_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_reference(project_id: int, title: str, **kwargs):
    conn = get_db()
    try:
        fields = ["project_id", "title"]
        values = [project_id, title]
        for k in ("node_id", "type", "file_path", "url", "notes"):
            if k in kwargs:
                fields.append(k)
                values.append(kwargs[k])

        placeholders = ", ".join("?" for _ in fields)
        cur = conn.execute(
            f"INSERT INTO reference ({', '.join(fields)}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        return get_reference(cur.lastrowid)
    finally:
        conn.close()


def update_reference(ref_id: int, **kwargs):
    allowed = {"title", "type", "node_id", "file_path", "url", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_reference(ref_id)

    conn = get_db()
    try:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())
        conn.execute(
            f"UPDATE reference SET {set_clause} WHERE id = ?",
            values + [ref_id],
        )
        conn.commit()
        return get_reference(ref_id)
    finally:
        conn.close()


def delete_reference(ref_id: int):
    conn = get_db()
    try:
        # 获取文件路径以便清理
        row = conn.execute("SELECT file_path FROM reference WHERE id = ?", (ref_id,)).fetchone()
        file_path = row["file_path"] if row else None
        conn.execute("DELETE FROM reference WHERE id = ?", (ref_id,))
        conn.commit()
        return file_path
    finally:
        conn.close()
