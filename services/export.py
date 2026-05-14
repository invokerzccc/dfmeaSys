"""项目导出：Excel / JSON"""

import io
import json
from db.database import get_db
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, numbers
from openpyxl.utils import get_column_letter


# ── Excel 导出（完整数据） ──

DFMEA_HEADERS = [
    "序号", "功能描述", "失效模式", "失效影响(对当前元素)", "失效影响(对系统/整机)",
    "严重度S", "特殊特性", "失效原因", "频度O",
    "预防控制", "探测控制", "探测度D",
    "RPN", "AP", "建议措施",
    "责任人", "期限", "措施状态", "措施效果",
    "修订S", "修订O", "修订D", "修订RPN",
]


def export_xlsx(project_id: int):
    """导出项目 DFMEA 数据为 Excel 文件"""
    conn = get_db()
    try:
        proj = conn.execute("SELECT * FROM project WHERE id = ?", (project_id,)).fetchone()

        rows = conn.execute(
            """SELECT fm.*, fi.function_desc, sn.name AS node_name
               FROM failure_mode fm
               JOIN function_item fi ON fm.function_item_id = fi.id
               JOIN structure_node sn ON fi.node_id = sn.id
               WHERE sn.project_id = ?
               ORDER BY sn.order_index, fi.order_index, fm.order_index""",
            (project_id,),
        ).fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "DFMEA"

        # 标题行
        ws.merge_cells("A1:W1")
        ws["A1"] = f"DFMEA — {proj['name']}"
        ws["A1"].font = Font(size=14, bold=True)
        ws["A1"].alignment = Alignment(horizontal="center")
        ws.merge_cells("A2:W2")
        ws["A2"] = f"导出日期: {proj['updated_at']}"
        ws["A2"].font = Font(size=9, color="666666")
        ws["A2"].alignment = Alignment(horizontal="center")

        # 表头
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(size=10, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin"),
        )

        for col_idx, h in enumerate(DFMEA_HEADERS, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
            cell.border = thin_border

        # 数据行
        for i, row in enumerate(rows):
            rn = i + 1
            vals = [
                rn, row["function_desc"], row["mode_desc"],
                row["local_effect"], row["potential_effect"],
                row["severity_S"], row["classification"], row["potential_cause"], row["occurrence_O"],
                row["prevention_control"], row["detection_control"], row["detection_D"],
                row["rpn"], row["action_priority"], row["recommended_action"],
                row["action_owner"], row["action_due_date"], row["action_status"], row["action_effect"],
                row["revised_S"], row["revised_O"], row["revised_D"], row["revised_RPN"],
            ]
            for col_idx, v in enumerate(vals, 1):
                cell = ws.cell(row=5 + i, column=col_idx, value=v)
                cell.border = thin_border
                cell.font = Font(size=9)
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                # RPN 高亮
                if col_idx == 13 and isinstance(v, int):
                    if v >= 200:
                        cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                    elif v >= 100:
                        cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

        # 列宽
        widths = [5, 20, 18, 22, 22, 5, 7, 18, 5, 18, 18, 5, 7, 5, 18, 8, 10, 8, 18, 6, 6, 6, 8]
        for col_idx, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = w

        # 冻结
        ws.freeze_panes = "A5"

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    finally:
        conn.close()


# ── Excel 模板导出（空表格） ──

def export_template():
    """导出空 DFMEA 模板"""
    wb = Workbook()
    ws = wb.active
    ws.title = "DFMEA模板"

    ws.merge_cells("A1:W1")
    ws["A1"] = "DFMEA 工作表模板"
    ws["A1"].font = Font(size=14, bold=True)
    ws["A1"].alignment = Alignment(horizontal="center")

    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(size=10, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    for col_idx, h in enumerate(DFMEA_HEADERS, 1):
        cell = ws.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = thin_border

    # 示例空行
    for r in range(4, 14):
        for c in range(1, len(DFMEA_HEADERS) + 1):
            cell = ws.cell(row=r, column=c, value="")
            cell.border = thin_border
            cell.font = Font(size=9)

    widths = [5, 20, 18, 22, 22, 5, 7, 18, 5, 18, 18, 5, 7, 5, 18, 8, 10, 8, 18, 6, 6, 6, 8]
    for col_idx, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = w

    ws.freeze_panes = "A4"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


# ── JSON 导出 ──

def export_json(project_id: int):
    """导出项目完整数据为 JSON"""
    conn = get_db()
    try:
        proj = conn.execute("SELECT * FROM project WHERE id = ?", (project_id,)).fetchone()
        nodes = conn.execute("SELECT * FROM structure_node WHERE project_id = ? ORDER BY order_index", (project_id,)).fetchall()
        node_ids = [n["id"] for n in nodes]

        functions = []
        failures = []
        if node_ids:
            placeholders = ",".join("?" for _ in node_ids)
            functions = conn.execute(
                f"SELECT * FROM function_item WHERE node_id IN ({placeholders}) ORDER BY order_index",
                node_ids,
            ).fetchall()
            func_ids = [f["id"] for f in functions]
            if func_ids:
                f_placeholders = ",".join("?" for _ in func_ids)
                failures = conn.execute(
                    f"SELECT * FROM failure_mode WHERE function_item_id IN ({f_placeholders}) ORDER BY order_index",
                    func_ids,
                ).fetchall()

        refs = conn.execute("SELECT * FROM reference WHERE project_id = ?", (project_id,)).fetchall()

        return json.dumps({
            "version": "0.2",
            "exported_at": proj["updated_at"],
            "project": dict(proj),
            "structure": [dict(n) for n in nodes],
            "functions": [dict(f) for f in functions],
            "failures": [dict(fm) for fm in failures],
            "references": [dict(r) for r in refs],
        }, ensure_ascii=False, indent=2, default=str)

    finally:
        conn.close()
