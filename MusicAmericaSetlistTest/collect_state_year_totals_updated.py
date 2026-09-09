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

# Setlist.fm throttles sustained request bursts. Keep normal calls slow even
# when the HTTP retry adapter is not active.
REQUEST_DELAY = 2.0


# --------------------------------------------------
# YEARS
# --------------------------------------------------

TARGET_YEARS = [
    1985,
    1990,
    1995,
    2000,
    2005,
    2010,
    2015,
    2020,
    2022,
    2023,
    2024,
    2025,
    2026,
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
        total=6,
        backoff_factor=3,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504
        ],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
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

def get_total(params, request_label="API request"):
    """
    Return the Setlist.fm total for one query.

    Prints status before and after the request so
    a slow or rate-limited request is visible.
    """

    print(
        f"        → Sending {request_label}...",
        flush=True
    )

    try:

        response = session.get(
            SETLIST_URL,
            headers=HEADERS,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        total = int(
            data.get(
                "total",
                0
            )
        )

        print(
            f"        ✓ {request_label} returned "
            f"{total:,}",
            flush=True
        )

        return total

    except requests.RequestException as error:

        print(
            f"        ✗ {request_label} failed "
            f"after retries.",
            flush=True
        )

        print(
            f"          {error}",
            flush=True
        )

        raise

    finally:

        time.sleep(
            REQUEST_DELAY
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
        params,
        request_label=(
            f"annual request for "
            f"{state_code} {year}"
        )
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

    Used only after the annual request successfully
    returns the 10,000-result ceiling.
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

    # For the current year, do not request future dates.
    today = date.today()

    if year == today.year:
        end_date = today

    current_date = start_date
    annual_sum = 0
    days_checked = 0

    total_days = (
        end_date - start_date
    ).days + 1

    print(
        f"      DAILY FALLBACK STARTED: "
        f"{state_code} {year}",
        flush=True
    )

    print(
        f"      Need to check "
        f"{total_days} individual dates.",
        flush=True
    )

    while current_date <= end_date:

        params = {
            "countryCode": "US",
            "stateCode": state_code,
            "date": current_date.strftime(
                "%d-%m-%Y"
            ),
            "p": 1
        }

        # Tell us when each 10-day block begins.
        if days_checked % 10 == 0:

            print(
                f"        Working on day "
                f"{days_checked + 1} of {total_days} "
                f"({current_date})...",
                flush=True
            )

        daily_total = get_total(
            params,
            request_label=(
                f"{state_code} "
                f"{current_date}"
            )
        )

        annual_sum += daily_total
        days_checked += 1

        if (
            days_checked % 10 == 0
            or current_date == end_date
        ):

            percent = (
                days_checked
                / total_days
                * 100
            )

            print(
                f"        PROGRESS: "
                f"{days_checked}/{total_days} days "
                f"({percent:.0f}%) "
                f"→ running total "
                f"{annual_sum:,}",
                flush=True
            )

        current_date += timedelta(
            days=1
        )

    print(
        f"      DAILY FALLBACK COMPLETE: "
        f"{state_code} {year} "
        f"→ {annual_sum:,} total",
        flush=True
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


total_jobs = (
    len(TARGET_YEARS)
    * len(STATES)
)

target_keys = {
    (year, state_code)
    for year in TARGET_YEARS
    for state_code in STATES.values()
}


for year in TARGET_YEARS:

    print(
        f"\n=============================="
    )

    print(
        f"YEAR {year}"
    )

    print(
        f"=============================="
    )

    for state_name, state_code in STATES.items():

        key = (
            year,
            state_code
        )

        completed_target = (
            completed
            & target_keys
        )

        done_count = len(
            completed_target
        )

        percent_done = (
            done_count
            / total_jobs
            * 100
        )

        # ------------------------------------------
        # ALREADY COMPLETE
        # ------------------------------------------

        if key in completed:

            print(
                f"  [{done_count}/{total_jobs} "
                f"| {percent_done:.1f}%] "
                f"{state_code} {year}: "
                f"already complete"
            )

            continue


        # ------------------------------------------
        # NEW STATE/YEAR
        # ------------------------------------------

        print(
            f"\n  [{done_count}/{total_jobs} "
            f"| {percent_done:.1f}%] "
            f"Checking {state_code} {year}..."
        )

        try:

            annual_total = get_annual_total(
                state_code,
                year
            )

            print(
                f"      Annual API total: "
                f"{annual_total:,}"
            )


            # --------------------------------------
            # NORMAL ANNUAL QUERY
            # --------------------------------------

            if annual_total < RESULT_CAP:

                final_total = (
                    annual_total
                )

                method = (
                    "annual"
                )

                daily_queries = 0

                print(
                    f"      Accepted annual total: "
                    f"{final_total:,}"
                )


            # --------------------------------------
            # 10,000 CAP FALLBACK
            # --------------------------------------

            else:

                print(
                    f"      Annual total hit "
                    f"{RESULT_CAP:,} cap."
                )

                print(
                    f"      Switching to daily "
                    f"reconstruction..."
                )

                (
                    final_total,
                    daily_queries
                ) = get_daily_sum(
                    state_code,
                    year
                )

                method = (
                    "daily_sum"
                )

                print(
                    f"      Daily reconstruction "
                    f"complete: {final_total:,}"
                )


            # --------------------------------------
            # SAVE RESULT
            # --------------------------------------

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


            new_done_count = len(
                completed
                & target_keys
            )

            new_percent_done = (
                new_done_count
                / total_jobs
                * 100
            )

            print(
                f"      SAVED ✓ "
                f"{state_code} {year}"
            )

            print(
                f"      Overall progress: "
                f"{new_done_count}/{total_jobs} "
                f"({new_percent_done:.1f}%)"
            )


        except requests.RequestException as error:

            print(
                f"      ERROR: "
                f"{state_code} {year}"
            )

            print(
                f"      {error}"
            )

            print(
                "      This state/year was NOT saved. "
                "It will be retried next time."
            )


# --------------------------------------------------
# FINAL SUMMARY
# --------------------------------------------------

print("\n-----------------------------------")
expected_rows = len(TARGET_YEARS) * len(STATES)
target_keys = {
    (year, state_code)
    for year in TARGET_YEARS
    for state_code in STATES.values()
}
completed_target = completed & target_keys
is_complete = len(completed_target) == expected_rows

print("COLLECTION COMPLETE" if is_complete else "COLLECTION INCOMPLETE")
print("-----------------------------------")

print(
    f"State/year rows: "
    f"{len(completed_target)} of {expected_rows}"
)

if not is_complete:
    print("Run the script again later; completed rows will be skipped.")

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
