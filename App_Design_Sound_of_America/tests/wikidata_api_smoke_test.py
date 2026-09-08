from pathlib import Path
import sys

# Allow test to import modules from App_Design_Sound_of_America
TESTS_DIR = Path(__file__).resolve().parent
APP_DIR = TESTS_DIR.parent
sys.path.append(str(APP_DIR))

from apis.wikidata_api import get_wikidata_genre


TEST_ARTISTS = [
    {
        "name": "Chad Gray",
        "mbid": "7c89e6f2-5e39-450b-bce6-0b9bfe68d732"
    },
    {
        "name": "Alice Bag",
        "mbid": "ddd2d0bf-4fa7-4fa1-995b-46ed4d689c0b"
    }
]


print("\nWIKIDATA API MODULE SMOKE TEST\n")

for artist in TEST_ARTISTS:

    genre, reason = get_wikidata_genre(
        artist["mbid"]
    )

    print(
        f"{artist['name']:<20} "
        f"genre={genre:<25} "
        f"reason={reason}"
    )