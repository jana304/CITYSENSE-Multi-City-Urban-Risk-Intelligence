
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Six cities
CITIES = {
    "Chennai": {"latitude": 13.0827, "longitude": 80.2707},
    "Bengaluru": {"latitude": 12.9716, "longitude": 77.5946},
    "Hyderabad": {"latitude": 17.3850, "longitude": 78.4867},
    "Mumbai": {"latitude": 19.0760, "longitude": 72.8777},
    "Delhi": {"latitude": 28.6139, "longitude": 77.2090},
    "Kolkata": {"latitude": 22.5726, "longitude": 88.3639},
}

API_URL = "https://api.open-meteo.com/v1/forecast"
records = []

# One collection timestamp for this refresh
fetched_at = datetime.now().astimezone().isoformat(
    timespec="seconds"
)

for city, location in CITIES.items():
    params = {
        **location,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation_probability,"
            "precipitation,"
            "wind_speed_10m"
        ),
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        if not times:
            print(f"FAILED: {city} - No hourly forecast returned")
            continue

        for i, forecast_time in enumerate(times):
            records.append({
                "city": city,
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "forecast_time": forecast_time,
                "fetched_at": fetched_at,
                "temperature_c": hourly["temperature_2m"][i],
                "humidity_pct": hourly["relative_humidity_2m"][i],
                "precipitation_probability_pct":
                    hourly["precipitation_probability"][i],
                "precipitation_mm": hourly["precipitation"][i],
                "wind_speed_kmh": hourly["wind_speed_10m"][i],
            })

        print(f"SUCCESS: {city} - {len(times)} hourly forecasts")

    except (requests.RequestException, ValueError, KeyError, IndexError) as error:
        print(f"FAILED: {city} - {error}")

if records:
    df = pd.DataFrame(records)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / (
        f"weather_hourly_forecast_{timestamp}.csv"
    )

    df.to_csv(output_file, index=False)

    print("\nHOURLY FORECAST COLLECTION REPORT")
    print("---------------------------------")
    print(f"Cities collected: {df['city'].nunique()}")
    print(f"Total forecast records: {len(df)}")
    print(f"Missing values: {df.isna().sum().sum()}")
    print(f"Output file: {output_file}")

    print("\nForecast records by city:")
    print(df.groupby("city").size().to_string())

    print("\nSample forecast records:")
    print(
        df[
            [
                "city",
                "forecast_time",
                "temperature_c",
                "precipitation_probability_pct",
                "wind_speed_kmh",
            ]
        ].head(12).to_string(index=False)
    )
else:
    print("No hourly forecast data was collected.")