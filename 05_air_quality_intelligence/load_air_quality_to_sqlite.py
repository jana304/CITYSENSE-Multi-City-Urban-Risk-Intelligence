
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "05_air_quality_intelligence" / "data" / "raw"
DB_PATH = PROJECT_DIR / "database" / "citysense.db"

SNAPSHOT_PATTERN = "air_quality_snapshot_*.csv"
FORECAST_PATTERN = "air_quality_hourly_forecast_*.csv"


def load_csv_files(pattern, required_columns):
    files = sorted(RAW_DIR.glob(pattern))

    if not files:
        print(f"No files found for: {pattern}")
        return pd.DataFrame(columns=required_columns)

    frames = []

    for file in files:
        df = pd.read_csv(file)

        missing = set(required_columns) - set(df.columns)
        if missing:
            print(f"Skipping {file.name}; missing columns: {missing}")
            continue

        frames.append(df[required_columns])
        print(f"Read {len(df)} rows from {file.name}")

    if not frames:
        return pd.DataFrame(columns=required_columns)

    result = pd.concat(frames, ignore_index=True)

    # Convert numeric columns safely
    numeric_columns = [
        "latitude", "longitude", "us_aqi",
        "pm2_5_ug_m3", "pm10_ug_m3"
    ]

    for column in numeric_columns:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column], errors="coerce"
            )

    return result


def main():
    snapshots = load_csv_files(
        SNAPSHOT_PATTERN,
        [
            "city", "latitude", "longitude", "current_time",
            "fetched_at", "us_aqi", "pm2_5_ug_m3", "pm10_ug_m3"
        ],
    )

    forecasts = load_csv_files(
        FORECAST_PATTERN,
        [
            "city", "latitude", "longitude", "forecast_time",
            "fetched_at", "us_aqi", "pm2_5_ug_m3", "pm10_ug_m3"
        ],
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS air_quality_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                current_time TEXT,
                fetched_at TEXT NOT NULL,
                us_aqi REAL,
                pm2_5_ug_m3 REAL,
                pm10_ug_m3 REAL,
                UNIQUE(city, fetched_at)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS air_quality_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                forecast_time TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                us_aqi REAL,
                pm2_5_ug_m3 REAL,
                pm10_ug_m3 REAL,
                UNIQUE(city, forecast_time, fetched_at)
            )
        """)

        before_observations = conn.execute(
            "SELECT COUNT(*) FROM air_quality_observations"
        ).fetchone()[0]

        before_forecasts = conn.execute(
            "SELECT COUNT(*) FROM air_quality_forecasts"
        ).fetchone()[0]

        if not snapshots.empty:
            conn.executemany("""
                INSERT INTO air_quality_observations (
                    city, latitude, longitude, current_time,
                    fetched_at, us_aqi, pm2_5_ug_m3, pm10_ug_m3
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(city, fetched_at) DO NOTHING
            """, snapshots.itertuples(index=False, name=None))

        if not forecasts.empty:
            conn.executemany("""
                INSERT INTO air_quality_forecasts (
                    city, latitude, longitude, forecast_time,
                    fetched_at, us_aqi, pm2_5_ug_m3, pm10_ug_m3
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(city, forecast_time, fetched_at) DO NOTHING
            """, forecasts.itertuples(index=False, name=None))

        after_observations = conn.execute(
            "SELECT COUNT(*) FROM air_quality_observations"
        ).fetchone()[0]

        after_forecasts = conn.execute(
            "SELECT COUNT(*) FROM air_quality_forecasts"
        ).fetchone()[0]

    print("\nAIR QUALITY DATABASE LOAD REPORT")
    print("=" * 40)
    print(f"Database: {DB_PATH}")
    print(f"Observation rows read: {len(snapshots)}")
    print(f"Forecast rows read: {len(forecasts)}")
    print(f"Observation rows before: {before_observations}")
    print(f"Observation rows after: {after_observations}")
    print(f"Forecast rows before: {before_forecasts}")
    print(f"Forecast rows after: {after_forecasts}")
    print(
        "New observation rows:",
        after_observations - before_observations
    )
    print(
        "New forecast rows:",
        after_forecasts - before_forecasts
    )


if __name__ == "__main__":
    main()