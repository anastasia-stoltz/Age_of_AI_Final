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

# Pull a manageable sample of recent U.S. setlists
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
        print("Setlist.fm rate limited — waiting...")
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


print("\nTesting MusicBrainz genre coverage...\n")

with_genre = 0
with_tags_only = 0
with_nothing = 0

examples_missing = []

for i, (mbid, name) in enumerate(artists.items(), start=1):

    url = f"https://musicbrainz.org/ws/2/artist/{mbid}"

    params = {
        "inc": "genres+tags",
        "fmt": "json"
    }

    response = requests.get(
        url,
        params=params,
        headers=MB_HEADERS,
        timeout=30
    )

    if response.status_code != 200:
        print(f"{name}: MusicBrainz error {response.status_code}")
        time.sleep(1.1)
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

        if len(examples_missing) < 10:
            examples_missing.append(name)

    print(
        f"{i:>3}/200  "
        f"{name[:30]:<30}  "
        f"genres={len(genres):>2}  tags={len(tags):>2}"
    )

    time.sleep(1.1)


total_tested = with_genre + with_tags_only + with_nothing

print("\n-----------------------------")
print("GENRE COVERAGE SUMMARY")
print("-----------------------------")

print(f"Artists tested: {total_tested}")
print(f"Artists with formal genre data: {with_genre}")
print(f"Artists with tags but no genre: {with_tags_only}")
print(f"Artists with neither: {with_nothing}")

if total_tested:
    usable = with_genre + with_tags_only

    print(
        f"Formal genre coverage: "
        f"{with_genre / total_tested * 100:.1f}%"
    )

    print(
        f"Genre-or-tag coverage: "
        f"{usable / total_tested * 100:.1f}%"
    )

print("\nExamples with no genre or tags:")
for artist in examples_missing:
    print("-", artist)
    