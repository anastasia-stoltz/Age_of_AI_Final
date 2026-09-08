from pathlib import Path
import sys

# Let this test import from App_Design_Sound_of_America/apis
TESTS_DIR = Path(__file__).resolve().parent
APP_DIR = TESTS_DIR.parent
sys.path.append(str(APP_DIR))

from apis.lastfm_api import get_lastfm_genre


TEST_ARTISTS = [
    {
        "name": "DJ Moon",
        "mbid": "2ed27ddf-8e93-4819-9aee-2eb5d2b9e3a0"
    },
    {
        "name": "Alice Bag",
        "mbid": "ddd20ebf-4fa7-4fa1-995b-46ed4d689c0b"
    },
    {
        "name": "Mismiths",
        "mbid": "d819acaa-9ca3-4de6-b462-dc2f843548a8"
    }
]


print("\nLAST.FM API MODULE SMOKE TEST\n")

for artist in TEST_ARTISTS:

    genre, reason = get_lastfm_genre(
        artist_name=artist["name"],
        mbid=artist["mbid"]
    )

    print(
        f"{artist['name']:<20} "
        f"genre={genre:<20} "
        f"reason={reason}"
    )