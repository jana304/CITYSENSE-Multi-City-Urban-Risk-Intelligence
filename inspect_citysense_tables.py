
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "database" / "citysense.db"
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

tables = [
    "weather_observations",
    "weather_forecasts",
    "traffic_incidents",
    "air_quality_observations",
    "air_quality_forecasts",
]

for table in tables:
    print(f"\n--- {table} ---")

    try:
        count = cursor.execute(
            f"SELECT COUNT(*) FROM [{table}]"
        ).fetchone()[0]

        columns = cursor.execute(
            f"PRAGMA table_info([{table}])"
        ).fetchall()

        print("Records:", count)
        print("Columns:", ", ".join(column[1] for column in columns))

        if count > 0:
            latest = cursor.execute(
                f"SELECT * FROM [{table}] LIMIT 1"
            ).fetchone()
            print("Sample record:", latest)

    except sqlite3.Error as error:
        print("Database error:", error)

connection.close()
