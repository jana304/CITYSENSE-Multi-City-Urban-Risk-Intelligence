
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "database" / "citysense.db"

with sqlite3.connect(db_path) as conn:
    print("DATABASE:", db_path)

    print("\nTABLES:")
    query = "SELECT name FROM sqlite_master WHERE type = ? ORDER BY name"
    tables = conn.execute(query, ("table",)).fetchall()

    for table in tables:
        print("-", table[0])

    print("\nWEATHER OBSERVATIONS:")
    result = conn.execute(
        "SELECT COUNT(*) FROM weather_observations"
    ).fetchone()
    print("Total records:", result[0])