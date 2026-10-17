
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "citysense.db"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HORIZONS = [5, 10]


def main():
    with sqlite3.connect(DB_PATH) as conn:
        latest_batch = conn.execute("""
            SELECT MAX(fetched_at)
            FROM weather_forecasts
        """).fetchone()[0]

        if not latest_batch:
            print("ERROR: No hourly forecasts found in the database.")
            return

        data = pd.read_sql_query("""
            SELECT city, forecast_time, fetched_at,
                   temperature_c, humidity_pct,
                   precipitation_probability_pct,
                   precipitation_mm, wind_speed_kmh
            FROM weather_forecasts
            WHERE fetched_at = ?
            ORDER BY city, forecast_time
        """, conn, params=(latest_batch,))

    # Interpret API forecast timestamps in Indian local time.
    data["forecast_time"] = pd.to_datetime(data["forecast_time"])
    reference_time = (
        pd.Timestamp(latest_batch)
        .tz_convert("Asia/Kolkata")
        .tz_localize(None)
    )

    results = []

    for city, city_data in data.groupby("city"):
        city_data = city_data.sort_values("forecast_time")

        for hours in HORIZONS:
            target_time = reference_time + pd.Timedelta(hours=hours)

            # Choose the hourly forecast closest to the target time.
            distances = (
                city_data["forecast_time"] - target_time
            ).abs()

            row = city_data.loc[distances.idxmin()]
            difference_minutes = abs(
                (row["forecast_time"] - target_time).total_seconds()
            ) / 60

            if difference_minutes > 30:
                print(
                    f"WARNING: {city}, +{hours}h forecast "
                    "is more than 30 minutes from the target."
                )

            results.append({
                "city": city,
                "reference_time": reference_time.isoformat(),
                "horizon_hours": hours,
                "target_time": target_time.isoformat(),
                "forecast_time": row["forecast_time"].isoformat(),
                "forecast_offset_minutes": round(difference_minutes, 1),
                "temperature_c": row["temperature_c"],
                "humidity_pct": row["humidity_pct"],
                "precipitation_probability_pct":
                    row["precipitation_probability_pct"],
                "precipitation_mm": row["precipitation_mm"],
                "wind_speed_kmh": row["wind_speed_kmh"],
                "fetched_at": latest_batch,
            })

    outlook = pd.DataFrame(results)

    # Save a CSV for inspection and future Power BI use.
    output_file = OUTPUT_DIR / "weather_horizon_outlook.csv"
    outlook.to_csv(output_file, index=False)

    # Store each forecast batch and horizon without overwriting history.
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_horizon_outlook (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                reference_time TEXT NOT NULL,
                horizon_hours INTEGER NOT NULL,
                target_time TEXT NOT NULL,
                forecast_time TEXT NOT NULL,
                forecast_offset_minutes REAL,
                temperature_c REAL,
                humidity_pct REAL,
                precipitation_probability_pct REAL,
                precipitation_mm REAL,
                wind_speed_kmh REAL,
                fetched_at TEXT NOT NULL,
                UNIQUE(city, fetched_at, horizon_hours)
            )
        """)

        conn.executemany("""
            INSERT INTO weather_horizon_outlook (
                city, reference_time, horizon_hours, target_time,
                forecast_time, forecast_offset_minutes, temperature_c,
                humidity_pct, precipitation_probability_pct,
                precipitation_mm, wind_speed_kmh, fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city, fetched_at, horizon_hours) DO NOTHING
        """, outlook.itertuples(index=False, name=None))

    print("\nWEATHER OUTLOOK REPORT")
    print("----------------------")
    print(f"Reference time: {reference_time}")
    print(f"Cities: {outlook['city'].nunique()}")
    print(f"Outlook records: {len(outlook)}")
    print(f"CSV saved: {output_file}")
    print("\nOUTLOOK:")
    print(outlook[[
        "city", "horizon_hours", "target_time",
        "forecast_time", "temperature_c",
        "precipitation_probability_pct", "wind_speed_kmh"
    ]].to_string(index=False))


if __name__ == "__main__":
    main()