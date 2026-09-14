import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "goose_scraped_data.db")
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables: {tables}")

for table in tables:
    table_name = table[0]
    print(f"\nTable: {table_name}")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    col_names = [c[1] for c in columns]
    print(f"Columns: {col_names}")
    
    # Search all text columns for 'pasteurizer'
    search_terms = ["pasteurizer", "milk", "dairy"]
    for term in search_terms:
        for col in col_names:
            try:
                cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE ?", (f'%{term}%',))
                rows = cursor.fetchall()
                if rows:
                    print(f"Matches for '{term}' in column '{col}':")
                    for row in rows:
                        print(row)
            except:
                pass

conn.close()
