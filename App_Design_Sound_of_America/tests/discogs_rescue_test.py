import csv
import os
import re
import time
import requests
from pathlib import Path
from dotenv import load_dotenv


# --------------------------------------------------
# PATHS
# --------------------------------------------------

TESTS_DIR = Path(__file__).resolve().parent
ASSIGNMENT_DIR = TESTS_DIR.parent.parent.parent

# Private .env lives OUTSIDE the shared GitHub repo
ENV_PATH = ASSIGNMENT_DIR / "soundofmusic" / ".env"

# Original MusicBrainz missing-genre sample
MISSING_FILE = TESTS_DIR.parent.parent / "missing_genre_artists.csv"


# --------------------------------------------------
# LOAD DISCOGS API KEY
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

DISCOGS_SEARCH_URL = (
    "https://api.discogs.com/database/search"
)

DISCOGS_API_URL = "https://api.discogs.com"


# IMPORTANT:
# Authentication is sent in the HEADER.
# The API key is NOT placed in the URL.
HEADERS = {
    "User-Agent": "SoundOfAmericaProject/1.0",
    "Authorization": f"Discogs token={DISCOGS_API_KEY}"
}


# --------------------------------------------------
# ARTISTS STILL UNRESOLVED
# --------------------------------------------------

REMAINING_ARTISTS = {
    "Mismiths",
    "Boy Seeking Band",
    "doug.",
    "Tom Siletto",
    "Hope Darling",
    "The Rush Tribute Project",
    "Yacht Rock Revue",
    "Zach John King",
    "The Marble Creek Loops",
    "The Jess Novak Band"
}


# --------------------------------------------------
# NAME NORMALIZATION
# --------------------------------------------------

def normalize_name(name):
    """
    Normalize artist names so harmless differences in
    capitalization and punctuation do not prevent a match.
    """

    name = name.lower().strip()

    # Remove Discogs disambiguation numbers such as Artist (2)
    name = re.sub(r"\s*\(\d+\)$", "", name)

    # Keep letters and numbers only
    name = re.sub(r"[^a-z0-9]+", "", name)

    return name


# --------------------------------------------------
# LOAD ARTISTS
# --------------------------------------------------

artists_to_test = []

with open(
    MISSING_FILE,
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        if row["name"] in REMAINING_ARTISTS:

            artists_to_test.append({
                "name": row["name"],
                "mbid": row["mbid"]
            })


# --------------------------------------------------
# FIND VERIFIED DISCOGS ARTIST
# --------------------------------------------------

def find_discogs_artist(name):
    """
    Search Discogs specifically for ARTIST records.

    Only accept a result when its normalized artist name
    exactly matches our target artist name.
    """

    params = {
        "q": name,
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

    data = response.json()

    target_name = normalize_name(name)

    for result in data.get("results", []):

        discogs_name = result.get("title", "")

        if normalize_name(discogs_name) == target_name:

            return {
                "id": result.get("id"),
                "name": discogs_name
            }

    return None


# --------------------------------------------------
# GET VERIFIED ARTIST RELEASES
# --------------------------------------------------

def get_artist_genres(artist_id):
    """
    Retrieve releases associated with the verified
    Discogs artist ID.

    Then retrieve individual release records and collect
    their genres and styles.
    """

    releases_url = (
        f"{DISCOGS_API_URL}/artists/"
        f"{artist_id}/releases"
    )

    params = {
        "sort": "year",
        "sort_order": "desc",
        "per_page": 5
    }

    response = requests.get(
        releases_url,
        params=params,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    release_data = response.json()

    genres = []
    styles = []

    releases_checked = 0

    for release in release_data.get("releases", []):

        # We want actual releases, not unrelated entries
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

            # Three verified releases are enough for this test
            if releases_checked >= 3:
                break

            time.sleep(1)

        except requests.exceptions.RequestException:
            continue

    return genres, styles, releases_checked


# --------------------------------------------------
# RUN TEST
# --------------------------------------------------

print("\nDISCOGS VERIFIED GENRE RESCUE TEST\n")

rescued = 0
no_artist_match = 0
no_genre_data = 0
errors = 0

rescued_artists = []
unresolved_artists = []


for i, artist in enumerate(
    artists_to_test,
    start=1
):

    name = artist["name"]

    try:

        discogs_artist = find_discogs_artist(name)

        # ------------------------------------------
        # No exact artist identity match
        # ------------------------------------------

        if not discogs_artist:

            no_artist_match += 1
            unresolved_artists.append(name)

            print(
                f"{i:>2}/{len(artists_to_test)} "
                f"{name:<30} "
                f"NO VERIFIED ARTIST MATCH"
            )

            time.sleep(1)
            continue


        # ------------------------------------------
        # Exact artist match found
        # ------------------------------------------

        artist_id = discogs_artist["id"]
        matched_name = discogs_artist["name"]

        genres, styles, releases_checked = (
            get_artist_genres(artist_id)
        )


        # ------------------------------------------
        # Genre/style data found
        # ------------------------------------------

        if genres or styles:

            rescued += 1

            rescued_artists.append({
                "name": name,
                "discogs_name": matched_name,
                "artist_id": artist_id,
                "genres": genres,
                "styles": styles,
                "releases_checked": releases_checked
            })

            print(
                f"{i:>2}/{len(artists_to_test)} "
                f"{name:<30} "
                f"VERIFIED -> {matched_name} | "
                f"genres={genres} | "
                f"styles={styles}"
            )


        # ------------------------------------------
        # Artist exists but no genre/style found
        # ------------------------------------------

        else:

            no_genre_data += 1
            unresolved_artists.append(name)

            print(
                f"{i:>2}/{len(artists_to_test)} "
                f"{name:<30} "
                f"VERIFIED ARTIST — NO GENRE DATA"
            )


    except requests.exceptions.RequestException as error:

        errors += 1
        unresolved_artists.append(name)

        # Authentication remains in headers,
        # so the API key should not appear in this URL.
        print(
            f"{i:>2}/{len(artists_to_test)} "
            f"{name:<30} "
            f"ERROR -> {error}"
        )


    time.sleep(1)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\n-----------------------------------")
print("DISCOGS VERIFIED RESCUE SUMMARY")
print("-----------------------------------")

print(
    f"Artists tested: "
    f"{len(artists_to_test)}"
)

print(
    f"Verified genre rescues: "
    f"{rescued}"
)

print(
    f"No verified artist match: "
    f"{no_artist_match}"
)

print(
    f"Verified artist but no genre data: "
    f"{no_genre_data}"
)

print(
    f"Errors: "
    f"{errors}"
)


if artists_to_test:

    rescue_rate = (
        rescued
        / len(artists_to_test)
        * 100
    )

    print(
        f"Verified rescue rate: "
        f"{rescue_rate:.1f}%"
    )


# --------------------------------------------------
# SUCCESSFUL RESCUES
# --------------------------------------------------

print("\nSuccessful VERIFIED rescues:")

for artist in rescued_artists:

    print(
        f"- {artist['name']} "
        f"-> Discogs: {artist['discogs_name']} "
        f"(Artist ID {artist['artist_id']})"
    )

    print(
        f"  Genres: "
        f"{artist['genres']}"
    )

    print(
        f"  Styles: "
        f"{artist['styles']}"
    )

    print(
        f"  Releases checked: "
        f"{artist['releases_checked']}"
    )


# --------------------------------------------------
# STILL UNRESOLVED
# --------------------------------------------------

print("\nStill unresolved:")

for name in unresolved_artists:

    print(f"- {name}")