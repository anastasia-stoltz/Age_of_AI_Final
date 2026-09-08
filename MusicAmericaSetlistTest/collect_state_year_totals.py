"""
Collect documented live-performance totals by U.S. state and year
from Setlist.fm for the Music Across America choropleth.

Method:
1. Query Setlist.fm once for each state/year.
2. If the reported annual total is below the 10,000-result ceiling,
   use that total directly.
3. If the annual total reaches the 10,000 ceiling, query the state
   one day at a time and sum the daily totals.
4. Save every completed state/year immediately to CSV so the script
   can resume without repeating finished work.

Output:
MusicAmericaSetlistTest/state_year_live_music_totals.csv
"""

import os
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# --------------------------------------------------
# PATHS
# --------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ASSIGNMENT_DIR = REPO_ROOT.parent

PRIVATE_ENV_PATH = (
    ASSIGNMENT_DIR
    / "soundofmusic"
    / ".env"
)

OUTPUT_FILE = (
    SCRIPT_DIR
    / "state_year_live_music_totals.csv"
)


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

if PRIVATE_ENV_PATH.exists():
    load_dotenv(
        PRIVATE_ENV_PATH,
        override=False
    )


SETLISTFM_API_KEY = os.getenv(
    "SETLISTFM_API_KEY"
)

if not SETLISTFM_API_KEY:
    raise ValueError(
        "SETLISTFM_API_KEY not found."
    )


# --------------------------------------------------
# SETLIST.FM SETTINGS
# --------------------------------------------------

SETLIST_URL = (
    "https://api.setlist.fm/rest/1.0/search/setlists"
)

HEADERS = {
    "Accept": "application/json",
    "x-api-key": SETLISTFM_API_KEY
}

RESULT_CAP = 10000

REQUEST_DELAY = 0.6


# --------------------------------------------------
# YEARS
# --------------------------------------------------

TARGET_YEARS = [
    2022,
    2023,
    2024,
    2025,
    2026
]


# --------------------------------------------------
# STATES
# --------------------------------------------------

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
    "Wyoming": "WY",
}


# --------------------------------------------------
# REQUEST SESSION
# --------------------------------------------------

def make_session():

    session = requests.Session()

    retry = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504
        ],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session.mount(
        "https://",
        adapter
    )

    return session


session = make_session()


# --------------------------------------------------
# API REQUEST
# --------------------------------------------------

def get_total(params):
    """
    Return the Setlist.fm total for one query.
    """

    response = session.get(
        SETLIST_URL,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    time.sleep(
        REQUEST_DELAY
    )

    return int(
        data.get(
            "total",
            0
        )
    )


# --------------------------------------------------
# ANNUAL TOTAL
# --------------------------------------------------

def get_annual_total(
    state_code,
    year
):
    """
    Ask Setlist.fm for the annual total for one state.
    """

    params = {
        "countryCode": "US",
        "stateCode": state_code,
        "year": year,
        "p": 1
    }

    return get_total(
        params
    )


# --------------------------------------------------
# DAILY FALLBACK
# --------------------------------------------------

def get_daily_sum(
    state_code,
    year
):
    """
    Sum daily Setlist.fm totals for a state/year.

    This is used only when the annual query reaches
    the 10,000-result ceiling.
    """

    start_date = date(
        year,
        1,
        1
    )

    end_date = date(
        year,
        12,
        31
    )

    # For the current year, do not waste API calls
    # requesting future dates.
    today = date.today()

    if year == today.year:
        end_date = today

    current_date = start_date

    annual_sum = 0
    days_checked = 0

    print(
        f"      Daily fallback: "
        f"{state_code} {year}"
    )

    while current_date <= end_date:

        params = {
            "countryCode": "US",
            "stateCode": state_code,

            # Setlist.fm date format:
            # dd-MM-yyyy
            "date": current_date.strftime(
                "%d-%m-%Y"
            ),

            "p": 1
        }

        daily_total = get_total(
            params
        )

        annual_sum += (
            daily_total
        )

        days_checked += 1

        if days_checked % 30 == 0:

            print(
                f"        {days_checked} days checked "
                f"→ running total {annual_sum}"
            )

        current_date += timedelta(
            days=1
        )

    return (
        annual_sum,
        days_checked
    )


# --------------------------------------------------
# LOAD PREVIOUS RESULTS
# --------------------------------------------------

if OUTPUT_FILE.exists():

    results_df = pd.read_csv(
        OUTPUT_FILE
    )

    completed = {
        (
            int(row["year"]),
            row["state"]
        )
        for _, row
        in results_df.iterrows()
    }

    print(
        f"\nLoaded {len(completed)} "
        f"completed state/year totals."
    )

else:

    results_df = pd.DataFrame(
        columns=[
            "year",
            "state",
            "state_name",
            "event_count",
            "method",
            "annual_api_total",
            "daily_queries",
        ]
    )

    completed = set()


# --------------------------------------------------
# COLLECTION
# --------------------------------------------------

print("\n-----------------------------------")
print("STATE/YEAR LIVE MUSIC TOTALS")
print("-----------------------------------\n")


for year in TARGET_YEARS:

    print(
        f"\nYEAR {year}"
    )

    for state_name, state_code in STATES.items():

        key = (
            year,
            state_code
        )

        if key in completed:

            print(
                f"  {state_code}: already complete"
            )

            continue


        try:

            annual_total = get_annual_total(
                state_code,
                year
            )


            # ------------------------------------------
            # NORMAL ANNUAL QUERY
            # ------------------------------------------

            if annual_total < RESULT_CAP:

                final_total = (
                    annual_total
                )

                method = (
                    "annual"
                )

                daily_queries = 0

                print(
                    f"  {state_code}: "
                    f"{final_total:,} "
                    f"(annual)"
                )


            # ------------------------------------------
            # 10,000 CAP FALLBACK
            # ------------------------------------------

            else:

                print(
                    f"  {state_code}: "
                    f"annual total hit "
                    f"{RESULT_CAP:,} cap"
                )

                final_total, daily_queries = (
                    get_daily_sum(
                        state_code,
                        year
                    )
                )

                method = (
                    "daily_sum"
                )

                print(
                    f"  {state_code}: "
                    f"{final_total:,} "
                    f"(daily sum)"
                )


            # ------------------------------------------
            # SAVE RESULT
            # ------------------------------------------

            new_row = pd.DataFrame([
                {
                    "year": year,
                    "state": state_code,
                    "state_name": state_name,
                    "event_count": final_total,
                    "method": method,
                    "annual_api_total": annual_total,
                    "daily_queries": daily_queries,
                }
            ])


            results_df = pd.concat(
                [
                    results_df,
                    new_row
                ],
                ignore_index=True
            )


            results_df = (
                results_df
                .sort_values(
                    [
                        "year",
                        "state"
                    ]
                )
                .reset_index(
                    drop=True
                )
            )


            # Save after EVERY completed state/year.
            results_df.to_csv(
                OUTPUT_FILE,
                index=False
            )


            completed.add(
                key
            )


        except requests.RequestException as error:

            print(
                f"  {state_code}: ERROR "
                f"{error}"
            )


# --------------------------------------------------
# FINAL SUMMARY
# --------------------------------------------------

print("\n-----------------------------------")
print("COLLECTION COMPLETE")
print("-----------------------------------")

print(
    f"State/year rows: "
    f"{len(results_df)}"
)

print(
    f"\nMethods used:"
)

print(
    results_df[
        "method"
    ].value_counts()
)

print(
    f"\nSaved to:"
)

print(
    OUTPUT_FILE
)


print(
    "\nLargest state/year totals:"
)

print(
    results_df
    .sort_values(
        "event_count",
        ascending=False
    )
    .head(15)[
        [
            "year",
            "state",
            "event_count",
            "method"
        ]
    ]
    .to_string(
        index=False
    )
)