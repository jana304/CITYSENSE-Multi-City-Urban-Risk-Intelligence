import sqlite3

db_path = "database/citysense.db"
connection = sqlite3.connect(db_path)

print("CITYSENSE AI - DATABASE TABLES")
print("=" * 40)

tables = connection.execute(
    "SELECT name FROM sqlite_master "
    "WHERE type='table' ORDER BY name"
).fetchall()

for table in tables:
    print(table[0])

connection.close()
