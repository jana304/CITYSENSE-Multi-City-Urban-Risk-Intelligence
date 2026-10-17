
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "database" / "citysense.db"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configurable project screening rules.
# These are project rules, not official government warning thresholds.
HEAVY_RAIN_MM = 7.5
HIGH_RAIN_PROBABILITY_PCT = 70
STRONG_WIND_KMH = 40
HIGH_TEMPERATURE_C = 38
MEDIUM_TEMPERATURE_C = 35

# Separate heat-and-humidity monitoring indicator.
HEAT_HUMIDITY_TEMPERATURE_C = 35
HEAT_HUMIDITY_PERCENT = 70


def assess_weather_risk(row):
    reasons = []
    actions = []
    score = 0

    rain = row["precipitation_mm"]
    rain_probability = row["precipitation_probability_pct"]
    wind = row["wind_speed_kmh"]
    temperature = row["temperature_c"]
    humidity = row["humidity_pct"]

    if pd.notna(rain) and rain >= HEAVY_RAIN_MM:
        score += 2
        reasons.append("High forecast rainfall")
        actions.append("Check local rain and waterlogging advisories")

    if (
        pd.notna(rain_probability)
        and rain_probability >= HIGH_RAIN_PROBABILITY_PCT
    ):
        score += 1
        reasons.append("High probability of precipitation")
        actions.append("Allow extra time for outdoor travel")

    if pd.notna(wind) and wind >= STRONG_WIND_KMH:
        score += 2
        reasons.append("Strong forecast winds")
        actions.append("Use caution in exposed outdoor areas")

    if pd.notna(temperature) and temperature >= HIGH_TEMPERATURE_C:
        score += 2
        reasons.append("Very high forecast temperature")
        actions.append("Stay hydrated and limit heat exposure")

    elif (
        pd.notna(temperature)
        and temperature >= MEDIUM_TEMPERATURE_C
    ):
        score += 1
        reasons.append("Elevated forecast temperature")
        actions.append("Stay hydrated during outdoor activities")

    heat_humidity_flag = (
        pd.notna(temperature)
        and pd.notna(humidity)
        and temperature >= HEAT_HUMIDITY_TEMPERATURE_C
        and humidity >= HEAT_HUMIDITY_PERCENT
    )

    if heat_humidity_flag:
        actions.append(
            "Review heat and humidity conditions before outdoor activities"
        )

    if score >= 2:
        risk_level = "HIGH"
    elif score == 1:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if not reasons:
        reasons.append(
            "No configured weather-risk thresholds were triggered"
        )

    if not actions:
        actions.append("Continue monitoring updated forecasts")

    return pd.Series({
        "weather_risk_score": score,
        "heat_humidity_flag": heat_humidity_flag,
        "weather_risk_level": risk_level,
        "risk_reasons": "; ".join(reasons),
        "recommended_actions": "; ".join(dict.fromkeys(actions)),
    })


def main():
    with sqlite3.connect(DB_PATH) as conn:
        outlook = pd.read_sql_query(
            """
            SELECT
                city,
                reference_time,
                horizon_hours,
                target_time,
                forecast_time,
                forecast_offset_minutes,
                temperature_c,
                humidity_pct,
                precipitation_probability_pct,
                precipitation_mm,
                wind_speed_kmh,
                fetched_at
            FROM weather_horizon_outlook AS w
            WHERE fetched_at = (
                SELECT MAX(w2.fetched_at)
                FROM weather_horizon_outlook AS w2
                WHERE w2.city = w.city
            )
            ORDER BY city, horizon_hours
            """,
            conn,
        )

    if outlook.empty:
        print("ERROR: No weather outlook records found.")
        print("Run create_weather_outlook.py first.")
        return

    risk_columns = outlook.apply(assess_weather_risk, axis=1)
    outlook = pd.concat([outlook, risk_columns], axis=1)

    output_file = OUTPUT_DIR / "weather_risk_assessments.csv"
    outlook.to_csv(output_file, index=False, encoding="utf-8")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_risk_assessments (
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
                weather_risk_score INTEGER NOT NULL,
                weather_risk_level TEXT NOT NULL,
                risk_reasons TEXT NOT NULL,
                recommended_actions TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                UNIQUE(city, fetched_at, horizon_hours)
            )
        """)

        conn.executemany("""
            INSERT INTO weather_risk_assessments (
                city,
                reference_time,
                horizon_hours,
                target_time,
                forecast_time,
                forecast_offset_minutes,
                temperature_c,
                humidity_pct,
                precipitation_probability_pct,
                precipitation_mm,
                wind_speed_kmh,
                weather_risk_score,
                weather_risk_level,
                risk_reasons,
                recommended_actions,
                fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(city, fetched_at, horizon_hours) DO NOTHING
        """, outlook[[
            "city",
            "reference_time",
            "horizon_hours",
            "target_time",
            "forecast_time",
            "forecast_offset_minutes",
            "temperature_c",
            "humidity_pct",
            "precipitation_probability_pct",
            "precipitation_mm",
            "wind_speed_kmh",
            "weather_risk_score",
            "weather_risk_level",
            "risk_reasons",
            "recommended_actions",
            "fetched_at",
        ]].itertuples(index=False, name=None))

    print("\nCITYSENSE AI - WEATHER RISK REPORT")
    print("=" * 45)
    print(f"Cities covered: {outlook['city'].nunique()}")
    print(f"Risk assessments: {len(outlook)}")
    print(f"CSV saved: {output_file}")

    print("\nRISK LEVEL COUNTS:")
    print(outlook["weather_risk_level"].value_counts().to_string())

    print("\nHEAT AND HUMIDITY FLAG COUNTS:")
    print(outlook["heat_humidity_flag"].value_counts().to_string())

    print("\nASSESSMENTS:")
    print(outlook[[
        "city",
        "horizon_hours",
        "temperature_c",
        "humidity_pct",
        "precipitation_mm",
        "precipitation_probability_pct",
        "wind_speed_kmh",
        "weather_risk_score",
        "weather_risk_level",
        "heat_humidity_flag",
        "risk_reasons",
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
