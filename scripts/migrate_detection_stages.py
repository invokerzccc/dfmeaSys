"""Migrate detection_control stage names in all failure_mode entries."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH
import sqlite3

mappings = [
    ("[下线检测]", "[制程]"),
    ("[过程检测]", "[制程]"),
    ("[设计分析]", "[设计]"),
    ("[验证测试]", "[验证]"),
]

conn = sqlite3.connect(DB_PATH)
try:
    total = 0
    for old_tag, new_tag in mappings:
        cur = conn.execute(
            "UPDATE failure_mode SET detection_control = REPLACE(detection_control, ?, ?) "
            "WHERE detection_control LIKE '%' || ? || '%'",
            (old_tag, new_tag, old_tag),
        )
        n = cur.rowcount
        total += n
        if n:
            print(f"  {old_tag} → {new_tag}: {n} rows updated")
    conn.commit()
    print(f"Done. {total} total rows updated.")
finally:
    conn.close()
