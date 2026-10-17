
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "citysense.db"
OUTPUT_DIR = (
    PROJECT_DIR
    / "05_air_quality_intelligence"
    / "data"
    / "processed"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    with sqlite3.connect(DB_PATH) as conn:
        latest_batch = pd.read_sql_query("""
            SELECT MAX(fetched_at) AS latest_fetched_at
            FROM air_quality_forecasts
        """, conn).iloc[0]["latest_fetched_at"]

        if pd.isna(latest_batch):
            print("ERROR: No air-quality forecasts found.")
            return

        forecasts = pd.read_sql_query("""
            SELECT city, latitude, longitude, forecast_time,
                   fetched_at, us_aqi, pm2_5_ug_m3, pm10_ug_m3
            FROM air_quality_forecasts
            WHERE fetched_at = ?
        """, conn, params=(latest_batch,))

    if forecasts.empty:
        print("ERROR: The latest forecast batch is empty.")
        return

    forecasts["forecast_time"] = pd.to_datetime(
        forecasts["forecast_time"], errors="coerce"
    )
    forecasts = forecasts.dropna(subset=["forecast_time"])

    # API timestamps and reference time use India Standard Time.
    reference_time = pd.to_datetime(
        latest_batch, utc=True
    ).tz_convert("Asia/Kolkata").tz_localize(None)

    results = []

    for city, city_data in forecasts.groupby("city"):
        city_data = city_data.sort_values("forecast_time")

        for horizon in [5, 10]:
            target_time = reference_time + pd.Timedelta(hours=horizon)

            differences = (
                city_data["forecast_time"] - target_time
            ).abs()

            best_index = differences.idxmin()
            selected = city_data.loc[best_index]
            offset_minutes = differences.loc[best_index].total_seconds() / 60

            if offset_minutes > 30:
                print(
                    f"WARNING: {city} +{horizon}h forecast is "
                    f"{offset_minutes:.0f} minutes from the target."
                )

            results.append({
                "city": city,
                "reference_time": reference_time.isoformat(),
                "horizon_hours": horizon,
                "target_time": target_time.isoformat(),
                "forecast_time": selected["forecast_time"].isoformat(),
                "forecast_offset_minutes": round(offset_minutes, 1),
                "us_aqi": selected["us_aqi"],
                "pm2_5_ug_m3": selected["pm2_5_ug_m3"],
                "pm10_ug_m3": selected["pm10_ug_m3"],
                "fetched_at": selected["fetched_at"],
            })

    outlook = pd.DataFrame(results)

    output_file = OUTPUT_DIR / "air_quality_horizon_outlook.csv"
    outlook.to_csv(output_file, index=False)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS air_quality_horizon_outlook (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                reference_time TEXT NOT NULL,
                horizon_hours INTEGER NOT NULL,
                target_time TEXT NOT NULL,
                forecast_time TEXT NOT NULL,
                forecast_offset_minutes REAL,
                us_aqi REAL,
                pm2_5_ug_m3 REAL,
                pm10_ug_m3 REAL,
                fetched_at TEXT NOT NULL,
                UNIQUE(city, fetched_at, horizon_hours)
            )
        """)

        conn.executemany("""
            INSERT INTO air_quality_horizon_outlook (
                city, reference_time, horizon_hours, target_time,
                forecast_time, forecast_offset_minutes, us_aqi,
                pm2_5_ug_m3, pm10_ug_m3, fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city, fetched_at, horizon_hours) DO NOTHING
        """, outlook[[
            "city", "reference_time", "horizon_hours", "target_time",
            "forecast_time", "forecast_offset_minutes", "us_aqi",
            "pm2_5_ug_m3", "pm10_ug_m3", "fetched_at"
        ]].itertuples(index=False, name=None))

    print("\nAIR QUALITY OUTLOOK REPORT")
    print("=" * 40)
    print(f"Cities covered: {outlook['city'].nunique()}")
    print(f"Outlook records: {len(outlook)}")
    print(f"CSV saved: {output_file}")

    print("\nOUTLOOK:")
    print(outlook[[
        "city", "horizon_hours", "forecast_time",
        "us_aqi", "pm2_5_ug_m3", "pm10_ug_m3",
        "forecast_offset_minutes"
    ]].to_string(index=False))


if __name__ == "__main__":
    main()