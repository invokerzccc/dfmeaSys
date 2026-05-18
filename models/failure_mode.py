"""失效模式数据访问"""

from db.database import get_db
from services.dfmea_calc import calc_rpn, calc_ap


def list_all_failures_flat(project_id: int):
    """列出项目下所有失效模式（扁平列表，用于关联选择）"""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT fm.id, fm.mode_desc, fi.function_desc, sn.name as node_name, sn.id as node_id
               FROM failure_mode fm
               JOIN function_item fi ON fm.function_item_id = fi.id
               JOIN structure_node sn ON fi.node_id = sn.id
               WHERE sn.project_id = ?
               ORDER BY sn.id, fi.id, fm.id""",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_failures(node_id: int):
    """列出某节点下所有失效模式（关联功能项），含关联的参考资料"""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT fm.*, fi.function_desc
               FROM failure_mode fm
               JOIN function_item fi ON fm.function_item_id = fi.id
               WHERE fi.node_id = ?
               ORDER BY fm.order_index, fm.id""",
            (node_id,),
        ).fetchall()
        result = []
        for r in rows:
            fm = dict(r)
            fm["linked_refs"] = _get_linked_refs(conn, fm["id"])
            result.append(fm)
        return result
    finally:
        conn.close()


def _get_linked_refs(conn, failure_mode_id: int):
    """获取失效模式关联的参考资料简要信息"""
    rows = conn.execute(
        """SELECT r.id, r.title, r.type, r.file_path, r.url
           FROM failure_mode_reference fmr
           JOIN reference r ON fmr.reference_id = r.id
           WHERE fmr.failure_mode_id = ?
           ORDER BY r.id""",
        (failure_mode_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_failure(fm_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT fm.*, fi.function_desc
               FROM failure_mode fm
               JOIN function_item fi ON fm.function_item_id = fi.id
               WHERE fm.id = ?""",
            (fm_id,),
        ).fetchone()
        if row:
            fm = dict(row)
            fm["linked_refs"] = _get_linked_refs(conn, fm_id)
            return fm
        return None
    finally:
        conn.close()


def create_failure(function_item_id: int, **kwargs):
    """创建失效模式行，自动计算 RPN 和 AP"""
    conn = get_db()
    try:
        S = kwargs.get("severity_S", 1)
        O = kwargs.get("occurrence_O", 1)
        D = kwargs.get("detection_D", 1)
        rpn = calc_rpn(S, O, D)
        ap = calc_ap(S, O, D)

        reference_ids = kwargs.pop("reference_ids", [])

        fields = ["function_item_id", "rpn", "action_priority"]
        values = [function_item_id, rpn, ap]

        for k in ("mode_desc", "local_effect", "potential_effect", "severity_S", "classification",
                  "potential_cause", "occurrence_O", "prevention_control",
                  "detection_control", "detection_D", "recommended_action",
                  "action_owner", "action_due_date", "action_status", "action_effect",
                  "revised_S", "revised_O", "revised_D", "revised_RPN", "notes"):
            if k in kwargs:
                fields.append(k)
                values.append(kwargs[k])

        placeholders = ", ".join("?" for _ in fields)
        cur = conn.execute(
            f"INSERT INTO failure_mode ({', '.join(fields)}) VALUES ({placeholders})",
            values,
        )
        fm_id = cur.lastrowid
        _set_linked_refs(conn, fm_id, reference_ids)
        conn.commit()
        return get_failure(fm_id)
    finally:
        conn.close()


def _set_linked_refs(conn, failure_mode_id: int, reference_ids: list[int]):
    """设置失效模式关联的参考资料（全量替换）"""
    conn.execute(
        "DELETE FROM failure_mode_reference WHERE failure_mode_id = ?",
        (failure_mode_id,),
    )
    for ref_id in reference_ids:
        conn.execute(
            "INSERT OR IGNORE INTO failure_mode_reference (failure_mode_id, reference_id) VALUES (?, ?)",
            (failure_mode_id, ref_id),
        )


def update_failure(fm_id: int, **kwargs):
    """更新失效模式，自动重算 RPN 和 AP"""
    allowed = {
        "mode_desc", "local_effect", "potential_effect", "severity_S", "classification",
        "potential_cause", "occurrence_O", "prevention_control",
        "detection_control", "detection_D", "recommended_action",
        "action_owner", "action_due_date", "action_status", "action_effect",
        "revised_S", "revised_O", "revised_D", "revised_RPN", "notes",
        "order_index", "function_item_id",
    }
    reference_ids = kwargs.pop("reference_ids", None)
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates and reference_ids is None:
        return get_failure(fm_id)

    conn = get_db()
    try:
        if updates:
            # 获取当前 S/O/D 值用于重算
            cur_fm = conn.execute(
                "SELECT severity_S, occurrence_O, detection_D FROM failure_mode WHERE id = ?",
                (fm_id,),
            ).fetchone()
            if cur_fm:
                S = int(updates.get("severity_S", cur_fm["severity_S"]))
                O = int(updates.get("occurrence_O", cur_fm["occurrence_O"]))
                D = int(updates.get("detection_D", cur_fm["detection_D"]))
                updates["rpn"] = calc_rpn(S, O, D)
                updates["action_priority"] = calc_ap(S, O, D)

            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values())
            conn.execute(
                f"UPDATE failure_mode SET {set_clause} WHERE id = ?",
                values + [fm_id],
            )

        if reference_ids is not None:
            _set_linked_refs(conn, fm_id, reference_ids)

        conn.commit()
        return get_failure(fm_id)
    finally:
        conn.close()


def delete_failure(fm_id: int):
    conn = get_db()
    try:
        conn.execute("DELETE FROM failure_mode WHERE id = ?", (fm_id,))
        conn.commit()
        return True
    finally:
        conn.close()
