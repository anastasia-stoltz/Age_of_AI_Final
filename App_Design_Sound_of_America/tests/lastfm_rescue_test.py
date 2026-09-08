import csv
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv


# --------------------------------------------------
# PATHS
# --------------------------------------------------

TESTS_DIR = Path(__file__).resolve().parent
ASSIGNMENT_DIR = TESTS_DIR.parent.parent.parent

ENV_PATH = ASSIGNMENT_DIR / "soundofmusic" / ".env"
MISSING_FILE = TESTS_DIR.parent.parent / "missing_genre_artists.csv"


# --------------------------------------------------
# LOAD API KEY
# --------------------------------------------------

load_dotenv(ENV_PATH)

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

if not LASTFM_API_KEY:
    raise ValueError("LASTFM_API_KEY not found in .env")


# --------------------------------------------------
# LAST.FM SETTINGS
# --------------------------------------------------

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"


# Approved genre vocabulary
VALID_GENRES = {
    "alternative",
    "alternative hip-hop",
    "alternative metal",
    "alternative rock",
    "bedroom pop",
    "breaks",
    "dance",
    "disco",
    "edm",
    "electro",
    "electronic",
    "electronica",
    "electropop",
    "experimental",
    "folk",
    "funk",
    "fusion",
    "garage rock",
    "goa",
    "hard rock",
    "hardcore",
    "hardcore punk",
    "hip-hop",
    "hip hop",
    "hyperpop",
    "indie",
    "indie pop",
    "indie rock",
    "jazz rap",
    "lo-fi",
    "math rock",
    "metal",
    "metalcore",
    "modern rock",
    "noise",
    "noise rock",
    "nu metal",
    "nu metalcore",
    "pop",
    "pop punk",
    "post-hardcore",
    "power pop",
    "psychedelic",
    "psytrance",
    "punk",
    "punk rock",
    "rap",
    "rap rock",
    "rave",
    "rnb",
    "rock",
    "singer-songwriter",
    "soul",
    "surf rock",
    "swancore"
}


# --------------------------------------------------
# LAST.FM HELPERS
# --------------------------------------------------

def get_lastfm_tags(name, mbid):
    """
    Query Last.fm for an artist's top tags.

    Uses MBID first.
    If MBID returns no tags, falls back to artist name.
    """

    params = {
        "method": "artist.getTopTags",
        "mbid": mbid,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "autocorrect": 1
    }

    response = requests.get(
        LASTFM_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    tags = (
        data.get("toptags", {})
        .get("tag", [])
    )

    # Fall back to artist name if MBID returned no tags
    if not tags:

        params = {
            "method": "artist.getTopTags",
            "artist": name,
            "api_key": LASTFM_API_KEY,
            "format": "json",
            "autocorrect": 1
        }

        response = requests.get(
            LASTFM_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        tags = (
            data.get("toptags", {})
            .get("tag", [])
        )

    return tags


def clean_tags(tags):
    """
    Keep only tags that match the approved genre vocabulary.
    """

    cleaned = []

    for tag in tags:

        name = tag.get("name", "").strip()
        count = int(tag.get("count", 0))

        if not name:
            continue

        normalized = name.lower()

        if normalized not in VALID_GENRES:
            continue

        # Ignore very weak tags
        if count < 10:
            continue

        cleaned.append({
            "name": name,
            "count": count
        })

    cleaned.sort(
        key=lambda x: x["count"],
        reverse=True
    )

    return cleaned[:5]


# --------------------------------------------------
# LOAD MISSING ARTISTS
# --------------------------------------------------

missing_artists = []

with open(
    MISSING_FILE,
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        missing_artists.append(row)


# --------------------------------------------------
# RUN RESCUE TEST
# --------------------------------------------------

print("\nLAST.FM CLEAN GENRE RESCUE TEST\n")

rescued = 0
still_missing = 0
errors = 0

rescued_artists = []
missing_after_lastfm = []


for i, row in enumerate(missing_artists, start=1):

    name = row["name"]
    mbid = row["mbid"]

    try:

        tags = get_lastfm_tags(name, mbid)

        cleaned = clean_tags(tags)

        if cleaned:

            rescued += 1

            genre_names = [
                tag["name"]
                for tag in cleaned
            ]

            rescued_artists.append({
                "name": name,
                "mbid": mbid,
                "genres": genre_names
            })

            print(
                f"{i:>2}/{len(missing_artists)} "
                f"{name:<30} "
                f"RESCUED -> {genre_names}"
            )

        else:

            still_missing += 1

            missing_after_lastfm.append({
                "name": name,
                "mbid": mbid
            })

            print(
                f"{i:>2}/{len(missing_artists)} "
                f"{name:<30} "
                f"NO VALID GENRE"
            )

    except requests.exceptions.RequestException as error:

        errors += 1

        missing_after_lastfm.append({
            "name": name,
            "mbid": mbid
        })

        print(
            f"{i:>2}/{len(missing_artists)} "
            f"{name:<30} "
            f"ERROR -> {error}"
        )

    time.sleep(0.5)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\n-----------------------------")
print("LAST.FM CLEAN RESCUE SUMMARY")
print("-----------------------------")

print(f"Artists tested: {len(missing_artists)}")
print(f"Artists rescued: {rescued}")
print(f"Still missing: {still_missing}")
print(f"Errors: {errors}")

if missing_artists:

    rescue_rate = (
        rescued
        / len(missing_artists)
        * 100
    )

    print(
        f"Clean rescue rate: "
        f"{rescue_rate:.1f}%"
    )


print("\nSuccessful clean rescues:")

for artist in rescued_artists:

    print(
        f"- {artist['name']}: "
        f"{', '.join(artist['genres'])}"
    )


print("\nStill missing after Last.fm:")

for artist in missing_after_lastfm:

    print(
        f"- {artist['name']}"
    )