from pathlib import Path
import sys

TESTS_DIR = Path(__file__).resolve().parent
APP_DIR = TESTS_DIR.parent
sys.path.append(str(APP_DIR))

from apis.discogs_api import get_discogs_genre


TEST_ARTISTS = [
    "Yacht Rock Revue",
    "The Rush Tribute Project",
    "Boy Seeking Band"
]


print("\nDISCOGS API MODULE SMOKE TEST\n")

for artist_name in TEST_ARTISTS:

    genre, reason = get_discogs_genre(
        artist_name
    )

    print(
        f"{artist_name:<30} "
        f"genre={genre:<20} "
        f"reason={reason}"
    )