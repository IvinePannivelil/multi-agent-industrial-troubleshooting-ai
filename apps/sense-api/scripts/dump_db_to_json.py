import sqlite3
import json
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "goose_scraped_data.db")
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

def get_table_data(table):
    try:
        cur.execute(f"PRAGMA table_info({table})")
        cols = [col[1] for col in cur.fetchall()]
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        return {"columns": cols, "rows": [list(row) for row in rows]}
    except Exception as e:
        return {"error": str(e)}

tables = ["products", "engineers", "courses", "services", "conversations"]
data = {table: get_table_data(table) for table in tables}

out_path = os.path.join(os.path.dirname(__file__), "..", "db_dump.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

conn.close()
print("Success: Database dumped to db_dump.json")
