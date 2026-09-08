from pathlib import Path
import json
import pandas as pd


# --------------------------------------------------
# PATHS
# --------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

RAW_SETLISTS_FILE = REPO_ROOT / "raw_setlists_cache.csv"
ENRICHED_CACHE_FILE = REPO_ROOT / "artist_enriched_genre_cache.json"

OUTPUT_FILE = SCRIPT_DIR / "unresolved_artists_full_run.csv"


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

raw_df = pd.read_csv(
    RAW_SETLISTS_FILE,
    keep_default_na=False
)

with open(
    ENRICHED_CACHE_FILE,
    "r",
    encoding="utf-8"
) as file:
    enriched_cache = json.load(file)


# --------------------------------------------------
# LOOK UP FINAL GENRE FROM CACHE
# --------------------------------------------------

def get_cache_key(row):
    mbid = row["mbid"].strip()
    artist_name = row["artist_name"].strip()

    if mbid:
        return f"mbid::{mbid}"

    return f"name::{artist_name.lower()}"


raw_df["cache_key"] = raw_df.apply(
    get_cache_key,
    axis=1
)


def get_final_genre(cache_key):
    result = enriched_cache.get(cache_key)

    if not result:
        return "unknown"

    return result[0]


raw_df["final_genre"] = raw_df["cache_key"].apply(
    get_final_genre
)


# --------------------------------------------------
# KEEP ONLY UNRESOLVED RECORDS
# --------------------------------------------------

unknown_df = raw_df[
    raw_df["final_genre"] == "unknown"
].copy()


# --------------------------------------------------
# SUMMARIZE BY UNIQUE ARTIST
# --------------------------------------------------

unresolved_summary = (
    unknown_df
    .groupby(
        [
            "artist_name",
            "mbid"
        ],
        dropna=False
    )
    .size()
    .reset_index(
        name="unknown_records"
    )
    .sort_values(
        by="unknown_records",
        ascending=False
    )
)


# --------------------------------------------------
# SAVE OUTPUT
# --------------------------------------------------

unresolved_summary.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\n-----------------------------")
print("UNRESOLVED ARTIST SUMMARY")
print("-----------------------------")

print(
    f"Unknown records: "
    f"{len(unknown_df)}"
)

print(
    f"Unique unresolved artists: "
    f"{len(unresolved_summary)}"
)

print(
    f"\nSaved unresolved artist list to:"
)

print(
    OUTPUT_FILE
)


print("\nTop unresolved artists by record count:\n")

print(
    unresolved_summary
    .head(25)
    .to_string(index=False)
)
