"""结构树节点数据访问"""

from db.database import get_db
from models.project import VersionConflict


def get_tree(project_id: int):
    """获取项目完整结构树（层级嵌套）"""
    conn = get_db()
    try:
        nodes = conn.execute(
            """SELECT * FROM structure_node
               WHERE project_id = ?
               ORDER BY order_index, id""",
            (project_id,),
        ).fetchall()

        # 构建层级树
        node_map = {}
        tree = []

        for row in nodes:
            n = dict(row)
            n["children"] = []
            node_map[n["id"]] = n

        for row in nodes:
            n = node_map[row["id"]]
            if n["parent_id"] and n["parent_id"] in node_map:
                node_map[n["parent_id"]]["children"].append(n)
            else:
                tree.append(n)

        return tree
    finally:
        conn.close()


def get_node(node_id: int):
    """获取单个节点"""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM structure_node WHERE id = ?", (node_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_node(project_id: int, parent_id: int = None, name: str = "", type: str = "部件"):
    """创建节点"""
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO structure_node (project_id, parent_id, name, type)
               VALUES (?, ?, ?, ?)""",
            (project_id, parent_id, name, type),
        )
        conn.commit()
        return get_node(cur.lastrowid)
    finally:
        conn.close()


def update_node(node_id: int, **kwargs):
    """更新节点字段"""
    expected_version = kwargs.pop("expected_version", None)
    allowed = {"name", "type", "part_number", "description", "parent_id", "order_index"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_node(node_id)

    conn = get_db()
    try:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())
        if expected_version is None:
            cur = conn.execute(
                f"UPDATE structure_node SET {set_clause}, version = version + 1, updated_at = datetime('now','localtime') WHERE id = ?",
                values + [node_id],
            )
        else:
            cur = conn.execute(
                f"UPDATE structure_node SET {set_clause}, version = version + 1, updated_at = datetime('now','localtime') WHERE id = ? AND version = ?",
                values + [node_id, expected_version],
            )
        conn.commit()
        if cur.rowcount == 0 and get_node(node_id):
            raise VersionConflict()
        return get_node(node_id)
    finally:
        conn.close()


def delete_node(node_id: int):
    """删除节点（CASCADE 自动删除子节点）"""
    conn = get_db()
    try:
        conn.execute("DELETE FROM structure_node WHERE id = ?", (node_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def move_node(node_id: int, new_parent_id: int | None, new_index: int):
    """
    移动节点到新位置，自动重排 order_index。
    - new_parent_id: 目标父节点 ID（None = 移到顶层）
    - new_index: 在同级兄弟中的目标位置（0-based）
    """
    node = get_node(node_id)
    if node is None:
        return None

    conn = get_db()
    try:
        if new_parent_id is not None:
            target = conn.execute("SELECT project_id FROM structure_node WHERE id = ?", (new_parent_id,)).fetchone()
            if not target or target["project_id"] != node["project_id"]:
                return None

        old_parent_id = node["parent_id"]

        # 1. 将旧父级下其他兄弟的 order_index 重新排列（填补空缺）
        _reindex_siblings(conn, old_parent_id)

        # 2. 确定新父级下的新 order_index
        if new_parent_id is None:
            siblings = conn.execute(
                "SELECT id, order_index FROM structure_node WHERE parent_id IS NULL ORDER BY order_index, id"
            ).fetchall()
        else:
            siblings = conn.execute(
                "SELECT id, order_index FROM structure_node WHERE parent_id = ? ORDER BY order_index, id",
                (new_parent_id,),
            ).fetchall()

        if new_index >= len(siblings):
            new_order = (siblings[-1]["order_index"] + 1) if siblings else 0
        else:
            new_order = siblings[new_index]["order_index"]
            # 把 >= new_order 的兄弟往后移
            for sib in siblings:
                if sib["order_index"] >= new_order:
                    conn.execute(
                        "UPDATE structure_node SET order_index = order_index + 1 WHERE id = ?",
                        (sib["id"],),
                    )

        # 3. 更新节点
        conn.execute(
            """UPDATE structure_node
               SET parent_id = ?, order_index = ?, version = version + 1,
                   updated_at = datetime('now','localtime')
               WHERE id = ?""",
            (new_parent_id, new_order, node_id),
        )

        # 4. 如果父级变了，重新排列旧父级兄弟
        if old_parent_id != new_parent_id:
            _reindex_siblings(conn, old_parent_id)

        conn.commit()
        return get_node(node_id)
    finally:
        conn.close()


def _reindex_siblings(conn, parent_id):
    """紧凑排列同父节点的 order_index（0, 1, 2, ...）"""
    if parent_id is None:
        rows = conn.execute(
            "SELECT id FROM structure_node WHERE parent_id IS NULL ORDER BY order_index, id"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id FROM structure_node WHERE parent_id = ? ORDER BY order_index, id",
            (parent_id,),
        ).fetchall()

    for i, row in enumerate(rows):
        conn.execute(
            "UPDATE structure_node SET order_index = ? WHERE id = ?",
            (i, row["id"]),
        )
