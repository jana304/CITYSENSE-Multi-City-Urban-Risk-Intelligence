
import sqlite3
from pathlib import Path

import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
DB_PATH = PROJECT_DIR / "database" / "citysense.db"

REQUIRED_COLUMNS = [
    "city",
    "latitude",
    "longitude",
    "observed_time",
    "fetched_at",
    "temperature_c",
    "humidity_pct",
    "precipitation_mm",
    "wind_speed_kmh",
]

def main():
    csv_files = sorted(RAW_DIR.glob("weather_snapshot_*.csv"))

    if not csv_files:
        print("ERROR: No weather snapshot CSV files found.")
        return

    frames = []

    for csv_file in csv_files:
        print(f"Reading: {csv_file.name}")
        df = pd.read_csv(csv_file)

        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            print(f"Skipping file; missing columns: {missing}")
            continue

        df = df[REQUIRED_COLUMNS].copy()
        frames.append(df)

    if not frames:
        print("ERROR: No valid CSV files were found.")
        return

    data = pd.concat(frames, ignore_index=True)

    numeric_columns = [
        "latitude",
        "longitude",
        "temperature_c",
        "humidity_pct",
        "precipitation_mm",
        "wind_speed_kmh",
    ]

    for col in numeric_columns:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(
        subset=[
            "city",
            "observed_time",
            "fetched_at",
            "temperature_c",
            "humidity_pct",
            "precipitation_mm",
            "wind_speed_kmh",
        ]
    )

    # Keep the latest fetched version of each city and observation time.
    data = data.sort_values("fetched_at")
    data = data.drop_duplicates(
        subset=["city", "observed_time"],
        keep="last",
    )

    # Do not replace the database or its historical records.
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                observed_time TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_pct REAL,
                precipitation_mm REAL,
                wind_speed_kmh REAL,
                UNIQUE(city, observed_time)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS cities (
                city TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL
            )
        """)

        conn.executemany(
            """
            INSERT INTO cities (city, latitude, longitude)
            VALUES (?, ?, ?)
            ON CONFLICT(city) DO UPDATE SET
                latitude = excluded.latitude,
                longitude = excluded.longitude
            """,
            data[
                ["city", "latitude", "longitude"]
            ].drop_duplicates("city").itertuples(index=False, name=None),
        )

        before = conn.execute(
            "SELECT COUNT(*) FROM weather_observations"
        ).fetchone()[0]

        conn.executemany(
            """
            INSERT INTO weather_observations (
                city, latitude, longitude, observed_time,
                fetched_at, temperature_c, humidity_pct,
                precipitation_mm, wind_speed_kmh
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city, observed_time) DO NOTHING
            """,
            data.itertuples(index=False, name=None),
        )

        after = conn.execute(
            "SELECT COUNT(*) FROM weather_observations"
        ).fetchone()[0]

        print("\nDATABASE LOAD REPORT")
        print("--------------------")
        print(f"Valid unique CSV records: {len(data)}")
        print(f"Records before loading: {before}")
        print(f"Records after loading: {after}")
        print(f"New records inserted: {after - before}")
        print(f"Database: {DB_PATH}")

        print("\nCITY RECORD COUNTS")
        for city, count in conn.execute("""
            SELECT city, COUNT(*)
            FROM weather_observations
            GROUP BY city
            ORDER BY city
        """):
            print(f"{city}: {count}")

if __name__ == "__main__":
    main()