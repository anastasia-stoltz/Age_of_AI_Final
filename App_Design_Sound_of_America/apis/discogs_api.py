import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv


# --------------------------------------------------
# PATHS
# --------------------------------------------------

API_DIR = Path(__file__).resolve().parent
ASSIGNMENT_DIR = API_DIR.parent.parent.parent

# Private .env lives outside the shared GitHub repo
ENV_PATH = ASSIGNMENT_DIR / "soundofmusic" / ".env"


# --------------------------------------------------
# LOAD API KEY
# --------------------------------------------------

load_dotenv(ENV_PATH)

DISCOGS_API_KEY = os.getenv("DISCOGS_API_KEY")

if not DISCOGS_API_KEY:
    raise ValueError(
        "DISCOGS_API_KEY not found in private .env"
    )


# --------------------------------------------------
# DISCOGS SETTINGS
# --------------------------------------------------

DISCOGS_SEARCH_URL = "https://api.discogs.com/database/search"
DISCOGS_API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": "SoundOfAmericaProject/1.0",
    "Authorization": f"Discogs token={DISCOGS_API_KEY}"
}


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def _normalize_name(name):
    """
    Normalize artist names for identity matching.
    """

    name = name.lower().strip()

    # Remove Discogs disambiguation suffixes such as Artist (2)
    name = re.sub(r"\s*\(\d+\)$", "", name)

    # Ignore punctuation and spacing differences
    name = re.sub(r"[^a-z0-9]+", "", name)

    return name


def _find_verified_artist(artist_name):
    """
    Search Discogs artist records and accept only an exact
    normalized-name match.

    Returns:
        {"id": ..., "name": ...}
        or None
    """

    params = {
        "q": artist_name,
        "type": "artist",
        "per_page": 10
    }

    response = requests.get(
        DISCOGS_SEARCH_URL,
        params=params,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    results = response.json().get("results", [])

    target = _normalize_name(artist_name)

    for result in results:

        discogs_name = result.get("title", "")

        if _normalize_name(discogs_name) == target:
            return {
                "id": result.get("id"),
                "name": discogs_name
            }

    return None


def _get_artist_release_genres(artist_id, max_releases=3):
    """
    Get genres/styles from releases associated with a verified
    Discogs artist ID.

    Returns:
        genres, styles
    """

    releases_url = (
        f"{DISCOGS_API_URL}/artists/"
        f"{artist_id}/releases"
    )

    response = requests.get(
        releases_url,
        params={
            "sort": "year",
            "sort_order": "desc",
            "per_page": 5
        },
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    releases = (
        response.json()
        .get("releases", [])
    )

    genres = []
    styles = []

    releases_checked = 0

    for release in releases:

        resource_url = release.get("resource_url")

        if not resource_url:
            continue

        try:

            detail_response = requests.get(
                resource_url,
                headers=HEADERS,
                timeout=30
            )

            detail_response.raise_for_status()

            detail = detail_response.json()

            for genre in detail.get("genres", []):
                if genre not in genres:
                    genres.append(genre)

            for style in detail.get("styles", []):
                if style not in styles:
                    styles.append(style)

            releases_checked += 1

            if releases_checked >= max_releases:
                break

        except requests.RequestException:
            continue

    return genres, styles


# --------------------------------------------------
# PUBLIC GENRE LOOKUP
# --------------------------------------------------

def get_discogs_genre(artist_name):
    """
    Return one verified genre/style for an artist using Discogs.

    The artist identity must first match a Discogs artist record.
    Genre/style is then collected only from releases associated
    with that verified artist ID.

    Returns:
        (genre, reason)

    Possible reasons:
        "found"
        "no_artist_match"
        "no_genre_data"
        "lookup_failed"
    """

    if not artist_name:
        return "unknown", "no_artist_match"

    try:

        artist = _find_verified_artist(artist_name)

        if not artist:
            return "unknown", "no_artist_match"

        genres, styles = _get_artist_release_genres(
            artist["id"]
        )

        # Prefer a specific style over a broad Discogs genre
        if styles:
            return styles[0].lower(), "found"

        if genres:
            return genres[0].lower(), "found"

        return "unknown", "no_genre_data"

    except requests.RequestException as error:

        print(
            f"Discogs lookup failed for "
            f"{artist_name}: {error}"
        )

        return "unknown", "lookup_failed"