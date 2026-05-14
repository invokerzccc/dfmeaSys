"""RPN 计算与 AP（措施优先级）判定"""

from db.database import get_db


def calc_rpn(S: int, O: int, D: int) -> int:
    return S * O * D


def calc_ap(S: int, O: int, D: int) -> str:
    """
    基于 AIAG-VDA 手册查表判定 AP（H/M/L）。
    优先从数据库 ap_matrix 表查询，降级使用硬编码规则。
    """
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT ap FROM ap_matrix
               WHERE ? BETWEEN s_from AND s_to
                 AND ? BETWEEN o_from AND o_to
                 AND ? BETWEEN d_from AND d_to
               LIMIT 1""",
            (S, O, D),
        ).fetchone()
        if row:
            return row["ap"]
    except Exception:
        pass
    finally:
        conn.close()

    # 降级：硬编码规则（与 seed.sql 保持一致）
    return _ap_fallback(S, O, D)


def _ap_fallback(S: int, O: int, D: int) -> str:
    """AP 判定后备逻辑（与 ap_matrix 表数据一致）"""
    # fmt: off
    rules = [
        (9, 10, 9, 10, 1, 10, 'H'),
        (9, 10, 7,  8, 1, 10, 'H'),
        (9, 10, 4,  6, 1,  9, 'H'), (9, 10, 4, 6, 10, 10, 'M'),
        (9, 10, 2,  3, 1,  7, 'H'), (9, 10, 2, 3,  8,  9, 'M'), (9, 10, 2, 3, 10, 10, 'L'),
        (9, 10, 1,  1, 1,  2, 'H'), (9, 10, 1, 1,  3,  5, 'M'), (9, 10, 1, 1,  6, 10, 'L'),
        (7, 8, 9, 10, 1, 10, 'H'),
        (7, 8, 7,  8, 1,  8, 'H'), (7, 8, 7, 8,  9, 10, 'M'),
        (7, 8, 4,  6, 1,  5, 'H'), (7, 8, 4, 6,  6, 10, 'M'),
        (7, 8, 2,  3, 1,  3, 'H'), (7, 8, 2, 3,  4,  8, 'M'), (7, 8, 2, 3,  9, 10, 'L'),
        (7, 8, 1,  1, 1,  5, 'M'), (7, 8, 1, 1,  6, 10, 'L'),
        (4, 6, 9, 10, 1, 10, 'H'),
        (4, 6, 7,  8, 1,  7, 'H'), (4, 6, 7, 8,  8, 10, 'M'),
        (4, 6, 4,  6, 1,  3, 'H'), (4, 6, 4, 6,  4, 10, 'M'),
        (4, 6, 2,  3, 1,  1, 'H'), (4, 6, 2, 3,  2,  7, 'M'), (4, 6, 2, 3,  8, 10, 'L'),
        (4, 6, 1,  1, 1,  4, 'M'), (4, 6, 1, 1,  5, 10, 'L'),
        (2, 3, 9, 10, 1, 10, 'H'),
        (2, 3, 7,  8, 1,  5, 'H'), (2, 3, 7, 8,  6, 10, 'M'),
        (2, 3, 4,  6, 1,  2, 'H'), (2, 3, 4, 6,  3,  8, 'M'), (2, 3, 4, 6,  9, 10, 'L'),
        (2, 3, 2,  3, 1,  1, 'H'), (2, 3, 2, 3,  2,  5, 'M'), (2, 3, 2, 3,  6, 10, 'L'),
        (2, 3, 1,  1, 1,  2, 'M'), (2, 3, 1, 1,  3, 10, 'L'),
        (1, 1, 9, 10, 1, 10, 'H'),
        (1, 1, 7,  8, 1,  5, 'H'), (1, 1, 7, 8,  6, 10, 'M'),
        (1, 1, 4,  6, 1,  2, 'H'), (1, 1, 4, 6,  3,  8, 'M'), (1, 1, 4, 6,  9, 10, 'L'),
        (1, 1, 2,  3, 1,  1, 'H'), (1, 1, 2, 3,  2,  5, 'M'), (1, 1, 2, 3,  6, 10, 'L'),
        (1, 1, 1,  1, 1,  2, 'M'), (1, 1, 1, 1,  3, 10, 'L'),
    ]
    # fmt: on
    for s1, s2, o1, o2, d1, d2, ap in rules:
        if s1 <= S <= s2 and o1 <= O <= o2 and d1 <= D <= d2:
            return ap
    return "L"


def rpn_level(rpn: int) -> str:
    """返回 RPN 风险等级标签"""
    if rpn >= 200:
        return "H"
    elif rpn >= 100:
        return "M"
    return "L"
