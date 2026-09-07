import csv
import time
import requests
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent

MISSING_FILE = TESTS_DIR / "missing_genre_artists.csv"

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

HEADERS = {
    "User-Agent": "SoundOfAmericaProject/1.0 (student project)"
}


def get_wikidata_genres_by_mbid(mbid):
    """
    Find a Wikidata artist by exact MusicBrainz artist ID (P434)
    and return its genre labels (P136).
    """

    query = f"""
    SELECT ?artist ?artistLabel ?genreLabel
    WHERE {{
      ?artist wdt:P434 "{mbid}" .
      OPTIONAL {{
        ?artist wdt:P136 ?genre .
      }}

      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
      }}
    }}
    """

    response = requests.get(
        WIKIDATA_SPARQL_URL,
        params={
            "query": query,
            "format": "json"
        },
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    rows = (
        response.json()
        .get("results", {})
        .get("bindings", [])
    )

    if not rows:
        return None, []

    artist_label = rows[0].get(
        "artistLabel", {}
    ).get("value")

    genres = []

    for row in rows:
        genre = row.get(
            "genreLabel", {}
        ).get("value")

        if genre and genre not in genres:
            genres.append(genre)

    return artist_label, genres


missing_artists = []

with open(
    MISSING_FILE,
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        missing_artists.append(row)


print("\nWIKIDATA MBID RESCUE TEST\n")

rescued = 0
still_missing = 0
errors = 0

for i, row in enumerate(missing_artists, start=1):

    name = row["name"]
    mbid = row["mbid"]

    try:
        wikidata_name, genres = get_wikidata_genres_by_mbid(mbid)

        if genres:
            rescued += 1

            print(
                f"{i:>2}/{len(missing_artists)} "
                f"{name:<30} "
                f"RESCUED -> {genres}"
            )

        else:
            still_missing += 1

            print(
                f"{i:>2}/{len(missing_artists)} "
                f"{name:<30} "
                f"NO GENRE"
            )

    except requests.exceptions.RequestException as error:
        errors += 1

        print(
            f"{i:>2}/{len(missing_artists)} "
            f"{name:<30} "
            f"ERROR -> {error}"
        )

    time.sleep(1)


print("\n-----------------------------")
print("WIKIDATA MBID RESCUE SUMMARY")
print("-----------------------------")

print(f"Artists tested: {len(missing_artists)}")
print(f"Genres rescued: {rescued}")
print(f"Still missing: {still_missing}")
print(f"Errors: {errors}")

if missing_artists:
    rescue_pct = (
        rescued
        / len(missing_artists)
        * 100
    )

    print(
        f"Rescue rate: {rescue_pct:.1f}%"
    )