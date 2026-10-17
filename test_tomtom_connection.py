
import os
import requests
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()

api_key = os.getenv("TOMTOM_API_KEY")

if not api_key:
    print("ERROR: API key not found. Check your .env file.")
    raise SystemExit(1)

url = "https://api.tomtom.com/maps/orbis/traffic/incidents/details"

params = {
    "apiVersion": "2",
    "bbox": "80.15,12.95,80.35,13.20",
    "timeValidity": "present"
}

headers = {
    "TomTom-Api-Key": api_key,
    "TomTom-Api-Version": "2",
    "Attributes": "incidents(type,geometry(type,coordinates),properties(iconCategory))"
}

try:
    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30
    )

    print("HTTP Status:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        incidents = data.get("incidents", [])
        print("Connection successful!")
        print("Incidents returned:", len(incidents))

        if incidents:
            print("First incident fields:", list(incidents[0].keys()))
        else:
            print("No incidents returned for this area right now.")

    elif response.status_code == 204:
        print("Request succeeded, but no incidents were returned.")

    else:
        print("Response message:", response.text[:1000])

except requests.RequestException as error:
    print("Connection error:", error)