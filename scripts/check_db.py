"""Check database state"""
import sqlite3

conn = sqlite3.connect(r'C:\Users\invok\dfmea_db\dfmea.db')
conn.row_factory = sqlite3.Row

print('=== FULL REFERENCE ===')
for r in conn.execute('SELECT * FROM reference'):
    d = dict(r)
    for k, v in d.items():
        if v and len(str(v)) > 100:
            d[k] = str(v)[:100] + '...'
    print(d)

print()
print('=== FAILURE MODES (project 7) ===')
for r in conn.execute("""
    SELECT fm.id, fm.mode_desc, fm.local_effect, fm.potential_effect,
           fi.function_desc, sn.name as node_name, sn.id as node_id
    FROM failure_mode fm
    JOIN function_item fi ON fm.function_item_id = fi.id
    JOIN structure_node sn ON fi.node_id = sn.id
    WHERE sn.project_id = 7
    ORDER BY sn.id, fi.id, fm.id
"""):
    print(f'  fm_id={r["id"]} node={r["node_name"]}(id={r["node_id"]}) func={r["function_desc"][:50]} mode={r["mode_desc"][:60]}')

print()
print('=== FUNCTIONS FOR ACDC-24V (node 30) ===')
for r in conn.execute('SELECT * FROM function_item WHERE node_id = 30'):
    print(dict(r))

print()
print('=== FAILURE MODES FOR ACDC-24V RELATED ===')
for r in conn.execute("""
    SELECT fm.*, fi.function_desc
    FROM failure_mode fm
    JOIN function_item fi ON fm.function_item_id = fi.id
    WHERE fi.node_id = 30
"""):
    print(f'  fm_id={r["id"]} func={r["function_desc"]} mode={r["mode_desc"]}')

print()
print('=== STRUCTURE SUBTREE (parent=22 or id=30) ===')
for r in conn.execute("""
    SELECT * FROM structure_node
    WHERE id = 30 OR parent_id = 30
    ORDER BY id
"""):
    print(f'  id={r["id"]} parent={r["parent_id"]} name={r["name"]} type={r["type"]} desc={r["description"][:80]}')

conn.close()
