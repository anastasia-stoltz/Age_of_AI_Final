import json
import re
import sys
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# PATHS
# --------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
APP_DIR = REPO_ROOT / "App_Design_Sound_of_America"

RAW_SETLISTS_FILE = REPO_ROOT / "raw_setlists_cache.csv"
ENRICHED_CACHE_FILE = REPO_ROOT / "artist_enriched_genre_cache.json"

UNRESOLVED_FILE = (
    SCRIPT_DIR / "unresolved_artists_full_run.csv"
)

OUTPUT_FILE = (
    SCRIPT_DIR / "concert_map_data_setlistfm.csv"
)

RESCUE_REPORT_FILE = (
    SCRIPT_DIR / "unresolved_rescue_results.csv"
)


# --------------------------------------------------
# ALLOW IMPORTS FROM APP API MODULES
# --------------------------------------------------

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


from apis.lastfm_api import get_lastfm_genre
from apis.wikidata_api import get_wikidata_genre
from apis.discogs_api import get_discogs_genre


# --------------------------------------------------
# LOAD FILES
# --------------------------------------------------

raw_df = pd.read_csv(
    RAW_SETLISTS_FILE,
    keep_default_na=False
)

unresolved_df = pd.read_csv(
    UNRESOLVED_FILE,
    keep_default_na=False
)

with open(
    ENRICHED_CACHE_FILE,
    "r",
    encoding="utf-8"
) as file:
    enriched_cache = json.load(file)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def make_cache_key(mbid, artist_name):
    """
    Match the cache-key format used by the main collector.
    """

    mbid = str(mbid).strip()
    artist_name = str(artist_name).strip()

    if mbid:
        return f"mbid::{mbid}"

    return f"name::{artist_name.lower()}"


def save_cache():
    """
    Save progress after each rescue so work is never lost.
    """

    with open(
        ENRICHED_CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            enriched_cache,
            file,
            indent=2
        )


# --------------------------------------------------
# TRIBUTE-ACT DETECTION
# --------------------------------------------------

TRIBUTE_PATTERNS = [
    r"(.+?):\s*a tribute to (.+)",
    r"(.+?):\s*tribute to (.+)",
    r"(.+?)\s*-\s*a tribute to (.+)",
    r"(.+?)\s*-\s*tribute to (.+)",
]


def detect_tribute_target(artist_name):
    """
    Detect explicit tribute-act names such as:

    Badfish: A Tribute to Sublime
    Rain: A Tribute to the Beatles

    Returns the named tribute artist, or None.
    """

    artist_name = artist_name.strip()

    for pattern in TRIBUTE_PATTERNS:

        match = re.match(
            pattern,
            artist_name,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(2).strip()

    return None


# --------------------------------------------------
# FIND GENRE FOR TRIBUTE TARGET
# --------------------------------------------------

def resolve_tribute_target(target_name):
    """
    Try to classify the explicitly named tribute target.

    We use Last.fm and Discogs because they support artist-name lookup.
    """

    genre, reason = get_lastfm_genre(
        artist_name=target_name,
        mbid=None
    )

    if genre != "unknown":
        return genre, "tribute_lastfm"

    genre, reason = get_discogs_genre(
        target_name
    )

    if genre != "unknown":
        return genre, "tribute_discogs"

    return "unknown", "unknown"


# --------------------------------------------------
# STANDARD RESCUE PIPELINE
# --------------------------------------------------

def rescue_artist(artist_name, mbid):
    """
    Retry unresolved artists using the fallback sources.

    Order:
    1. Last.fm
    2. Wikidata exact MBID
    3. Discogs verified artist
    4. Explicit tribute-target inference
    """

    # ----------------------------------------------
    # LAST.FM
    # ----------------------------------------------

    genre, reason = get_lastfm_genre(
        artist_name=artist_name,
        mbid=mbid if mbid else None
    )

    if genre != "unknown":
        return genre, "lastfm"


    # ----------------------------------------------
    # WIKIDATA
    # ----------------------------------------------

    if mbid:

        genre, reason = get_wikidata_genre(
            mbid
        )

        if genre != "unknown":
            return genre, "wikidata"


    # ----------------------------------------------
    # DISCOGS
    # ----------------------------------------------

    genre, reason = get_discogs_genre(
        artist_name
    )

    if genre != "unknown":
        return genre, "discogs"


    # ----------------------------------------------
    # EXPLICIT TRIBUTE ACT
    # ----------------------------------------------

    tribute_target = detect_tribute_target(
        artist_name
    )

    if tribute_target:

        genre, source = resolve_tribute_target(
            tribute_target
        )

        if genre != "unknown":
            return genre, source


    return "unknown", "unknown"


# --------------------------------------------------
# RESCUE UNRESOLVED ARTISTS
# --------------------------------------------------

print("\n-----------------------------------")
print("TARGETED UNRESOLVED ARTIST RESCUE")
print("-----------------------------------\n")

results = []

total = len(unresolved_df)

for index, row in unresolved_df.iterrows():

    artist_name = row["artist_name"]
    mbid = row["mbid"]
    unknown_records = int(
        row["unknown_records"]
    )

    genre, source = rescue_artist(
        artist_name,
        mbid
    )

    cache_key = make_cache_key(
        mbid,
        artist_name
    )

    if genre != "unknown":

        enriched_cache[cache_key] = [
            genre,
            source
        ]

        save_cache()

        print(
            f"{index + 1}/{total} "
            f"{artist_name:<35} "
            f"RESCUED -> {genre} "
            f"({source}) "
            f"[{unknown_records} records]"
        )

    else:

        print(
            f"{index + 1}/{total} "
            f"{artist_name:<35} "
            f"STILL UNKNOWN "
            f"[{unknown_records} records]"
        )

    results.append({
        "artist_name": artist_name,
        "mbid": mbid,
        "unknown_records": unknown_records,
        "genre": genre,
        "source": source
    })


# --------------------------------------------------
# SAVE RESCUE REPORT
# --------------------------------------------------

results_df = pd.DataFrame(
    results
)

results_df.to_csv(
    RESCUE_REPORT_FILE,
    index=False
)


# --------------------------------------------------
# REAPPLY UPDATED CACHE TO RAW DATA
# --------------------------------------------------

def get_final_genre(row):

    cache_key = make_cache_key(
        row["mbid"],
        row["artist_name"]
    )

    result = enriched_cache.get(
        cache_key
    )

    if not result:
        return "unknown"

    return result[0]


raw_df["genre"] = raw_df.apply(
    get_final_genre,
    axis=1
)


# --------------------------------------------------
# NEW COVERAGE NUMBERS
# --------------------------------------------------

known_count = (
    raw_df["genre"] != "unknown"
).sum()

unknown_count = (
    raw_df["genre"] == "unknown"
).sum()

total_records = len(
    raw_df
)

coverage = (
    known_count
    / total_records
    * 100
)


print("\n-----------------------------------")
print("UPDATED GENRE COVERAGE")
print("-----------------------------------")

print(
    f"Known records: {known_count}"
)

print(
    f"Unknown records: {unknown_count}"
)

print(
    f"Total records: {total_records}"
)

print(
    f"Record coverage: {coverage:.1f}%"
)


# --------------------------------------------------
# REBUILD MAP CSV
# --------------------------------------------------

map_df = (
    raw_df
    .groupby(
        [
            "year",
            "state",
            "genre"
        ]
    )
    .size()
    .reset_index(
        name="event_count"
    )
)

map_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    f"\nUpdated map CSV saved to:\n"
    f"{OUTPUT_FILE}"
)

print(
    f"\nDetailed rescue report saved to:\n"
    f"{RESCUE_REPORT_FILE}"
)