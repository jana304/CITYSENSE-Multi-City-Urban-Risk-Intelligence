import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


# --------------------------------------------------
# CITYSENSE AI - TRAFFIC INCIDENT COLLECTOR
# Data source: TomTom Traffic Incidents API
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = (
    PROJECT_DIR
    / "02_traffic_intelligence"
    / "data"
    / "raw"
)

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load API key from the root .env file
load_dotenv(PROJECT_DIR / ".env")

API_KEY = os.getenv("TOMTOM_API_KEY")

if not API_KEY:
    print("ERROR: TOMTOM_API_KEY was not found in the root .env file.")
    sys.exit(1)


# --------------------------------------------------
# CITY COORDINATES
# Bounding box format: minLon,minLat,maxLon,maxLat
# --------------------------------------------------

CITIES = {
    "Chennai": "80.15,12.95,80.35,13.20",
    "Bengaluru": "77.48,12.90,77.70,13.10",
    "Hyderabad": "78.35,17.30,78.55,17.50",
    "Mumbai": "72.80,18.90,73.00,19.20",
    "Delhi": "77.10,28.50,77.30,28.75",
    "Kolkata": "88.30,22.45,88.45,22.65",
}


# --------------------------------------------------
# API CONFIGURATION
# --------------------------------------------------

API_URL = (
    "https://api.tomtom.com/maps/orbis/"
    "traffic/incidents/details"
)

HEADERS = {
    "TomTom-Api-Key": API_KEY,
    "TomTom-Api-Version": "2",
    "Attributes": (
        "incidents("
        "type,"
        "geometry(type,coordinates),"
        "properties("
        "id,"
        "iconCategory,"
        "magnitudeOfDelay,"
        "startTime,"
        "endTime,"
        "from,"
        "to,"
        "lengthInMeters,"
        "delayInSeconds,"
        "roadNumbers,"
        "timeValidity,"
        "probabilityOfOccurrence,"
        "numberOfReports,"
        "lastReportTime"
        ")"
        ")"
    ),
}

COLUMNS = [
    "city",
    "fetched_at",
    "incident_id",
    "category",
    "magnitude_of_delay",
    "start_time",
    "end_time",
    "from_road",
    "to_road",
    "length_in_meters",
    "delay_in_seconds",
    "road_numbers",
    "time_validity",
    "probability_of_occurrence",
    "number_of_reports",
    "last_report_time",
    "geometry_type",
    "coordinates",
]


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def get_property(properties, *possible_names):
    """Return the first matching property name."""
    for name in possible_names:
        if name in properties:
            return properties[name]
    return None


def collect_city_incidents(city, bbox, fetched_at):
    """Collect current traffic incidents for one city."""

    params = {
        "apiVersion": "2",
        "bbox": bbox,
        "timeValidity": "present",
    }

    print(f"\nCollecting traffic incidents for {city}...")

    try:
        response = requests.get(
            API_URL,
            headers=HEADERS,
            params=params,
            timeout=60,
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as error:
        print(f"ERROR collecting {city}: {error}")
        return []

    incidents = data.get("incidents", [])

    if not isinstance(incidents, list):
        print(f"WARNING: Unexpected response format for {city}.")
        return []

    city_records = []

    for incident in incidents:
        properties = incident.get("properties") or {}
        geometry = incident.get("geometry") or {}

        category = get_property(
            properties, "iconCategory", "category"
        )

        coordinates = geometry.get("coordinates")

        # Convert list-valued fields to text for CSV compatibility.
        road_numbers = get_property(properties, "roadNumbers")
        if isinstance(road_numbers, (list, dict)):
            road_numbers = str(road_numbers)

        if isinstance(coordinates, (list, dict)):
            coordinates = str(coordinates)

        record = {
            "city": city,
            "fetched_at": fetched_at,
            "incident_id": get_property(
                properties, "id"
            ) or incident.get("id"),
            "category": category,
            "magnitude_of_delay": get_property(
                properties, "magnitudeOfDelay"
            ),
            "start_time": get_property(
                properties, "startTime"
            ),
            "end_time": get_property(
                properties, "endTime"
            ),
            "from_road": get_property(properties, "from"),
            "to_road": get_property(properties, "to"),
            "length_in_meters": get_property(
                properties, "lengthInMeters"
            ),
            "delay_in_seconds": get_property(
                properties, "delayInSeconds"
            ),
            "road_numbers": road_numbers,
            "time_validity": get_property(
                properties, "timeValidity"
            ),
            "probability_of_occurrence": get_property(
                properties, "probabilityOfOccurrence"
            ),
            "number_of_reports": get_property(
                properties, "numberOfReports"
            ),
            "last_report_time": get_property(
                properties, "lastReportTime"
            ),
            "geometry_type": geometry.get("type"),
            "coordinates": coordinates,
        }

        city_records.append(record)

    print(f"Incidents collected for {city}: {len(city_records)}")

    return city_records


# --------------------------------------------------
# MAIN COLLECTION PROCESS
# --------------------------------------------------

def main():
    fetched_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    all_records = []

    print("=" * 60)
    print("CITYSENSE AI - TRAFFIC INCIDENT COLLECTION")
    print(f"Collection time: {fetched_at}")
    print("=" * 60)

    for city, bbox in CITIES.items():
        records = collect_city_incidents(
            city, bbox, fetched_at
        )
        all_records.extend(records)

    if not all_records:
        print("\nNo incident records collected.")
        print("Check the API response, key permissions, and quota.")
        return

    df = pd.DataFrame(all_records, columns=COLUMNS)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = (
        RAW_DATA_DIR
        / f"traffic_incidents_{timestamp}.csv"
    )

    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)

    print(f"Total records: {len(df)}")
    print(f"Cities collected: {df['city'].nunique()}")
    print(f"Output file: {output_file}")

    print("\nRecords by city:")
    print(df.groupby("city").size().to_string())

    print("\nIncident categories:")
    print(
        df["category"]
        .fillna("Unknown")
        .value_counts()
        .to_string()
    )

    detail_columns = [
        "incident_id",
        "magnitude_of_delay",
        "delay_in_seconds",
        "from_road",
        "to_road",
    ]

    print("\nMissing-value check:")
    print(df[detail_columns].isna().sum().to_string())

    print("\nSample incident details:")
    print(
        df[
            [
                "city",
                "category",
                "incident_id",
                "magnitude_of_delay",
                "delay_in_seconds",
                "from_road",
                "to_road",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nTraffic incident collection completed.")


if __name__ == "__main__":
    main()
