"""
Data collection script for Music Across America.

Uses the Ticketmaster Discovery API for both concert location AND genre —
Ticketmaster's own classification system (segment -> genre -> subGenre)
tags each event directly, so no second genre-lookup API is needed.

Run this on its own (e.g. `python collect_data.py`) to build/refresh
concert_map_data.csv. The dashboard page just reads that CSV — it should
NOT be re-scraping the API every time someone loads the page.
"""

import os
import time
from datetime import datetime, timedelta

import requests
import pandas as pd
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Reads variables from a .env file in the current directory into os.environ.
load_dotenv()

# --- Config -------------------------------------------------------------
# Never hardcode API keys in source. Put this in a .env file next to this
# script (and make sure .env is in your .gitignore):
#   TICKETMASTER_API_KEY=your-key-here
TICKETMASTER_API_KEY = os.environ.get("TICKETMASTER_API_KEY", "")
if not TICKETMASTER_API_KEY:
    raise RuntimeError(
        "Set the TICKETMASTER_API_KEY environment variable before running this script "
        "(get one free at https://developer.ticketmaster.com/)."
    )

EVENTS_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

# Ticketmaster's "music" classification occasionally includes non-musical
# categories (rodeo, motorsports, etc. get lumped in under some events).
# These get dropped entirely rather than treated as a genre.
NON_MUSIC_GENRES = {"rodeo", "motorsports/racing", "wrestling", "fairs & festivals"}

# Generic/catch-all labels Ticketmaster uses when an event isn't classified
# more specifically. These are kept (they're still real music events) but
# bucketed together instead of showing up as their own confusing "genres".
GENERIC_GENRES = {"music", "other", "undefined", "unknown"}


# A shared session with automatic retries handles transient connection
# resets/timeouts much better than a bare requests.get() per call.
def _make_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.5,  # waits ~1.5s, 3s, 6s between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_session = _make_session()


def _clean_genre(raw_genre):
    """Return a cleaned genre label, or None if this event should be dropped."""
    genre = (raw_genre or "unknown").lower().strip()
    if genre in NON_MUSIC_GENRES:
        return None
    if genre in GENERIC_GENRES:
        return "other/unclassified"
    return genre


def collect_events(start_date=None, end_date=None, max_pages=5, page_size=200):
    """
    Pull raw US music events from Ticketmaster within an optional date window.

    Returns one row per event (not yet deduplicated or aggregated), including
    the artist and venue identifiers needed later to collapse residencies
    (an artist playing the same venue repeatedly within a short span).

    start_date / end_date: datetime objects (UTC). If omitted, Ticketmaster
    defaults to "from now onward" with no upper bound.

    Note: Ticketmaster's Discovery API only supports paging up to the 1000th
    result per query (page * page_size < 1000). To pull more than that in
    total, call this multiple times with different date windows — see
    collect_across_date_ranges below — rather than just raising max_pages.
    """
    rows = []

    base_params = {
        "apikey": TICKETMASTER_API_KEY,
        "countryCode": "US",
        "classificationName": "music",
        "size": page_size,
    }
    if start_date:
        base_params["startDateTime"] = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    if end_date:
        base_params["endDateTime"] = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    for page in range(max_pages):  # Ticketmaster pages are 0-indexed
        params = {**base_params, "page": page}
        response = _session.get(EVENTS_URL, params=params, timeout=10)
        time.sleep(0.25)  # stay comfortably under 5 requests/sec

        if response.status_code != 200:
            print(f"Failed to fetch page {page}: {response.status_code} {response.text[:200]}")
            continue

        events = response.json().get("_embedded", {}).get("events", [])
        if not events:
            break  # no more results in this window

        for event in events:
            local_date = event.get("dates", {}).get("start", {}).get("localDate", "")
            if not local_date or len(local_date) < 7:
                continue
            year = local_date[:4]
            month = local_date[5:7]  # format: YYYY-MM-DD

            venues = event.get("_embedded", {}).get("venues", []) or []
            if not venues:
                continue
            state = venues[0].get("state", {}).get("stateCode", "")
            if not state or len(state) != 2:
                continue
            venue_id = venues[0].get("id", "")

            classifications = event.get("classifications", []) or []
            raw_genre = None
            for c in classifications:
                if c.get("primary") and c.get("genre", {}).get("name"):
                    raw_genre = c["genre"]["name"]
                    break

            genre = _clean_genre(raw_genre)
            if genre is None:
                continue  # dropped: non-music category (rodeo, wrestling, etc.)

            attractions = event.get("_embedded", {}).get("attractions", []) or []
            artist_id = attractions[0].get("id", "") if attractions else ""

            rows.append({
                "event_id": event.get("id", ""),
                "artist_id": artist_id,
                "venue_id": venue_id,
                "year": int(year),
                "month": month,
                "state": state.upper(),
                "genre": genre,
            })

    return pd.DataFrame(rows)


def collect_across_date_ranges(months_ahead=24, window_months=3, max_pages=3, page_size=200):
    """
    Split the lookup window into consecutive chunks (default: 3-month
    windows spanning the next 24 months) and collect each separately.

    Ticketmaster only lists on-sale/upcoming events — there's no history to
    pull. But a single unbounded query would also hit the 1000-result paging
    cap almost immediately, since it's dominated by whatever's on sale in
    the next few weeks. Querying window-by-window spreads that 1000-result
    budget across the whole time span instead of burning it all up front.
    """
    all_frames = []
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    months_covered = 0
    while months_covered < months_ahead:
        start = today + timedelta(days=30 * months_covered)
        end = today + timedelta(days=30 * (months_covered + window_months))
        print(f"Collecting {start.date()} to {end.date()}...")
        chunk_df = collect_events(
            start_date=start, end_date=end, max_pages=max_pages, page_size=page_size
        )
        print(f"  -> {len(chunk_df)} raw events")
        all_frames.append(chunk_df)
        months_covered += window_months

    if not all_frames:
        return pd.DataFrame(columns=["event_id", "artist_id", "venue_id", "year", "month", "state", "genre"])
    return pd.concat(all_frames, ignore_index=True)


def dedupe_residencies(raw_df):
    """
    Collapse repeated dates from the same artist at the same venue within
    the same month into a single "engagement" — e.g. a 15-night Las Vegas
    residency counts once, not 15 times, so it doesn't dominate the map.

    Events without a recognized artist_id (festivals, multi-act bills, or
    anything Ticketmaster didn't tag with an attraction) are left as-is
    and never merged with each other, since we have no reliable way to
    tell whether they're actually the same act.
    """
    has_artist = raw_df["artist_id"] != ""
    with_artist = raw_df[has_artist].copy()
    without_artist = raw_df[~has_artist].copy()

    # One row per (artist, venue, month) -- repeats within that window collapse.
    with_artist_deduped = with_artist.drop_duplicates(
        subset=["artist_id", "venue_id", "year", "month"]
    )

    deduped = pd.concat([with_artist_deduped, without_artist], ignore_index=True)
    dropped = len(raw_df) - len(deduped)
    print(f"Deduplication: {len(raw_df)} raw events -> {len(deduped)} engagements "
          f"({dropped} residency repeats collapsed)")
    return deduped


if __name__ == "__main__":
    raw_df = collect_across_date_ranges(
        months_ahead=24, window_months=3, max_pages=3, page_size=200
    )
    deduped_df = dedupe_residencies(raw_df)
    df_grouped = (
        deduped_df.groupby(["year", "state", "genre"]).size().reset_index(name="event_count")
    )
    df_grouped.to_csv("concert_map_data.csv", index=False)
    print(f"Data collection complete! Saved {len(df_grouped)} rows to concert_map_data.csv")