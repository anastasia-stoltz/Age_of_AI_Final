"""
Data collection script for Music Across America — setlist.fm + MusicBrainz
version.

"""

import json
import os
import re
import time

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

SETLISTFM_API_KEY = os.getenv("SETLISTFM_API_KEY")
if not SETLISTFM_API_KEY:
    raise ValueError("SETLISTFM_API_KEY was not found in your .env file.")

SETLIST_URL = "https://api.setlist.fm/rest/1.0/search/setlists"
MUSICBRAINZ_ARTIST_URL = "https://musicbrainz.org/ws/2/artist/{mbid}"

SETLIST_HEADERS = {
    "Accept": "application/json",
    "x-api-key": SETLISTFM_API_KEY,
}
MB_HEADERS = {
    "User-Agent": "SoundOfAmericaProject/1.0 (stoltzana@gmail.com)"
}

# All 50 U.S. states, confirmed by Tracy's coverage test to all return data.
STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}

# Tags that are clearly not genres (contain digits, underscores, or are
# implausibly long/specific) get rejected rather than trusted as a genre
# when we fall back from MusicBrainz's formal `genres` field to `tags`.
_JUNK_TAG_PATTERN = re.compile(r"[\d_]")


def _make_session():
    """Session for setlist.fm -- more tolerant retries, since that API has
    been reliable so far and it's worth waiting out a brief hiccup."""
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _make_mb_session():
    """Session for MusicBrainz -- fails fast instead. If MusicBrainz is
    throttling/soft-blocking (e.g. after a large prior run), aggressive
    retries with long backoff just multiply a bad patch into an hours-long
    slowdown for no benefit -- a failed lookup already falls back to
    "unknown" regardless of how many times we retried it."""
    session = requests.Session()
    retry = Retry(
        total=1,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 504],  # note: 503 excluded, see below
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_session = _make_session()
_mb_session = _make_mb_session()

RAW_SETLISTS_CACHE = "raw_setlists_cache.csv"
GENRE_CACHE_FILE = "artist_genre_cache.json"

artist_genre_cache = {}


def _load_genre_cache():
    """Load previously completed MusicBrainz lookups from disk, if any --
    lets a later run pick up where an earlier crashed/interrupted one left
    off instead of re-querying artists we already have an answer for."""
    global artist_genre_cache
    if os.path.exists(GENRE_CACHE_FILE):
        with open(GENRE_CACHE_FILE, "r") as f:
            raw = json.load(f)
        # JSON stores our (genre, reason) tuples as lists -- convert back.
        artist_genre_cache = {k: tuple(v) for k, v in raw.items()}
        print(f"Loaded {len(artist_genre_cache)} cached genre lookups from {GENRE_CACHE_FILE}")


def _save_genre_cache():
    with open(GENRE_CACHE_FILE, "w") as f:
        json.dump(artist_genre_cache, f)


def collect_setlists_by_state(years, max_pages_per_state=1, page_delay=0.6):
    """
    Query setlist.fm once per state, per target year (not unfiltered
    paging), so both all 50 states AND real historical years are actually
    represented -- a plain "recent setlists" query only ever returns
    whatever was most recently logged, which skews toward the current year
    regardless of how many pages you pull.
    """
    all_records = []

    for year in years:
        for state_name, state_code in STATES.items():
            state_total = None

            for page in range(1, max_pages_per_state + 1):
                params = {
                    "countryCode": "US",
                    "stateCode": state_code,
                    "year": year,
                    "p": page,
                }
                response = _session.get(SETLIST_URL, headers=SETLIST_HEADERS, params=params, timeout=30)
                time.sleep(page_delay)  # stay comfortably under setlist.fm's rate limit

                if response.status_code != 200:
                    print(f"{year} {state_name} page {page}: error {response.status_code}")
                    continue

                data = response.json()
                state_total = data.get("total", 0)
                setlists = data.get("setlist", [])
                if not setlists:
                    break  # no more pages for this state/year

                for record in setlists:
                    artist = record.get("artist", {}) or {}
                    mbid = artist.get("mbid", "")
                    artist_name = artist.get("name", "")

                    all_records.append({
                        "year": year,
                        "state": state_code,
                        "mbid": mbid,
                        "artist_name": artist_name,
                    })

                if state_total is not None and page * 20 >= state_total:
                    break

        year_count = sum(1 for r in all_records if r["year"] == year)
        print(f"Year {year}: collected {year_count} records across all states")

    return pd.DataFrame(all_records)


def get_genre_from_mbid(mbid):
    """
    Look up an artist's genre via MusicBrainz. Prefers the formal `genres`
    field (curated, e.g. "indie rock") over `tags` (free-text folksonomy,
    e.g. "_edit" or "2008 universal fire victim" -- real junk we saw in
    earlier runs). Tags are only used as a fallback, and filtered first.

    Returns (genre, reason) where reason is one of:
      "found" / "no_mbid" / "lookup_failed" / "no_genre_data"
    -- used to distinguish *why* something ended up "unknown", since those
    have very different fixes (missing mbid vs. a real API problem vs.
    MusicBrainz genuinely having no data for that artist).
    """
    if not mbid:
        return "unknown", "no_mbid"
    if mbid in artist_genre_cache:
        return artist_genre_cache[mbid]

    url = MUSICBRAINZ_ARTIST_URL.format(mbid=mbid)
    result = ("unknown", "no_genre_data")
    try:
        response = _mb_session.get(
            url, headers=MB_HEADERS, params={"inc": "genres+tags", "fmt": "json"}, timeout=10
        )
        time.sleep(1.1)  # MusicBrainz allows ~1 request/sec

        if response.status_code == 200:
            data = response.json()
            genres = data.get("genres", [])
            tags = data.get("tags", [])

            if genres:
                genres_sorted = sorted(genres, key=lambda g: g.get("count", 0), reverse=True)
                result = (genres_sorted[0].get("name", "unknown").lower(), "found")
            else:
                for tag in sorted(tags, key=lambda t: t.get("count", 0), reverse=True):
                    name = tag.get("name", "").lower().strip()
                    if name and not _JUNK_TAG_PATTERN.search(name) and len(name) <= 25:
                        result = (name, "found")
                        break
        else:
            print(f"MusicBrainz error {response.status_code} for {mbid}")
            result = ("unknown", "lookup_failed")
    except requests.RequestException as e:
        print(f"Error fetching MBID {mbid}: {e}")
        result = ("unknown", "lookup_failed")

    artist_genre_cache[mbid] = result
    return result


if __name__ == "__main__":
    _load_genre_cache()

    # Roughly the last 5 years, most recent first.
    TARGET_YEARS = [2026, 2025, 2024, 2023, 2022]

    if os.path.exists(RAW_SETLISTS_CACHE):
        print(f"Found existing {RAW_SETLISTS_CACHE}, skipping setlist.fm collection "
              f"and reusing it. Delete that file if you want to re-collect from scratch.\n")
        raw_df = pd.read_csv(RAW_SETLISTS_CACHE, keep_default_na=False)
    else:
        print("Step 1: collecting setlists per state, per year...\n")
        t0 = time.time()
        raw_df = collect_setlists_by_state(years=TARGET_YEARS, max_pages_per_state=1)
        print(f"\nStep 1 took {(time.time() - t0) / 60:.1f} minutes")
        # Save immediately -- this step's API calls should never need repeating
        # just because Step 2 (the much slower part) crashes or gets interrupted.
        raw_df.to_csv(RAW_SETLISTS_CACHE, index=False)
        print(f"Saved raw setlist data to {RAW_SETLISTS_CACHE}")

    print(f"\nTotal setlist records: {len(raw_df)}")

    unique_mbids = [m for m in raw_df["mbid"].unique() if m]
    missing_mbid_count = (raw_df["mbid"] == "").sum()
    already_cached = sum(1 for m in unique_mbids if m in artist_genre_cache)
    remaining = len(unique_mbids) - already_cached
    print(f"Records with no mbid at all: {missing_mbid_count} (these can't be genre-looked-up)")
    print(f"Unique artists: {len(unique_mbids)}  "
          f"({already_cached} already cached, {remaining} left to look up)\n")

    print("Step 2: looking up genres on MusicBrainz...\n")
    t0 = time.time()
    for i, mbid in enumerate(unique_mbids, start=1):
        get_genre_from_mbid(mbid)
        if i % 25 == 0:
            elapsed = time.time() - t0
            rate = i / elapsed  # lookups/sec, includes cache hits so this warms up fast
            remaining_count = len(unique_mbids) - i
            eta_min = (remaining_count / rate) / 60 if rate > 0 else float("nan")
            print(f"  {i}/{len(unique_mbids)} looked up  "
                  f"({elapsed/60:.1f} min elapsed, ~{eta_min:.1f} min remaining)")
            _save_genre_cache()  # checkpoint periodically, not just at the very end

    _save_genre_cache()

    # Apply cached lookups to every record, including ones with no mbid.
    lookup_results = raw_df["mbid"].apply(get_genre_from_mbid)
    raw_df["genre"] = lookup_results.apply(lambda r: r[0])
    reasons = lookup_results.apply(lambda r: r[1])

    print("\n-----------------------------")
    print("GENRE COVERAGE BREAKDOWN")
    print("-----------------------------")
    print(reasons.value_counts())

    df_grouped = (
        raw_df.groupby(["year", "state", "genre"]).size().reset_index(name="event_count")
    )
    df_grouped.to_csv("concert_map_data_setlistfm.csv", index=False)
    print(f"\nDone! Saved {len(df_grouped)} rows to concert_map_data_setlistfm.csv")
