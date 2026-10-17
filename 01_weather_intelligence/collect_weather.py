
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Initial cities for testing
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

for city, location in CITIES.items():
    params = {
        **location,
        "current": (
            "temperature_2m,relative_humidity_2m,"
            "precipitation,wind_speed_10m"
        ),
        "hourly": (
            "temperature_2m,precipitation_probability,"
            "precipitation,wind_speed_10m"
        ),
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }

    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        records.append({
            "city": city,
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "observed_time": current.get("time"),
            "fetched_at": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "temperature_c": current.get("temperature_2m"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
        })

        print(f"SUCCESS: {city}")

    except (requests.RequestException, ValueError) as error:
        print(f"FAILED: {city} - {error}")

if records:
    df = pd.DataFrame(records)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"weather_snapshot_{timestamp}.csv"
    df.to_csv(output_file, index=False)

    print("\nCollection summary")
    print("------------------")
    print(f"Cities collected: {len(df)}")
    print(f"Output file: {output_file}")
    print(df[["city", "temperature_c", "humidity_pct"]].to_string(index=False))
else:
    print("No city data was collected. No CSV file was created.")