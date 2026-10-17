
import os
import requests
from dotenv import load_dotenv
from collections import Counter

load_dotenv()
api_key = os.getenv("TOMTOM_API_KEY")

if not api_key:
    raise SystemExit("API key not found in .env")

url = "https://api.tomtom.com/maps/orbis/traffic/incidents/details"

params = {
    "apiVersion": "2",
    "bbox": "80.15,12.95,80.35,13.20",
    "timeValidity": "present"
}

headers = {
    "TomTom-Api-Key": api_key,
    "TomTom-Api-Version": "2",
    "Attributes": (
        "incidents(type,geometry(type,coordinates),"
        "properties(iconCategory))"
    )
}

response = requests.get(
    url, params=params, headers=headers, timeout=30
)

if response.status_code != 200:
    print("HTTP Status:", response.status_code)
    print(response.text[:1000])
    raise SystemExit(1)

data = response.json()
incidents = data.get("incidents", [])

print("Total incident records:", len(incidents))

categories = Counter()
for incident in incidents:
    properties = incident.get("properties", {})
    category = properties.get("iconCategory", "Unknown")
    categories[category] += 1

print("\nIncident categories:")
for category, count in categories.most_common():
    print(f"{category}: {count}")

if incidents:
    print("\nFirst incident sample:")
    print("Type:", incidents[0].get("type"))
    print("Properties:", incidents[0].get("properties"))
    print("Geometry type:",
          incidents[0].get("geometry", {}).get("type"))