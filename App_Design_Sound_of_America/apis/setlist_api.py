import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("SETLISTFM_API_KEY")
API_URL = "https://api.setlist.fm/rest/1.0/search/setlists"


STATE_CODES = {
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
    "Wyoming": "WY",
}

STATE_NAMES = {
    code: state
    for state, code in STATE_CODES.items()
}

# These caches exist only while the app process is running.
# Nothing from Setlist.fm is written to disk by this module.
STATE_TOTAL_CACHE = {}
YEAR_TOTALS_CACHE = {}


def get_state_total(state_code, year):
    """Return the number of Setlist.fm records matching one state and year."""

    if not API_KEY:
        raise ValueError(
            "Setlist.fm API key not found. Add SETLISTFM_API_KEY to your .env file "
            "or to Render's Environment Variables."
        )

    cache_key = (state_code, int(year))

    if cache_key in STATE_TOTAL_CACHE:
        return STATE_TOTAL_CACHE[cache_key]

    headers = {
        "Accept": "application/json",
        "x-api-key": API_KEY,
    }

    params = {
        "countryCode": "US",
        "stateCode": state_code,
        "year": int(year),
        "p": 1,
    }

    response = requests.get(
        API_URL,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    total = int(data.get("total", 0))

    STATE_TOTAL_CACHE[cache_key] = total

    # Keep requests comfortably spaced apart.
    time.sleep(0.6)

    return total


def get_us_state_totals(year):
    """Return one row per state for the selected benchmark year."""

    year = int(year)

    if year in YEAR_TOTALS_CACHE:
        return YEAR_TOTALS_CACHE[year].copy()

    rows = []

    for state_name, state_code in STATE_CODES.items():

        try:
            total = get_state_total(state_code, year)

        except requests.RequestException:
            total = None

        rows.append({
            "State": state_name,
            "Code": state_code,
            "Setlists": total,
        })

    df = pd.DataFrame(rows)

    YEAR_TOTALS_CACHE[year] = df.copy()

    return df


def get_state_history(state_code, years):
    """Return one state's Setlist.fm totals across the benchmark years."""

    rows = []

    for year in years:

        try:
            total = get_state_total(state_code, year)

        except requests.RequestException:
            total = None

        rows.append({
            "Year": int(year),
            "Setlists": total,
        })

    return pd.DataFrame(rows)
