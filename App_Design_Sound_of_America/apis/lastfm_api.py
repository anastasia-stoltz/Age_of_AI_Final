import os
import requests
from pathlib import Path
from dotenv import load_dotenv


# --------------------------------------------------
# PATHS
# --------------------------------------------------

API_DIR = Path(__file__).resolve().parent
ASSIGNMENT_DIR = API_DIR.parent.parent.parent

# Your private .env lives outside the shared GitHub repo
ENV_PATH = ASSIGNMENT_DIR / "soundofmusic" / ".env"


# --------------------------------------------------
# LOAD API KEY
# --------------------------------------------------

load_dotenv(ENV_PATH)

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

if not LASTFM_API_KEY:
    raise ValueError(
        "LASTFM_API_KEY not found in private .env"
    )


# --------------------------------------------------
# LAST.FM SETTINGS
# --------------------------------------------------

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"


# Approved genre vocabulary based on the cleaned feasibility test
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
# HELPERS
# --------------------------------------------------

def _request_tags(params):
    """
    Make one Last.fm artist.getTopTags request.
    """

    response = requests.get(
        LASTFM_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return (
        data.get("toptags", {})
        .get("tag", [])
    )


def _clean_tags(tags):
    """
    Keep only approved genre tags and return the strongest ones.
    """

    cleaned = []

    for tag in tags:

        name = tag.get("name", "").strip()

        if not name:
            continue

        normalized = name.lower()

        try:
            count = int(tag.get("count", 0))
        except (TypeError, ValueError):
            count = 0

        if normalized not in VALID_GENRES:
            continue

        if count < 10:
            continue

        cleaned.append({
            "name": normalized,
            "count": count
        })

    cleaned.sort(
        key=lambda x: x["count"],
        reverse=True
    )

    return cleaned


# --------------------------------------------------
# PUBLIC GENRE LOOKUP
# --------------------------------------------------

def get_lastfm_genre(artist_name, mbid=None):
    """
    Return the strongest cleaned Last.fm genre for an artist.

    Lookup order:
      1. MusicBrainz ID when available
      2. Artist name fallback

    Returns:
      (genre, reason)

    Possible reasons:
      "found"
      "no_genre_data"
      "lookup_failed"
    """

    try:

        tags = []

        # Try exact MBID first
        if mbid:

            params = {
                "method": "artist.getTopTags",
                "mbid": mbid,
                "api_key": LASTFM_API_KEY,
                "format": "json",
                "autocorrect": 1
            }

            tags = _request_tags(params)


        # Fall back to artist name if needed
        if not tags and artist_name:

            params = {
                "method": "artist.getTopTags",
                "artist": artist_name,
                "api_key": LASTFM_API_KEY,
                "format": "json",
                "autocorrect": 1
            }

            tags = _request_tags(params)


        cleaned = _clean_tags(tags)

        if cleaned:
            return cleaned[0]["name"], "found"

        return "unknown", "no_genre_data"


    except requests.RequestException as error:

        print(
            f"Last.fm lookup failed for "
            f"{artist_name}: {error}"
        )

        return "unknown", "lookup_failed"