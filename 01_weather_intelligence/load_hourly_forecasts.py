
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
DB_PATH = PROJECT_DIR / "database" / "citysense.db"

REQUIRED_COLUMNS = [
    "city",
    "latitude",
    "longitude",
    "forecast_time",
    "fetched_at",
    "temperature_c",
    "humidity_pct",
    "precipitation_probability_pct",
    "precipitation_mm",
    "wind_speed_kmh",
]


def main():
    files = sorted(RAW_DIR.glob("weather_hourly_forecast_*.csv"))

    if not files:
        print("ERROR: No hourly forecast CSV files found.")
        return

    frames = []

    for file in files:
        print(f"Reading: {file.name}")
        df = pd.read_csv(file)

        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            print(f"Skipping file; missing columns: {missing}")
            continue

        frames.append(df[REQUIRED_COLUMNS].copy())

    if not frames:
        print("ERROR: No valid hourly forecast CSV files.")
        return

    data = pd.concat(frames, ignore_index=True)

    numeric_columns = [
        "latitude",
        "longitude",
        "temperature_c",
        "humidity_pct",
        "precipitation_probability_pct",
        "precipitation_mm",
        "wind_speed_kmh",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(
        subset=[
            "city",
            "forecast_time",
            "fetched_at",
            "temperature_c",
        ]
    )

    # Remove repeated copies of the same forecast from the CSV collection.
    data = data.drop_duplicates(
        subset=["city", "forecast_time", "fetched_at"],
        keep="last",
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                forecast_time TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_pct REAL,
                precipitation_probability_pct REAL,
                precipitation_mm REAL,
                wind_speed_kmh REAL,
                UNIQUE(city, forecast_time, fetched_at)
            )
        """)

        before = conn.execute(
            "SELECT COUNT(*) FROM weather_forecasts"
        ).fetchone()[0]

        conn.executemany("""
            INSERT INTO weather_forecasts (
                city, latitude, longitude, forecast_time,
                fetched_at, temperature_c, humidity_pct,
                precipitation_probability_pct, precipitation_mm,
                wind_speed_kmh
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city, forecast_time, fetched_at) DO NOTHING
        """, data.itertuples(index=False, name=None))

        after = conn.execute(
            "SELECT COUNT(*) FROM weather_forecasts"
        ).fetchone()[0]

        print("\nHOURLY FORECAST DATABASE REPORT")
        print("--------------------------------")
        print(f"Valid unique CSV records: {len(data)}")
        print(f"Records before loading: {before}")
        print(f"Records after loading: {after}")
        print(f"New records inserted: {after - before}")
        print(f"Database: {DB_PATH}")

        print("\nRECORD COUNTS BY CITY")
        rows = conn.execute("""
            SELECT city, COUNT(*)
            FROM weather_forecasts
            GROUP BY city
            ORDER BY city
        """).fetchall()

        for city, count in rows:
            print(f"{city}: {count}")


if __name__ == "__main__":
    main()