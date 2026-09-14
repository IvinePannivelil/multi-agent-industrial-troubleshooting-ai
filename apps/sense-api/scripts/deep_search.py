import sqlite3
import os
import glob

def check_db():
    db_path = os.path.join(os.path.dirname(__file__), "..", "goose_scraped_data.db")
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    print("Checking database...")
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cur.fetchall()]
        for table in tables:
            cur.execute(f"PRAGMA table_info({table})")
            cols = [c[1] for c in cur.fetchall()]
            query = f"SELECT * FROM {table} WHERE " + " OR ".join([f"{c} LIKE '%pasteurizer%'" for c in cols if "TEXT" in [col[2] for col in cur.execute(f"PRAGMA table_info({table})").fetchall() if col[1] == c]])
            # Actually just search all columns that could have text
            search_cols = [c for c in cols] # Simplified for this script
            where_clause = " OR ".join([f"CAST({c} AS TEXT) LIKE '%pasteurizer%'" for c in search_cols])
            cur.execute(f"SELECT * FROM {table} WHERE {where_clause}")
            rows = cur.fetchall()
            if rows:
                print(f"Found {len(rows)} matches in table {table}")
                for row in rows[:5]:
                    print(row)
    except Exception as e:
        print(f"DB Error: {e}")
    conn.close()

def check_files():
    print("\nChecking for files...")
    patterns = ["**/*pasteurizer*", "**/*milk*", "**/*dairy*"]
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    for pattern in patterns:
        for file in glob.glob(os.path.join(base_dir, pattern), recursive=True):
            if os.path.isfile(file):
                print(f"Found file: {file}")

if __name__ == "__main__":
    check_db()
    check_files()
