import os
import requests
from pathlib import Path
from dotenv import load_dotenv


# --------------------------------------------------
# LOAD PRIVATE .ENV
# --------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ASSIGNMENT_DIR = REPO_ROOT.parent

PRIVATE_ENV_PATH = ASSIGNMENT_DIR / "soundofmusic" / ".env"

load_dotenv()

if PRIVATE_ENV_PATH.exists():
    load_dotenv(PRIVATE_ENV_PATH, override=False)


SETLISTFM_API_KEY = os.getenv("SETLISTFM_API_KEY")

if not SETLISTFM_API_KEY:
    raise ValueError("SETLISTFM_API_KEY not found.")


# --------------------------------------------------
# TEST QUERY
# --------------------------------------------------

url = "https://api.setlist.fm/rest/1.0/search/setlists"

headers = {
    "Accept": "application/json",
    "x-api-key": SETLISTFM_API_KEY
}

params = {
    "countryCode": "US",
    "stateCode": "CA",
    "year": 2025,
    "p": 1
}


response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30
)

response.raise_for_status()

data = response.json()


print("\nSETLIST.FM TOTAL TEST")
print("-----------------------------")
print(f"California, 2025")
print(f"total: {data.get('total')}")
print(f"itemsPerPage: {data.get('itemsPerPage')}")
print(f"page: {data.get('page')}")