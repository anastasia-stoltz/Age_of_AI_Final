from pathlib import Path
import sys

TESTS_DIR = Path(__file__).resolve().parent
APP_DIR = TESTS_DIR.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from apis.lastfm_api import get_lastfm_genre
from apis.wikidata_api import get_wikidata_genre
from apis.discogs_api import get_discogs_genre


TEST_ARTISTS = [
    {
        "name": "DJ Moon",
        "mbid": "2ed27ddf-8e93-4819-9aee-2eb5d2b9e3a0"
    },
    {
        "name": "Chad Gray",
        "mbid": "7c89e6f2-5e39-450b-bce6-0b9bfe68d732"
    },
    {
        "name": "Yacht Rock Revue",
        "mbid": "56241616-665f-4f02-ba23-67ded8b1bdf9"
    },
    {
        "name": "Boy Seeking Band",
        "mbid": "3b4e83c4-bbd2-4d3c-bf81-b5aafe047767"
    }
]


def resolve_test_genre(name, mbid):
    """
    Test the fallback sequence for artists already known
    to be unresolved by MusicBrainz.
    """

    # 1. Last.fm
    genre, reason = get_lastfm_genre(
        artist_name=name,
        mbid=mbid
    )

    if genre != "unknown":
        return genre, "lastfm"

    # 2. Wikidata
    if mbid:
        genre, reason = get_wikidata_genre(mbid)

        if genre != "unknown":
            return genre, "wikidata"

    # 3. Discogs
    genre, reason = get_discogs_genre(name)

    if genre != "unknown":
        return genre, "discogs"

    # 4. Still unresolved
    return "unknown", "unknown"


print("\nMULTI-SOURCE ENRICHMENT PIPELINE SMOKE TEST\n")

for artist in TEST_ARTISTS:

    genre, source = resolve_test_genre(
        artist["name"],
        artist["mbid"]
    )

    print(
        f"{artist['name']:<25} "
        f"genre={genre:<20} "
        f"source={source}"
    )