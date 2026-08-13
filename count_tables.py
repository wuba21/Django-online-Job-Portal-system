import sqlite3
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Total tables: {len(tables)}")
for idx, t in enumerate(tables):
    print(f"{idx+1}. {t[0]}")
