import requests


# --------------------------------------------------
# WIKIDATA SETTINGS
# --------------------------------------------------

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

HEADERS = {
    "User-Agent": "SoundOfAmericaProject/1.0"
}


# --------------------------------------------------
# PUBLIC GENRE LOOKUP
# --------------------------------------------------

def get_wikidata_genre(mbid):
    """
    Look up an artist in Wikidata by exact MusicBrainz artist ID.

    Returns:
        (genre, reason)

    Possible reasons:
        "found"
        "no_mbid"
        "no_genre_data"
        "lookup_failed"
    """

    if not mbid:
        return "unknown", "no_mbid"

    query = f"""
    SELECT ?artist ?genreLabel
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

    try:
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
            return "unknown", "no_genre_data"

        genres = []

        for row in rows:
            genre = (
                row.get("genreLabel", {})
                .get("value")
            )

            if genre:
                normalized = genre.strip().lower()

                if normalized not in genres:
                    genres.append(normalized)

        if genres:
            return genres[0], "found"

        return "unknown", "no_genre_data"

    except requests.RequestException as error:
        print(
            f"Wikidata lookup failed for "
            f"{mbid}: {error}"
        )

        return "unknown", "lookup_failed"