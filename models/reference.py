"""参考材料数据访问"""

from db.database import get_db


def _attach_nodes(conn, refs):
    """为参考材料列表附加关联节点信息和关联失效模式"""
    if not refs:
        return refs
    ids = [r["id"] for r in refs]
    placeholders = ",".join("?" for _ in ids)
    # 关联节点
    rows = conn.execute(
        f"""SELECT rn.reference_id, sn.id, sn.name
            FROM reference_node rn
            JOIN structure_node sn ON rn.node_id = sn.id
            WHERE rn.reference_id IN ({placeholders})""",
        ids,
    ).fetchall()
    node_map = {}
    for row in rows:
        node_map.setdefault(row["reference_id"], []).append({"id": row["id"], "name": row["name"]})
    # 关联失效模式
    fm_rows = conn.execute(
        f"""SELECT fmr.reference_id, fm.id, fm.mode_desc, sn.name as node_name
            FROM failure_mode_reference fmr
            JOIN failure_mode fm ON fmr.failure_mode_id = fm.id
            JOIN function_item fi ON fm.function_item_id = fi.id
            JOIN structure_node sn ON fi.node_id = sn.id
            WHERE fmr.reference_id IN ({placeholders})
            ORDER BY fm.id""",
        ids,
    ).fetchall()
    fm_map = {}
    for row in fm_rows:
        fm_map.setdefault(row["reference_id"], []).append({"id": row["id"], "mode_desc": row["mode_desc"], "node_name": row["node_name"]})
    for r in refs:
        r["nodes"] = node_map.get(r["id"], [])
        r["node_name"] = r["nodes"][0]["name"] if r["nodes"] else None
        r["failure_modes"] = fm_map.get(r["id"], [])
    return refs


def _set_nodes(conn, ref_id, node_ids):
    """设置参考材料关联的节点"""
    conn.execute("DELETE FROM reference_node WHERE reference_id = ?", (ref_id,))
    if node_ids:
        for nid in node_ids:
            conn.execute(
                "INSERT OR IGNORE INTO reference_node (reference_id, node_id) VALUES (?, ?)",
                (ref_id, nid),
            )


def _set_failure_modes(conn, ref_id, fm_ids):
    """设置参考材料关联的失效模式"""
    conn.execute("DELETE FROM failure_mode_reference WHERE reference_id = ?", (ref_id,))
    if fm_ids:
        for fid in fm_ids:
            conn.execute(
                "INSERT OR IGNORE INTO failure_mode_reference (reference_id, failure_mode_id) VALUES (?, ?)",
                (ref_id, fid),
            )


def list_references(project_id: int, node_id: int = None):
    """列出项目的参考材料，可按节点筛选"""
    conn = get_db()
    try:
        if node_id:
            rows = conn.execute(
                """SELECT DISTINCT r.* FROM reference r
                   JOIN reference_node rn ON r.id = rn.reference_id
                   WHERE r.project_id = ? AND rn.node_id = ?
                   ORDER BY r.created_at DESC""",
                (project_id, node_id),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT r.* FROM reference r
                   WHERE r.project_id = ?
                   ORDER BY r.created_at DESC""",
                (project_id,),
            ).fetchall()
        refs = [dict(r) for r in rows]
        return _attach_nodes(conn, refs)
    finally:
        conn.close()


def get_reference(ref_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM reference WHERE id = ?", (ref_id,)).fetchone()
        if not row:
            return None
        refs = _attach_nodes(conn, [dict(row)])
        return refs[0]
    finally:
        conn.close()


def create_reference(project_id: int, title: str, **kwargs):
    conn = get_db()
    try:
        node_ids = kwargs.pop("node_ids", None)
        fields = ["project_id", "title"]
        values = [project_id, title]
        for k in ("type", "file_path", "url", "notes"):
            if k in kwargs:
                fields.append(k)
                values.append(kwargs[k])

        placeholders = ", ".join("?" for _ in fields)
        cur = conn.execute(
            f"INSERT INTO reference ({', '.join(fields)}) VALUES ({placeholders})",
            values,
        )
        ref_id = cur.lastrowid
        if node_ids:
            _set_nodes(conn, ref_id, node_ids)
        fm_ids = kwargs.get("failure_mode_ids")
        if fm_ids:
            _set_failure_modes(conn, ref_id, fm_ids)
        conn.commit()
        return get_reference(ref_id)
    finally:
        conn.close()


def update_reference(ref_id: int, **kwargs):
    allowed = {"title", "type", "file_path", "url", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    node_ids = kwargs.get("node_ids")

    conn = get_db()
    try:
        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values())
            conn.execute(
                f"UPDATE reference SET {set_clause} WHERE id = ?",
                values + [ref_id],
            )
        if node_ids is not None:
            _set_nodes(conn, ref_id, node_ids)
        fm_ids = kwargs.get("failure_mode_ids")
        if fm_ids is not None:
            _set_failure_modes(conn, ref_id, fm_ids)
        conn.commit()
        return get_reference(ref_id)
    finally:
        conn.close()


def delete_reference(ref_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT file_path FROM reference WHERE id = ?", (ref_id,)).fetchone()
        file_path = row["file_path"] if row else None
        conn.execute("DELETE FROM reference WHERE id = ?", (ref_id,))
        conn.commit()
        return file_path
    finally:
        conn.close()
