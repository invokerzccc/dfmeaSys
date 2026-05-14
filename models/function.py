"""功能项数据访问"""

from db.database import get_db


def list_functions(node_id: int):
    """列出某节点下所有功能项"""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT * FROM function_item
               WHERE node_id = ?
               ORDER BY order_index, id""",
            (node_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_function(func_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM function_item WHERE id = ?", (func_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_function(node_id: int, function_desc: str, **kwargs):
    """创建功能项"""
    conn = get_db()
    try:
        fields = ["node_id", "function_desc"]
        values = [node_id, function_desc]
        for k in ("requirement", "performance_spec", "interface_desc"):
            if k in kwargs:
                fields.append(k)
                values.append(kwargs[k])

        placeholders = ", ".join("?" for _ in fields)
        cur = conn.execute(
            f"INSERT INTO function_item ({', '.join(fields)}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        return get_function(cur.lastrowid)
    finally:
        conn.close()


def update_function(func_id: int, **kwargs):
    """更新功能项字段"""
    allowed = {"function_desc", "requirement", "performance_spec", "interface_desc", "order_index"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_function(func_id)

    conn = get_db()
    try:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())
        conn.execute(
            f"UPDATE function_item SET {set_clause} WHERE id = ?",
            values + [func_id],
        )
        conn.commit()
        return get_function(func_id)
    finally:
        conn.close()


def delete_function(func_id: int):
    conn = get_db()
    try:
        conn.execute("DELETE FROM function_item WHERE id = ?", (func_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def batch_create(node_id: int, lines: list[str]):
    """批量创建功能项：每行一个功能描述"""
    conn = get_db()
    created = []
    try:
        for line in lines:
            text = line.strip()
            if not text:
                continue
            cur = conn.execute(
                "INSERT INTO function_item (node_id, function_desc) VALUES (?, ?)",
                (node_id, text),
            )
            created.append({"id": cur.lastrowid, "function_desc": text})
        conn.commit()
        return created
    finally:
        conn.close()
