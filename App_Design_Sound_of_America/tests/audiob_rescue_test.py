import csv
import time
import requests
from pathlib import Path


# --------------------------------------------------
# PATHS
# --------------------------------------------------

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent.parent

MISSING_FILE = PROJECT_ROOT / "missing_genre_artists.csv"


# --------------------------------------------------
# THEAUDIODB SETTINGS
# --------------------------------------------------

# TheAudioDB currently provides "123" as its public free v1 API key.
AUDIODB_API_KEY = "123"

AUDIODB_BASE_URL = (
    f"https://www.theaudiodb.com/api/v1/json/"
    f"{AUDIODB_API_KEY}/artist-mb.php"
)


# --------------------------------------------------
# ARTISTS STILL UNRESOLVED AFTER
# MUSICBRAINZ + LAST.FM + WIKIDATA
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
# LOAD MBIDS FROM ORIGINAL MISSING-ARTIST CSV
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


print("\nTHEAUDIODB GENRE RESCUE TEST\n")

print(
    f"Remaining artists found in CSV: "
    f"{len(artists_to_test)}"
)

print()


# --------------------------------------------------
# RUN TEST
# --------------------------------------------------

rescued = 0
still_missing = 0
errors = 0

rescued_artists = []
still_missing_artists = []


for i, artist in enumerate(artists_to_test, start=1):

    name = artist["name"]
    mbid = artist["mbid"]

    try:

        response = requests.get(
            AUDIODB_BASE_URL,
            params={"i": mbid},
            timeout=30
        )

        # Handle free-tier rate limiting
        if response.status_code == 429:

            print(
                f"{i:>2}/{len(artists_to_test)} "
                f"{name:<30} "
                f"RATE LIMITED — waiting 60 seconds..."
            )

            time.sleep(60)

            response = requests.get(
                AUDIODB_BASE_URL,
                params={"i": mbid},
                timeout=30
            )

        response.raise_for_status()

        data = response.json()

        artists = data.get("artists")

        # No artist found for this exact MBID
        if not artists:

            still_missing += 1
            still_missing_artists.append(name)

            print(
                f"{i:>2}/{len(artists_to_test)} "
                f"{name:<30} "
                f"NO MATCH"
            )

            time.sleep(2.1)
            continue

        result = artists[0]

        audiodb_name = result.get("strArtist")
        genre = result.get("strGenre")
        style = result.get("strStyle")

        # Clean empty strings / None
        genre = genre.strip() if genre else ""
        style = style.strip() if style else ""

        if genre or style:

            rescued += 1

            rescued_artists.append({
                "name": name,
                "audiodb_name": audiodb_name,
                "genre": genre,
                "style": style
            })

            print(
                f"{i:>2}/{len(artists_to_test)} "
                f"{name:<30} "
                f"RESCUED -> "
                f"genre={genre or 'None'} | "
                f"style={style or 'None'}"
            )

        else:

            still_missing += 1
            still_missing_artists.append(name)

            print(
                f"{i:>2}/{len(artists_to_test)} "
                f"{name:<30} "
                f"MATCH FOUND — NO GENRE/STYLE"
            )

    except requests.exceptions.RequestException as error:

        errors += 1

        print(
            f"{i:>2}/{len(artists_to_test)} "
            f"{name:<30} "
            f"ERROR -> {error}"
        )

    # Free tier is 30 requests/minute.
    # 2.1 seconds keeps us safely underneath that.
    time.sleep(2.1)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\n-----------------------------")
print("THEAUDIODB RESCUE SUMMARY")
print("-----------------------------")

print(f"Artists tested: {len(artists_to_test)}")
print(f"Artists rescued: {rescued}")
print(f"Still missing: {still_missing}")
print(f"Errors: {errors}")

if artists_to_test:

    rescue_rate = (
        rescued
        / len(artists_to_test)
        * 100
    )

    print(
        f"Rescue rate: "
        f"{rescue_rate:.1f}%"
    )


print("\nSuccessful rescues:")

for artist in rescued_artists:

    print(
        f"- {artist['name']}: "
        f"genre={artist['genre'] or 'None'}, "
        f"style={artist['style'] or 'None'}"
    )


print("\nStill unresolved:")

for artist in still_missing_artists:

    print(f"- {artist}")