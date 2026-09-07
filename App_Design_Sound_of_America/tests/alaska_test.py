import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SETLISTFM_API_KEY")

URL = "https://api.setlist.fm/rest/1.0/search/setlists"

HEADERS = {
    "Accept": "application/json",
    "x-api-key": API_KEY
}

params = {
    "countryCode": "US",
    "stateCode": "AK",
    "p": 1
}

for attempt in range(5):
    response = requests.get(
        URL,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    print("Attempt", attempt + 1, "Status:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        print("Alaska total:", data.get("total", 0))
        break

    if response.status_code == 429:
        print("Rate limited. Waiting 5 seconds...")
        time.sleep(5)