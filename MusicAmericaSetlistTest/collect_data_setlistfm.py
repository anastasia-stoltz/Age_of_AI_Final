"""
Data collection script for Music Across America.

Pipeline:
Setlist.fm -> MusicBrainz -> Last.fm -> Wikidata -> Discogs
           -> Tribute-act inference -> Unknown

The script:
1. Collects U.S. setlist data by state and year.
2. Uses MusicBrainz as the primary genre source.
3. Enriches unresolved artists with Last.fm, Wikidata, and Discogs.
4. For explicit tribute acts (e.g. "Badfish: A Tribute to Sublime") that
   still come up unresolved, extracts the named original artist and
   classifies the show by *their* genre instead.
5. Caches completed lookups so API work does not need to be repeated.
6. Aggregates the results by year, state, and genre for the dashboard map.

This folds in what used to be a separate two-step rescue pass
(find_unresolved_artists.py + rescue_unresolved_artists.py) directly into
the main resolve_genre() hierarchy, so a fresh full run gets the same
coverage in one pass instead of needing a manual follow-up.
"""

import json
import os
import re
import sys
import time
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

APP_DIR = REPO_ROOT / "App_Design_Sound_of_America"

# Tracy's private API-key file lives outside the shared GitHub repo.
PRIVATE_ENV_PATH = ASSIGNMENT_DIR / "soundofmusic" / ".env"

# Existing caches created by earlier runs live at the repo root.
RAW_SETLISTS_CACHE = REPO_ROOT / "raw_setlists_cache.csv"
GENRE_CACHE_FILE = REPO_ROOT / "artist_genre_cache.json"

# New cache for the FINAL multi-source genre decision.
ENRICHED_GENRE_CACHE_FILE = (
    REPO_ROOT / "artist_enriched_genre_cache.json"
)

# Keep the new Setlist.fm output separate from the current live-map CSV
# until we verify that everything looks correct.
OUTPUT_FILE = SCRIPT_DIR / "concert_map_data_setlistfm.csv"


# --------------------------------------------------
# ENVIRONMENT VARIABLES
# --------------------------------------------------

# First allow a normal local .env if another teammate uses one.
load_dotenv()

# Then also load Tracy's private .env when it exists.
if PRIVATE_ENV_PATH.exists():
    load_dotenv(PRIVATE_ENV_PATH, override=False)


# --------------------------------------------------
# ENRICHMENT API MODULES
# --------------------------------------------------

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# Last.fm requires an API key.
# The collector still runs without it if another teammate lacks the key.
try:
    from apis.lastfm_api import get_lastfm_genre
except (ImportError, ValueError) as error:
    print(f"Last.fm fallback unavailable: {error}")
    get_lastfm_genre = None


# Wikidata does not require an API key.
from apis.wikidata_api import get_wikidata_genre


# Discogs requires an API key.
# The collector still runs without it if the key is unavailable.
try:
    from apis.discogs_api import get_discogs_genre
except (ImportError, ValueError) as error:
    print(f"Discogs fallback unavailable: {error}")
    get_discogs_genre = None


# --------------------------------------------------
# API SETTINGS
# --------------------------------------------------

SETLISTFM_API_KEY = os.getenv("SETLISTFM_API_KEY")

if not SETLISTFM_API_KEY:
    raise ValueError(
        "SETLISTFM_API_KEY was not found in an available .env file."
    )


SETLIST_URL = (
    "https://api.setlist.fm/rest/1.0/search/setlists"
)

MUSICBRAINZ_ARTIST_URL = (
    "https://musicbrainz.org/ws/2/artist/{mbid}"
)


SETLIST_HEADERS = {
    "Accept": "application/json",
    "x-api-key": SETLISTFM_API_KEY,
}


MB_HEADERS = {
    "User-Agent": "SoundOfAmericaProject/1.0"
}


# --------------------------------------------------
# ALL 50 U.S. STATES
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
# MUSICBRAINZ TAG FILTER
# --------------------------------------------------

# Reject obviously problematic MusicBrainz fallback tags containing
# digits or underscores.
_JUNK_TAG_PATTERN = re.compile(r"[\d_]")


# --------------------------------------------------
# REQUEST SESSIONS
# --------------------------------------------------

def _make_session():
    """
    Session for Setlist.fm.

    Retries temporary rate-limit and server errors.
    """

    session = requests.Session()

    retry = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session.mount(
        "https://",
        adapter
    )

    session.mount(
        "http://",
        adapter
    )

    return session


def _make_mb_session():
    """
    Session for MusicBrainz.

    MusicBrainz fails relatively quickly so a temporary bad patch does
    not turn into an hours-long retry cycle.
    """

    session = requests.Session()

    retry = Retry(
        total=1,
        backoff_factor=0.5,
        status_forcelist=[
            500,
            502,
            504,
        ],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session.mount(
        "https://",
        adapter
    )

    session.mount(
        "http://",
        adapter
    )

    return session


_session = _make_session()
_mb_session = _make_mb_session()


# --------------------------------------------------
# CACHES
# --------------------------------------------------

# Existing MusicBrainz-only cache.
artist_genre_cache = {}

# New final multi-source cache.
enriched_genre_cache = {}


def _load_genre_cache():
    """
    Load previously completed MusicBrainz lookups.
    """

    global artist_genre_cache

    if GENRE_CACHE_FILE.exists():

        with open(
            GENRE_CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            raw = json.load(file)

        artist_genre_cache = {
            key: tuple(value)
            for key, value in raw.items()
        }

        print(
            f"Loaded {len(artist_genre_cache)} "
            f"cached MusicBrainz lookups from "
            f"{GENRE_CACHE_FILE.name}"
        )


def _save_genre_cache():
    """
    Save MusicBrainz-only lookups.
    """

    with open(
        GENRE_CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            artist_genre_cache,
            file,
            indent=2
        )


def _load_enriched_genre_cache():
    """
    Load previously completed multi-source genre resolutions.
    """

    global enriched_genre_cache

    if ENRICHED_GENRE_CACHE_FILE.exists():

        with open(
            ENRICHED_GENRE_CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            raw = json.load(file)

        enriched_genre_cache = {
            key: tuple(value)
            for key, value in raw.items()
        }

        print(
            f"Loaded {len(enriched_genre_cache)} "
            f"enriched genre lookups from "
            f"{ENRICHED_GENRE_CACHE_FILE.name}"
        )


def _save_enriched_genre_cache():
    """
    Save final multi-source genre decisions.
    """

    with open(
        ENRICHED_GENRE_CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            enriched_genre_cache,
            file,
            indent=2
        )


# --------------------------------------------------
# SETLIST.FM COLLECTION
# --------------------------------------------------

def collect_setlists_by_state(
    years,
    max_pages_per_state=1,
    page_delay=0.6
):
    """
    Query Setlist.fm once per state and target year.

    This ensures all 50 states and the requested historical years
    are represented rather than relying only on recently logged shows.
    """

    all_records = []

    for year in years:

        for state_name, state_code in STATES.items():

            state_total = None

            for page in range(
                1,
                max_pages_per_state + 1
            ):

                params = {
                    "countryCode": "US",
                    "stateCode": state_code,
                    "year": year,
                    "p": page,
                }

                response = _session.get(
                    SETLIST_URL,
                    headers=SETLIST_HEADERS,
                    params=params,
                    timeout=30
                )

                # Stay comfortably under Setlist.fm's rate limit.
                time.sleep(page_delay)

                if response.status_code != 200:

                    print(
                        f"{year} {state_name} "
                        f"page {page}: "
                        f"error {response.status_code}"
                    )

                    continue

                data = response.json()

                state_total = data.get(
                    "total",
                    0
                )

                setlists = data.get(
                    "setlist",
                    []
                )

                if not setlists:
                    break

                for record in setlists:

                    artist = (
                        record.get(
                            "artist",
                            {}
                        )
                        or {}
                    )

                    mbid = artist.get(
                        "mbid",
                        ""
                    )

                    artist_name = artist.get(
                        "name",
                        ""
                    )

                    all_records.append({
                        "year": year,
                        "state": state_code,
                        "mbid": mbid,
                        "artist_name": artist_name,
                    })

                if (
                    state_total is not None
                    and page * 20 >= state_total
                ):
                    break

        year_count = sum(
            1
            for record in all_records
            if record["year"] == year
        )

        print(
            f"Year {year}: collected "
            f"{year_count} records across all states"
        )

    return pd.DataFrame(
        all_records
    )


# --------------------------------------------------
# PRIMARY MUSICBRAINZ LOOKUP
# --------------------------------------------------

def get_genre_from_mbid(mbid):
    """
    Look up an artist's genre using MusicBrainz.

    Formal genres are preferred.

    MusicBrainz tags are used only when no formal genre exists and
    obvious junk tags are filtered.

    Returns:
        (genre, reason)

    Reasons:
        found
        no_mbid
        lookup_failed
        no_genre_data
    """

    if not mbid:
        return "unknown", "no_mbid"

    if mbid in artist_genre_cache:
        return artist_genre_cache[mbid]

    url = MUSICBRAINZ_ARTIST_URL.format(
        mbid=mbid
    )

    result = (
        "unknown",
        "no_genre_data"
    )

    try:

        response = _mb_session.get(
            url,
            headers=MB_HEADERS,
            params={
                "inc": "genres+tags",
                "fmt": "json"
            },
            timeout=10
        )

        # MusicBrainz allows roughly one request per second.
        time.sleep(1.1)

        if response.status_code == 200:

            data = response.json()

            genres = data.get(
                "genres",
                []
            )

            tags = data.get(
                "tags",
                []
            )

            if genres:

                genres_sorted = sorted(
                    genres,
                    key=lambda genre: genre.get(
                        "count",
                        0
                    ),
                    reverse=True
                )

                genre_name = (
                    genres_sorted[0]
                    .get(
                        "name",
                        "unknown"
                    )
                    .lower()
                    .strip()
                )

                result = (
                    genre_name,
                    "found"
                )

            else:

                for tag in sorted(
                    tags,
                    key=lambda item: item.get(
                        "count",
                        0
                    ),
                    reverse=True
                ):

                    name = (
                        tag.get(
                            "name",
                            ""
                        )
                        .lower()
                        .strip()
                    )

                    if (
                        name
                        and not _JUNK_TAG_PATTERN.search(name)
                        and len(name) <= 25
                    ):

                        result = (
                            name,
                            "found"
                        )

                        break

        else:

            print(
                f"MusicBrainz error "
                f"{response.status_code} "
                f"for {mbid}"
            )

            result = (
                "unknown",
                "lookup_failed"
            )

    except requests.RequestException as error:

        print(
            f"Error fetching MBID "
            f"{mbid}: {error}"
        )

        result = (
            "unknown",
            "lookup_failed"
        )

    artist_genre_cache[mbid] = result

    return result


# --------------------------------------------------
# TRIBUTE-ACT DETECTION
# --------------------------------------------------

# Matches artist names that explicitly identify themselves as a tribute
# act, e.g. "Badfish: A Tribute to Sublime" or "Rain - Tribute to the
# Beatles". These acts are almost never in MusicBrainz/Last.fm/Wikidata/
# Discogs under their own name, but the *named* target artist usually is.
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

    Returns the named tribute target, or None.
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


def resolve_tribute_target(target_name):
    """
    Classify the explicitly named tribute target using Last.fm and
    Discogs, since both support lookup by artist name (unlike Wikidata,
    which needs an MBID we won't have for the target either).
    """

    if get_lastfm_genre is not None:

        genre, reason = get_lastfm_genre(
            artist_name=target_name,
            mbid=None
        )

        if genre != "unknown":
            return genre, "tribute_lastfm"

    if get_discogs_genre is not None:

        genre, reason = get_discogs_genre(
            target_name
        )

        if genre != "unknown":
            return genre, "tribute_discogs"

    return "unknown", "unknown"


# --------------------------------------------------
# GENRE BUCKETING
# --------------------------------------------------
# Raw genres coming out of resolve_genre() are extremely fine-grained --
# MusicBrainz/Last.fm/Discogs between them can return 300+ distinct
# strings ("kawaii metal", "beatdown hardcore", "dark plugg", ...), which
# is unusable as a dashboard dropdown. This buckets each raw genre into
# one of a small set of broad categories.
#
# This is a best-effort heuristic (ordered keyword matching), not a
# perfect taxonomy -- genres that are genuinely cross-cutting (e.g.
# "country rock", "folk punk") get assigned to whichever bucket's
# keywords are checked first. GENRE_OVERRIDES below exists to hand-fix
# any specific raw genre that lands somewhere wrong; add to it as you
# spot-check the results.

# Exact-match overrides checked before the keyword rules -- use this for
# any specific raw genre string you want pinned to a bucket regardless of
# what the keyword rules would otherwise pick. Empty for now; add entries
# as you spot-check bucketing results, e.g. {"some raw genre": "Rock"}.
GENRE_OVERRIDES = {}

# Checked in order -- first bucket whose keyword appears in the raw genre
# (as a substring) wins. Order matters: more specific/exclusive genres
# (metal, punk, hip-hop, electronic) are checked before the broad "Rock"
# and "Pop" catch-alls, since e.g. "folk metal" should land in Metal, not
# get caught by a generic "folk" rule first.
GENRE_BUCKET_RULES = [
    ("Metal", [
        "metal", "grindcore", "deathcore", "mathcore", "djent", "thrash",
    ]),
    ("Punk/Hardcore", [
        "punk", "hardcore", "screamo", "emo", "riot grrrl", "psychobilly",
        "swancore", "emoviolence",
    ]),
    ("Hip-Hop/Rap", [
        "hip hop", "hip-hop", "rap", "trap", "crunk", "boom bap",
        "gangsta", "cloud rap", "horrorcore", "nerdcore", "g-funk",
        "dark plugg",
    ]),
    ("Electronic/Dance", [
        "electronic", "edm", "dubstep", "house", "techno", "trance",
        "electro", "synth", "dance", "breakbeat", "breakcore", "breaks",
        "drum n bass", "drum and bass", "downtempo", "ambient",
        "industrial", "ebm", "wave", "goa", "chiptune", "glitch",
        "ghettotech", "hyperpop", "rave", "hardstyle", "trip hop",
        "electronica", "big beat", "eurodance", "acid ", "disco",
        "new age", "lo-fi", "future bass", "drone",
    ]),
    ("Reggae/Ska", [
        "reggae", "dub", "ska", "dancehall",
    ]),
    ("Jazz/Blues", [
        "jazz", "blues", "big band", "swing", "dixieland", "lounge",
        "bop",
    ]),
    ("R&B/Soul/Funk", [
        "soul", "funk", "new jack swing", "r&b", "rnb",
    ]),
    ("Country/Folk/Americana", [
        "country", "bluegrass", "americana", "folk", "cowboy",
        "appalachian", "norteño", "red dirt", "singer-songwriter",
        "acoustic",
    ]),
    ("Christian/Gospel", [
        "christian", "gospel", "religious",
    ]),
    ("Classical", [
        "classical", "opera", "choral", "chamber", "orchestral",
    ]),
    ("Comedy/Spoken Word", [
        "comedy", "parody", "satire", "spoken word", "audiobook",
        "cookbook", "cabaret", "drag",
    ]),
    ("World", [
        "afrobeat", "cumbia", "salsa", "mariachi", "flamenco", "calypso",
        "zamrock", "hawaiian", "latin", "celtic", "polka", "k-pop",
        "filmi",
    ]),
    ("Pop", [
        "pop",
    ]),
    ("Rock", [
        "rock", "grunge", "psych", "indie", "jam band", "shoegaze",
        "surf", "aor", "alternative",
    ]),
]


def bucket_genre(raw_genre):
    """
    Map a fine-grained raw genre string to a broad dashboard-friendly
    bucket. Returns "Unknown" for unresolved artists, or
    "Other/Uncategorized" for anything that doesn't match a rule (often
    non-genre junk that slipped through upstream sources, e.g. "iowa" or
    "session").
    """

    genre = (raw_genre or "").lower().strip()

    if not genre or genre == "unknown":
        return "Unknown"

    if genre in GENRE_OVERRIDES:
        return GENRE_OVERRIDES[genre]

    for bucket_name, keywords in GENRE_BUCKET_RULES:
        if any(keyword in genre for keyword in keywords):
            return bucket_name

    return "Other/Uncategorized"


# --------------------------------------------------
# FINAL MULTI-SOURCE GENRE RESOLVER
# --------------------------------------------------

def _artist_cache_key(
    mbid,
    artist_name
):
    """
    Create a stable key for the enriched genre cache.
    """

    if mbid:
        return f"mbid::{mbid}"

    normalized_name = (
        artist_name
        .lower()
        .strip()
    )

    return f"name::{normalized_name}"


def resolve_genre(
    mbid,
    artist_name
):
    """
    Resolve the final genre using the tested hierarchy:

    1. MusicBrainz
    2. Last.fm cleaned tags
    3. Wikidata exact-MBID lookup
    4. Discogs verified-artist lookup
    5. Unknown

    Returns:
        (genre, source)
    """

    cache_key = _artist_cache_key(
        mbid,
        artist_name
    )

    if cache_key in enriched_genre_cache:
        return enriched_genre_cache[
            cache_key
        ]


    # --------------------------------------------------
    # 1. MUSICBRAINZ
    # --------------------------------------------------

    genre, reason = get_genre_from_mbid(
        mbid
    )

    if genre != "unknown":

        result = (
            genre,
            "musicbrainz"
        )

        enriched_genre_cache[
            cache_key
        ] = result

        return result


    # --------------------------------------------------
    # 2. LAST.FM
    # --------------------------------------------------

    if get_lastfm_genre is not None:

        lastfm_genre, lastfm_reason = (
            get_lastfm_genre(
                artist_name=artist_name,
                mbid=mbid if mbid else None
            )
        )

        if lastfm_genre != "unknown":

            result = (
                lastfm_genre,
                "lastfm"
            )

            enriched_genre_cache[
                cache_key
            ] = result

            return result


    # --------------------------------------------------
    # 3. WIKIDATA
    # --------------------------------------------------

    if mbid:

        wikidata_genre, wikidata_reason = (
            get_wikidata_genre(
                mbid
            )
        )

        if wikidata_genre != "unknown":

            result = (
                wikidata_genre,
                "wikidata"
            )

            enriched_genre_cache[
                cache_key
            ] = result

            return result


    # --------------------------------------------------
    # 4. DISCOGS
    # --------------------------------------------------

    if (
        get_discogs_genre is not None
        and artist_name
    ):

        discogs_genre, discogs_reason = (
            get_discogs_genre(
                artist_name
            )
        )

        if discogs_genre != "unknown":

            result = (
                discogs_genre,
                "discogs"
            )

            enriched_genre_cache[
                cache_key
            ] = result

            return result


    # --------------------------------------------------
    # 5. EXPLICIT TRIBUTE ACT
    # --------------------------------------------------
    # Tried last, since it only applies to names matching a specific
    # "X: A Tribute to Y" pattern -- and even then, classifies the show
    # by the *original* artist's genre, not the tribute act's own.

    tribute_target = detect_tribute_target(
        artist_name
    )

    if tribute_target:

        tribute_genre, tribute_source = resolve_tribute_target(
            tribute_target
        )

        if tribute_genre != "unknown":

            result = (
                tribute_genre,
                tribute_source
            )

            enriched_genre_cache[
                cache_key
            ] = result

            return result


    # --------------------------------------------------
    # 6. UNKNOWN
    # --------------------------------------------------

    result = (
        "unknown",
        "unknown"
    )

    enriched_genre_cache[
        cache_key
    ] = result

    return result


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

if __name__ == "__main__":

    _load_genre_cache()
    _load_enriched_genre_cache()


    # Roughly the last five years.
    TARGET_YEARS = [
        2026,
        2025,
        2024,
        2023,
        2022
    ]


    # --------------------------------------------------
    # STEP 1 — SETLIST COLLECTION
    # --------------------------------------------------

    if RAW_SETLISTS_CACHE.exists():

        print(
            f"Found existing "
            f"{RAW_SETLISTS_CACHE.name}, "
            f"skipping Setlist.fm collection "
            f"and reusing it.\n"
        )

        raw_df = pd.read_csv(
            RAW_SETLISTS_CACHE,
            keep_default_na=False
        )

    else:

        print(
            "Step 1: collecting setlists "
            "per state, per year...\n"
        )

        start_time = time.time()

        raw_df = collect_setlists_by_state(
            years=TARGET_YEARS,
            max_pages_per_state=1
        )

        elapsed_minutes = (
            time.time()
            - start_time
        ) / 60

        print(
            f"\nStep 1 took "
            f"{elapsed_minutes:.1f} minutes"
        )

        raw_df.to_csv(
            RAW_SETLISTS_CACHE,
            index=False
        )

        print(
            f"Saved raw setlist data to "
            f"{RAW_SETLISTS_CACHE.name}"
        )


    print(
        f"\nTotal setlist records: "
        f"{len(raw_df)}"
    )


        # --------------------------------------------------
    # STEP 2 — MUSICBRAINZ PRIMARY LOOKUPS
    # --------------------------------------------------

    unique_mbids = [
        mbid
        for mbid in raw_df["mbid"].unique()
        if mbid
    ]

    missing_mbid_count = (
        raw_df["mbid"] == ""
    ).sum()

    already_cached = [
        mbid
        for mbid in unique_mbids
        if mbid in artist_genre_cache
    ]

    uncached_mbids = [
        mbid
        for mbid in unique_mbids
        if mbid not in artist_genre_cache
    ]

    print(
        f"Records with no MBID: "
        f"{missing_mbid_count}"
    )

    print(
        f"Unique artists with MBIDs: "
        f"{len(unique_mbids)}"
    )

    print(
        f"MusicBrainz already cached: "
        f"{len(already_cached)}"
    )

    print(
        f"MusicBrainz lookups actually needed: "
        f"{len(uncached_mbids)}\n"
    )


    # If everything is already cached, skip the API loop entirely.
    if not uncached_mbids:

        print(
            "Step 2: no new MusicBrainz "
            "lookups needed.\n"
        )

    else:

        print(
            "Step 2: looking up only "
            "uncached artists on MusicBrainz...\n"
        )

        start_time = time.time()

        for index, mbid in enumerate(
            uncached_mbids,
            start=1
        ):

            get_genre_from_mbid(
                mbid
            )

            # Save progress regularly so an interrupted run can resume.
            if (
                index % 25 == 0
                or index == len(uncached_mbids)
            ):

                elapsed = (
                    time.time()
                    - start_time
                )

                rate = (
                    index / elapsed
                    if elapsed > 0
                    else 0
                )

                remaining_count = (
                    len(uncached_mbids)
                    - index
                )

                eta_minutes = (
                    remaining_count
                    / rate
                    / 60
                    if rate > 0
                    else 0
                )

                print(
                    f"  {index}/"
                    f"{len(uncached_mbids)} "
                    f"new lookups completed "
                    f"({elapsed / 60:.1f} min elapsed, "
                    f"~{eta_minutes:.1f} min remaining)"
                )

                _save_genre_cache()


    _save_genre_cache()


    # --------------------------------------------------
    # STEP 3 — MULTI-SOURCE ENRICHMENT
    # --------------------------------------------------

    print(
        "\nStep 3: enriching unresolved "
        "genres...\n"
    )

    lookup_results = raw_df.apply(
        lambda row: resolve_genre(
            row["mbid"],
            row["artist_name"]
        ),
        axis=1
    )


    raw_df["genre"] = (
        lookup_results.apply(
            lambda result: result[0]
        )
    )


    raw_df["genre_source"] = (
        lookup_results.apply(
            lambda result: result[1]
        )
    )


    # Keep the fine-grained genre for reference/debugging, but use the
    # bucketed version for the dashboard-facing output -- 300+ distinct
    # raw genres isn't a usable dropdown.
    raw_df["genre_detailed"] = raw_df["genre"]
    raw_df["genre"] = raw_df["genre_detailed"].apply(bucket_genre)


    _save_enriched_genre_cache()


    # --------------------------------------------------
    # BUCKETING SUMMARY
    # --------------------------------------------------

    print(
        "\n-----------------------------"
    )

    print(
        "GENRE BUCKET BREAKDOWN"
    )

    print(
        "-----------------------------"
    )

    print(
        raw_df["genre"]
        .value_counts()
    )

    other_bucket = raw_df[
        raw_df["genre"] == "Other/Uncategorized"
    ]

    if len(other_bucket) > 0:

        print(
            f"\n{len(other_bucket)} records landed in "
            f"Other/Uncategorized. Raw genres involved "
            f"(add to GENRE_OVERRIDES if any should move):"
        )

        print(
            other_bucket["genre_detailed"]
            .value_counts()
            .head(20)
        )


    # --------------------------------------------------
    # SOURCE BREAKDOWN
    # --------------------------------------------------

    print(
        "\n-----------------------------"
    )

    print(
        "FINAL GENRE SOURCE BREAKDOWN"
    )

    print(
        "-----------------------------"
    )

    print(
        raw_df["genre_source"]
        .value_counts()
    )


    # --------------------------------------------------
    # RECORD-LEVEL COVERAGE
    # --------------------------------------------------

    known_count = (
        raw_df["genre"]
        != "Unknown"
    ).sum()

    unknown_count = (
        raw_df["genre"]
        == "Unknown"
    ).sum()

    total_count = len(
        raw_df
    )

    record_coverage = (
        known_count
        / total_count
        * 100
        if total_count
        else 0
    )


    print(
        "\n-----------------------------"
    )

    print(
        "FINAL RECORD GENRE COVERAGE"
    )

    print(
        "-----------------------------"
    )

    print(
        f"Known genre records: "
        f"{known_count}"
    )

    print(
        f"Unknown genre records: "
        f"{unknown_count}"
    )

    print(
        f"Total records: "
        f"{total_count}"
    )

    print(
        f"Record genre coverage: "
        f"{record_coverage:.1f}%"
    )


    # --------------------------------------------------
    # UNIQUE-ARTIST COVERAGE
    # --------------------------------------------------

    unique_artist_df = (
        raw_df[
            [
                "mbid",
                "artist_name",
                "genre",
                "genre_source"
            ]
        ]
        .drop_duplicates(
            subset=[
                "mbid",
                "artist_name"
            ]
        )
    )


    unique_known = (
        unique_artist_df["genre"]
        != "Unknown"
    ).sum()

    unique_total = len(
        unique_artist_df
    )

    unique_coverage = (
        unique_known
        / unique_total
        * 100
        if unique_total
        else 0
    )


    print(
        "\n-----------------------------"
    )

    print(
        "FINAL UNIQUE-ARTIST COVERAGE"
    )

    print(
        "-----------------------------"
    )

    print(
        f"Artists with genre: "
        f"{unique_known}"
    )

    print(
        f"Total unique artists: "
        f"{unique_total}"
    )

    print(
        f"Unique-artist genre coverage: "
        f"{unique_coverage:.1f}%"
    )


    # --------------------------------------------------
    # STEP 4 — AGGREGATE FOR MAP
    # --------------------------------------------------

    df_grouped = (
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


    df_grouped.to_csv(
        OUTPUT_FILE,
        index=False
    )


    # Also keep a detailed reference file with the fine-grained genre
    # preserved (not used by the dashboard, but useful if you want to
    # audit a bucket or refine GENRE_BUCKET_RULES later).
    detailed_grouped = (
        raw_df
        .groupby(
            [
                "year",
                "state",
                "genre",
                "genre_detailed"
            ]
        )
        .size()
        .reset_index(
            name="event_count"
        )
    )

    DETAILED_OUTPUT_FILE = (
        SCRIPT_DIR / "concert_map_data_setlistfm_detailed.csv"
    )

    detailed_grouped.to_csv(
        DETAILED_OUTPUT_FILE,
        index=False
    )


    print(
        f"\nDone! Saved "
        f"{len(df_grouped)} rows to:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        f"\nDetailed (unbucketed) genre breakdown saved to:"
    )

    print(
        DETAILED_OUTPUT_FILE
    )