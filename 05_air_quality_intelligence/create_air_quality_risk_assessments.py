
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


def classify_us_aqi(value):
    if pd.isna(value):
        return "UNKNOWN", "AQI value unavailable"

    if value <= 50:
        return "GOOD", "Air quality is in the good US AQI range"
    elif value <= 100:
        return "MODERATE", "Air quality is in the moderate US AQI range"
    elif value <= 150:
        return (
            "UNHEALTHY FOR SENSITIVE GROUPS",
            "Sensitive groups may be more affected"
        )
    elif value <= 200:
        return "UNHEALTHY", "Air quality is in the unhealthy US AQI range"
    elif value <= 300:
        return (
            "VERY UNHEALTHY",
            "Air quality is in the very unhealthy US AQI range"
        )
    else:
        return "HAZARDOUS", "Air quality is in the hazardous US AQI range"


def main():
    with sqlite3.connect(DB_PATH) as conn:
        outlook = pd.read_sql_query("""
            SELECT city, reference_time, horizon_hours, target_time,
                   forecast_time, forecast_offset_minutes, us_aqi,
                   pm2_5_ug_m3, pm10_ug_m3, fetched_at
            FROM air_quality_horizon_outlook
            WHERE fetched_at = (
                SELECT MAX(fetched_at)
                FROM air_quality_horizon_outlook
            )
            ORDER BY city, horizon_hours
        """, conn)

    if outlook.empty:
        print("ERROR: No air-quality outlook found.")
        print("Run create_air_quality_outlook.py first.")
        return

    classifications = outlook["us_aqi"].apply(classify_us_aqi)

    outlook["air_quality_risk_level"] = classifications.apply(
        lambda result: result[0]
    )
    outlook["risk_explanation"] = classifications.apply(
        lambda result: result[1]
    )

    outlook["recommended_action"] = outlook[
        "air_quality_risk_level"
    ].map({
        "GOOD": "Continue normal activities and monitor conditions.",
        "MODERATE": (
            "Sensitive individuals should monitor symptoms and local advice."
        ),
        "UNHEALTHY FOR SENSITIVE GROUPS": (
            "Sensitive individuals should consider reducing prolonged "
            "or strenuous outdoor activity."
        ),
        "UNHEALTHY": (
            "Consider reducing prolonged or strenuous outdoor activity."
        ),
        "VERY UNHEALTHY": (
            "Limit outdoor exposure and follow local health guidance."
        ),
        "HAZARDOUS": (
            "Avoid outdoor exposure where possible and follow official "
            "health advisories."
        ),
        "UNKNOWN": "Check another reliable air-quality source.",
    })

    output_file = OUTPUT_DIR / "air_quality_risk_assessments.csv"
    outlook.to_csv(output_file, index=False)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS air_quality_risk_assessments (
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
                air_quality_risk_level TEXT NOT NULL,
                risk_explanation TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                UNIQUE(city, fetched_at, horizon_hours)
            )
        """)

        conn.executemany("""
            INSERT INTO air_quality_risk_assessments (
                city, reference_time, horizon_hours, target_time,
                forecast_time, forecast_offset_minutes, us_aqi,
                pm2_5_ug_m3, pm10_ug_m3, air_quality_risk_level,
                risk_explanation, recommended_action, fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city, fetched_at, horizon_hours) DO NOTHING
        """, outlook[[
            "city", "reference_time", "horizon_hours", "target_time",
            "forecast_time", "forecast_offset_minutes", "us_aqi",
            "pm2_5_ug_m3", "pm10_ug_m3", "air_quality_risk_level",
            "risk_explanation", "recommended_action", "fetched_at"
        ]].itertuples(index=False, name=None))

    print("\nAIR QUALITY RISK ASSESSMENT REPORT")
    print("=" * 45)
    print(f"Cities covered: {outlook['city'].nunique()}")
    print(f"Assessments: {len(outlook)}")
    print(f"CSV saved: {output_file}")

    print("\nRISK CATEGORY COUNTS:")
    print(outlook["air_quality_risk_level"].value_counts().to_string())

    print("\nASSESSMENTS:")
    print(outlook[[
        "city", "horizon_hours", "us_aqi",
        "air_quality_risk_level", "risk_explanation"
    ]].to_string(index=False))


if __name__ == "__main__":
    main()