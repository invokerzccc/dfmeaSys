"""项目导出：Excel / JSON"""

import io
import json
from db.database import get_db
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, numbers
from openpyxl.utils import get_column_letter


# ── Excel 导出（完整数据） ──

DFMEA_HEADERS = [
    "序号", "结构路径", "功能描述", "设计要求", "性能指标", "接口说明",
    "失效模式", "失效影响(对当前元素)", "失效影响(对系统/整机)",
    "严重度S", "特殊特性", "失效原因", "频度O",
    "预防控制", "探测控制", "探测度D",
    "RPN", "AP", "建议措施",
    "责任人", "期限", "措施状态", "措施效果",
    "修订S", "修订O", "修订D", "修订RPN",
]


def _build_path_map(conn, project_id):
    """构建 node_id -> 完整结构路径 的映射"""
    nodes = conn.execute(
        "SELECT id, parent_id, name FROM structure_node WHERE project_id = ? ORDER BY order_index",
        (project_id,),
    ).fetchall()

    # 构建 parent 映射
    node_map = {n["id"]: {"name": n["name"], "parent_id": n["parent_id"]} for n in nodes}

    def get_path(node_id):
        parts = []
        cur = node_id
        while cur:
            info = node_map.get(cur)
            if not info:
                break
            parts.append(info["name"])
            cur = info["parent_id"]
        return " > ".join(reversed(parts))

    return {nid: get_path(nid) for nid in node_map}


def export_xlsx(project_id: int):
    """导出项目 DFMEA 数据为 Excel 文件（含结构路径和功能分析）"""
    conn = get_db()
    try:
        proj = conn.execute("SELECT * FROM project WHERE id = ?", (project_id,)).fetchone()
        path_map = _build_path_map(conn, project_id)

        rows = conn.execute(
            """SELECT fm.*, fi.function_desc, fi.requirement, fi.performance_spec, fi.interface_desc,
                      sn.name AS node_name, sn.id AS node_id
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

        ncols = len(DFMEA_HEADERS)
        last_col = get_column_letter(ncols)

        # 标题行
        ws.merge_cells(f"A1:{last_col}1")
        ws["A1"] = f"DFMEA — {proj['name']}"
        ws["A1"].font = Font(size=14, bold=True)
        ws["A1"].alignment = Alignment(horizontal="center")
        ws.merge_cells(f"A2:{last_col}2")
        ws["A2"] = f"导出日期: {proj['updated_at']}"
        ws["A2"].font = Font(size=9, color="666666")
        ws["A2"].alignment = Alignment(horizontal="center")

        # 列分组：基本信息 | 功能分析 | DFMEA分析
        ws.merge_cells("A3:B3")   # 基本信息
        ws["A3"] = "基本信息"
        ws.merge_cells("C3:F3")   # 功能分析
        ws["C3"] = "功能分析"
        ws.merge_cells(f"G3:{last_col}3")  # DFMEA
        ws["G3"] = "DFMEA 失效分析"
        group_fill = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
        group_font = Font(size=9, bold=True, color="2C5282")
        for col in ["A", "C", "G"]:
            cell = ws[f"{col}3"]
            cell.font = group_font
            cell.fill = group_fill
            cell.alignment = Alignment(horizontal="center")

        # 表头
        header_fill = PatternFill(start_color="2C6280", end_color="2C6280", fill_type="solid")
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

        # RPN 列号 (0-indexed: 序号=1, 结构路径=2, 功能描述=3, 设计要求=4, 性能指标=5, 接口说明=6,
        #   失效模式=7, 失效影响(当前)=8, 失效影响(系统)=9, S=10, 分类=11, 原因=12, O=13,
        #   预防=14, 探测=15, D=16, RPN=17, AP=18, 措施=19, ...)
        RPN_COL = 17
        AP_COL = 18
        S_COL = 10
        O_COL = 13
        D_COL = 16

        # 风险颜色
        rpn_high = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        rpn_mid = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        ap_h_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        ap_m_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        ap_l_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        path_fill = PatternFill(start_color="F7FAFC", end_color="F7FAFC", fill_type="solid")

        # 数据行
        for i, row in enumerate(rows):
            rn = i + 1
            struct_path = path_map.get(row["node_id"], row["node_name"])
            vals = [
                rn, struct_path,
                row["function_desc"], row["requirement"] or "", row["performance_spec"] or "", row["interface_desc"] or "",
                row["mode_desc"],
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

                # 结构路径列浅底色
                if col_idx == 2:
                    cell.fill = path_fill

                # RPN 高亮
                if col_idx == RPN_COL and isinstance(v, int):
                    if v >= 200:
                        cell.fill = rpn_high
                        cell.font = Font(size=9, bold=True, color="B91C1C")
                    elif v >= 100:
                        cell.fill = rpn_mid
                        cell.font = Font(size=9, bold=True, color="A16207")

                # AP 高亮
                if col_idx == AP_COL:
                    if v == "H":
                        cell.fill = ap_h_fill
                        cell.font = Font(size=9, bold=True, color="DC2626")
                    elif v == "M":
                        cell.fill = ap_m_fill
                        cell.font = Font(size=9, bold=True, color="D97706")
                    elif v == "L":
                        cell.fill = ap_l_fill
                        cell.font = Font(size=9, bold=True, color="16A34A")

                # S/O/D 加粗居中
                if col_idx in (S_COL, O_COL, D_COL):
                    cell.alignment = Alignment(horizontal="center", vertical="top")
                    cell.font = Font(size=9, bold=True)

        # 列宽
        widths = {
            1: 5,    # 序号
            2: 24,   # 结构路径
            3: 20,   # 功能描述
            4: 22,   # 设计要求
            5: 22,   # 性能指标
            6: 18,   # 接口说明
            7: 18,   # 失效模式
            8: 22,   # 失效影响(当前)
            9: 22,   # 失效影响(系统)
            10: 5,   # S
            11: 6,   # 分类
            12: 18,  # 失效原因
            13: 5,   # O
            14: 20,  # 预防控制
            15: 20,  # 探测控制
            16: 5,   # D
            17: 7,   # RPN
            18: 5,   # AP
            19: 20,  # 建议措施
            20: 8,   # 责任人
            21: 10,  # 期限
            22: 8,   # 状态
            23: 18,  # 措施效果
            24: 6,   # 修订S
            25: 6,   # 修订O
            26: 6,   # 修订D
            27: 8,   # 修订RPN
        }
        for col_idx, w in widths.items():
            ws.column_dimensions[get_column_letter(col_idx)].width = w

        # 冻结
        ws.freeze_panes = "A5"

        # 自动筛选
        ws.auto_filter.ref = f"A4:{last_col}{4 + len(rows)}"

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
