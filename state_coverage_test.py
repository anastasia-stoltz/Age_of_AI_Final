import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SETLISTFM_API_KEY")

if not API_KEY:
    raise ValueError("SETLIST_API_KEY was not found in your .env file.")

URL = "https://api.setlist.fm/rest/1.0/search/setlists"

HEADERS = {
    "Accept": "application/json",
    "X-Api-Key": API_KEY
}

# All 50 U.S. states
STATES = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY"
}


results = []

for state_name, state_code in STATES.items():

    params = {
        "countryCode": "US",
        "stateCode": state_code,
        "p": 1
    }

    response = requests.get(
        URL,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()

        total = data.get("total", 0)

        results.append({
            "state": state_name,
            "state_code": state_code,
            "total": total
        })

        print(f"{state_name:<15} {state_code}  ✓  {total:,}")

    else:
        print(
            f"{state_name:<15} {state_code}  ERROR {response.status_code}"
        )

    # Stay comfortably under the 2 requests/second limit
    time.sleep(0.6)


print("\n-----------------------------")
print("COVERAGE SUMMARY")
print("-----------------------------")

states_with_data = [
    row for row in results
    if row["total"] > 0
]

states_without_data = [
    row for row in results
    if row["total"] == 0
]

print(f"States tested: {len(results)}")
print(f"States with data: {len(states_with_data)}")
print(f"States without data: {len(states_without_data)}")

if states_without_data:
    print("\nStates with no records:")

    for row in states_without_data:
        print(row["state"])

tested_states = {row["state"] for row in results}

missing_states = [
    state_name
    for state_name in STATES
    if state_name not in tested_states
]

print("\nStates not successfully tested:")
for state in missing_states:
    print(state)