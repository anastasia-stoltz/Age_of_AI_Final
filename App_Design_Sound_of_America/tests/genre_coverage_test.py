import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

SETLISTFM_API_KEY = os.getenv("SETLISTFM_API_KEY")

if not SETLISTFM_API_KEY:
    raise ValueError("SETLISTFM_API_KEY not found in .env")

SETLIST_URL = "https://api.setlist.fm/rest/1.0/search/setlists"

SETLIST_HEADERS = {
    "Accept": "application/json",
    "x-api-key": SETLISTFM_API_KEY
}

MB_HEADERS = {
    "User-Agent": "SoundOfAmericaProject/1.0 (student project)"
}


# --------------------------------------------------
# STEP 1: COLLECT 200 UNIQUE ARTISTS FROM SETLIST.FM
# --------------------------------------------------

artists = {}
page = 1

while len(artists) < 200:

    params = {
        "countryCode": "US",
        "p": page
    }

    response = requests.get(
        SETLIST_URL,
        headers=SETLIST_HEADERS,
        params=params,
        timeout=30
    )

    if response.status_code == 429:
        print("Setlist.fm rate limited — waiting 5 seconds...")
        time.sleep(5)
        continue

    response.raise_for_status()

    data = response.json()

    for item in data.get("setlist", []):
        artist = item.get("artist", {})
        mbid = artist.get("mbid")
        name = artist.get("name")

        if mbid and mbid not in artists:
            artists[mbid] = name

        if len(artists) >= 200:
            break

    print(f"Unique artists collected: {len(artists)}")

    page += 1
    time.sleep(1)


# --------------------------------------------------
# STEP 2: TEST MUSICBRAINZ GENRE COVERAGE
# --------------------------------------------------

print("\nTesting MusicBrainz genre coverage...\n")

with_genre = 0
with_tags_only = 0
with_nothing = 0
api_errors = 0

examples_missing = []
missing_artists = []
error_artists = []

for i, (mbid, name) in enumerate(artists.items(), start=1):

    url = f"https://musicbrainz.org/ws/2/artist/{mbid}"

    params = {
        "inc": "genres+tags",
        "fmt": "json"
    }

    success = False

    # Retry each artist up to 3 times
    for attempt in range(1, 4):

        try:
            response = requests.get(
                url,
                params=params,
                headers=MB_HEADERS,
                timeout=30
            )

            if response.status_code == 200:
                success = True
                break

            elif response.status_code == 503:
                print(
                    f"{name}: 503 on attempt {attempt} — retrying..."
                )
                time.sleep(3)

            elif response.status_code == 404:
                print(f"{name}: MusicBrainz 404")
                break

            else:
                print(
                    f"{name}: MusicBrainz error "
                    f"{response.status_code}"
                )
                break

        except requests.exceptions.RequestException as error:
            print(
                f"{name}: connection error on attempt "
                f"{attempt} — retrying..."
            )
            print(f"  {error}")
            time.sleep(3)

    # If all attempts fail, count separately from missing metadata
    if not success:
        api_errors += 1
        error_artists.append(name)

        time.sleep(1.2)
        continue

    artist_data = response.json()

    genres = artist_data.get("genres", [])
    tags = artist_data.get("tags", [])

    if genres:
        with_genre += 1

    elif tags:
        with_tags_only += 1

    else:
        with_nothing += 1
        missing_artists.append({
            "name": name,
            "mbid": mbid
        })

        if len(examples_missing) < 10:
            examples_missing.append(name)

    print(
        f"{i:>3}/200  "
        f"{name[:30]:<30}  "
        f"genres={len(genres):>2}  "
        f"tags={len(tags):>2}"
    )

    # Respect MusicBrainz rate limits
    time.sleep(1.2)


# --------------------------------------------------
# STEP 3: SUMMARY
# --------------------------------------------------

successful_responses = (
    with_genre
    + with_tags_only
    + with_nothing
)

total_sample = len(artists)

print("\n-----------------------------")
print("GENRE COVERAGE SUMMARY")
print("-----------------------------")

print(f"Artists sampled: {total_sample}")
print(f"Successful MusicBrainz responses: {successful_responses}")
print(f"API errors after retries: {api_errors}")

print(f"\nArtists with formal genre data: {with_genre}")
print(f"Artists with tags but no genre: {with_tags_only}")
print(f"Artists with neither: {with_nothing}")

if successful_responses > 0:

    formal_genre_pct = (
        with_genre
        / successful_responses
        * 100
    )

    usable_pct = (
        (with_genre + with_tags_only)
        / successful_responses
        * 100
    )

    missing_pct = (
        with_nothing
        / successful_responses
        * 100
    )

    print(
        f"\nFormal genre coverage "
        f"(successful responses only): "
        f"{formal_genre_pct:.1f}%"
    )

    print(
        f"Genre-or-tag coverage "
        f"(successful responses only): "
        f"{usable_pct:.1f}%"
    )

    print(
        f"True missing metadata "
        f"(successful responses only): "
        f"{missing_pct:.1f}%"
    )

if total_sample > 0:

    error_pct = (
        api_errors
        / total_sample
        * 100
    )

    print(
        f"API error rate after retries: "
        f"{error_pct:.1f}%"
    )

print("\nExamples with no genre or tags:")
for artist in examples_missing:
    print("-", artist)

print("\nArtists that still failed after retries:")
for artist in error_artists:
    print("-", artist)


# --------------------------------------------------
# STEP 4: SAVE TRUE MISSING ARTISTS FOR FALLBACK TEST
# --------------------------------------------------

if missing_artists:
    import csv

    with open(
        "missing_genre_artists.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["name", "mbid"]
        )

        writer.writeheader()
        writer.writerows(missing_artists)

    print(
        "\nSaved artists with no MusicBrainz genre/tags to "
        "missing_genre_artists.csv"
    )