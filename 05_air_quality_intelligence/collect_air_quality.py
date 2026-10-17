
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

# Project and scope folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
SCOPE_DIR = PROJECT_DIR / "05_air_quality_intelligence"
RAW_DIR = SCOPE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Six initial cities for CITYSENSE AI
CITIES = {
    "Chennai": (13.0827, 80.2707),
    "Bengaluru": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "Kolkata": (22.5726, 88.3639),
}

IST = ZoneInfo("Asia/Kolkata")


def collect_city_data(city, latitude, longitude, fetched_at):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "us_aqi,pm2_5,pm10",
        "hourly": "us_aqi,pm2_5,pm10",
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Current model-based air-quality estimate
    current = data.get("current", {})

    snapshot = {
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
        "current_time": current.get("time"),
        "fetched_at": fetched_at,
        "us_aqi": current.get("us_aqi"),
        "pm2_5_ug_m3": current.get("pm2_5"),
        "pm10_ug_m3": current.get("pm10"),
    }

    # Hourly forecast
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    forecasts = []

    for index, forecast_time in enumerate(times):
        forecasts.append({
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "forecast_time": forecast_time,
            "fetched_at": fetched_at,
            "us_aqi": (
                hourly["us_aqi"][index]
                if hourly.get("us_aqi") else None
            ),
            "pm2_5_ug_m3": (
                hourly["pm2_5"][index]
                if hourly.get("pm2_5") else None
            ),
            "pm10_ug_m3": (
                hourly["pm10"][index]
                if hourly.get("pm10") else None
            ),
        })

    return snapshot, forecasts


def main():
    fetched_at = datetime.now(IST).isoformat(timespec="seconds")

    snapshots = []
    all_forecasts = []
    failed_cities = []

    print("CITYSENSE AI - AIR QUALITY COLLECTION")
    print("=" * 45)

    for city, coordinates in CITIES.items():
        latitude, longitude = coordinates

        try:
            snapshot, forecasts = collect_city_data(
                city, latitude, longitude, fetched_at
            )

            snapshots.append(snapshot)
            all_forecasts.extend(forecasts)

            print(
                f"{city}: collected current estimate "
                f"and {len(forecasts)} hourly forecast records"
            )

        except (requests.RequestException, ValueError, KeyError) as error:
            failed_cities.append(city)
            print(f"{city}: collection failed - {error}")

    timestamp = datetime.now(IST).strftime("%Y%m%d_%H%M%S")

    if snapshots:
        snapshot_file = RAW_DIR / f"air_quality_snapshot_{timestamp}.csv"
        pd.DataFrame(snapshots).to_csv(snapshot_file, index=False)
        print(f"\nSnapshot saved: {snapshot_file}")

    if all_forecasts:
        forecast_file = RAW_DIR / f"air_quality_hourly_forecast_{timestamp}.csv"
        pd.DataFrame(all_forecasts).to_csv(forecast_file, index=False)
        print(f"Hourly forecast saved: {forecast_file}")

    print("\nCOLLECTION SUMMARY")
    print("-" * 30)
    print(f"Cities requested: {len(CITIES)}")
    print(f"Cities successful: {len(snapshots)}")
    print(f"Cities failed: {len(failed_cities)}")
    print(f"Hourly forecast records: {len(all_forecasts)}")

    if failed_cities:
        print("Failed cities:", ", ".join(failed_cities))

    print("\nNote: API results are model-based estimates/forecasts,")
    print("not guaranteed ground-monitoring-station measurements.")


if __name__ == "__main__":
    main()