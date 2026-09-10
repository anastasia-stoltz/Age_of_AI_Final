# The Sound of America

**The Sound of America** is a multi-page Dash application that explores how American popular music changes across **place, time, and legacy**. The project combines documented live-performance data with historical Billboard chart data so users can explore where genres appear in live-music samples, how long hit songs remain on the charts, and which artists demonstrate the strongest long-term chart presence.

## Project Question

**How does American music change across place, time, and artists?**

The dashboard approaches that question through three connected views:

1. **Place — Music Across America:** How does the genre mix of documented live music differ across U.S. states, and how does it change by year?
2. **Time — Lifespan of a Hit:** How has the amount of time a Billboard Hot 100 hit remains on the chart changed across eras?
3. **Legacy — Artist Staying Power:** Which artists demonstrate the strongest long-term chart presence when success is measured across multiple dimensions?

## Audience and Value

The dashboard is designed for **music fans and data-curious listeners who want to explore patterns in American popular music without working directly with raw music-industry datasets**. Instead of presenting one static analysis, the app lets users change genres, years, comparison periods, and ranking measures to investigate the data themselves.

## Live App

**Render:** https://age-of-ai-final.onrender.com

**GitHub repository:** https://github.com/anastasia-stoltz/Age_of_AI_Final

## Team

**Team One**

- Christian Fannell
- Tracy Frey
- Sean McElwain
- Anastasia Stoltz

### Team Contributions

The project was completed collaboratively across several workstreams:

- Home page, navigation, shared visual design, app integration, and deployment;
- Setlist.fm data collection, genre enrichment, and Music Across America development;
- Lifespan of a Hit analysis and page development;
- Artist Staying Power analysis and page development;
- testing, documentation, poster preparation, and final quality assurance.

## Application Pages

### Home

The landing page introduces the project as an interactive music atlas and organizes the app around three perspectives: **Place, Time, and Legacy**. It connects the three analyses into one shared story and provides navigation to each interactive page.

### Music Across America

This page uses prepared Setlist.fm data to show how the genre mix within the collected sample differs across U.S. states.

Users can:

- select a broad music genre;
- move across available years with a year slider;
- compare within-state genre shares on a U.S. choropleth;
- hover over states to inspect the selected genre's share and sample counts;
- click a state to view its leading genre categories in a state sound profile.

Darker gold means the selected genre accounts for a larger share of that state's genre-identified setlists in the chosen year.

The prepared data cover 2022–2026**. Because 2026 is a partial year, the page defaults to the most recent complete year when 2026 is present. State/year samples are relatively small, so individual percentages should be interpreted as suggestive rather than statistically precise.

The map should **not** be interpreted as a complete census of concerts or as a measure of listener preference.

### Lifespan of a Hit

This page compares historical Billboard Hot 100 chart behavior across selected benchmark years. The implementation samples three comparable chart weeks — April, July, and October — for each benchmark year from **1985 through 2025**.

Users choose two years and the page updates:

- average weeks on the Hot 100;
- average weeks on chart for songs currently occupying the Top 10;
- average number of unique artists represented;
- a historical hit-lifespan trend chart;
- an artist-variety trend chart;
- a written comparison generated from the selected years.

Because the page samples three weeks per benchmark year rather than every weekly chart, its findings should be interpreted as patterns in the selected comparable samples rather than a complete census of every Hot 100 week.

### Artist Staying Power

This page aggregates historical Billboard Hot 100 performance by artist and allows users to change both the **ranking measure** and the **number of artists displayed**.

Available measures include:

- Staying Power Score;
- distinct charting songs;
- total chart weeks;
- Top 10 hits;
- number-one hits;
- career span in years.

Artists with only one charting song are excluded so the ranking focuses on repeated chart presence.

The project-created Staying Power Score is:

```text
Staying Power Score =
    1.5 × Distinct Charting Songs
  + 0.35 × Total Chart Weeks
  + 4 × Top 10 Hits
  + 5 × Number-One Hits
  + 1.2 × Career Span in Years
```

This is a team-designed composite measure, not an official Billboard metric. Its weights are analytical choices and are shown in the dashboard so users can understand how the score is constructed.

## Key Findings

### Place — Music Across America

The sampled live-music data show that genre mix varies meaningfully across states rather than following one uniform national pattern. The state profile interaction makes those differences visible, while the page's sample-size note makes clear that individual state percentages are exploratory rather than population-level estimates.

### Time — Lifespan of a Hit

Songs occupying the Billboard Hot 100 Top 10 in 2025 had been on the chart for an average of 32.57 weeks, compared with 10.93 weeks in 1990 — nearly three times longer.

Across the same comparison, the average number of unique artists appearing in the sampled Hot 100 charts fell from 91.0 to 71.33, a decrease of approximately 21.6%.

### Legacy — Staying Power

Under the dashboard's composite Staying Power Score, Taylor Swift ranks first at 685.4, followed by Madonna at 615.9 and The Beatles at 568.9. Because the score combines chart volume, longevity, Top 10 hits, number-one hits, and career span, it rewards sustained chart presence rather than a single peak.

## Data Sources

### 1. Setlist.fm

- **Use in project:** documented live-performance geography and setlists by state/year.
- **Source:** https://api.setlist.fm/docs/
- **Format:** REST API returning JSON during data collection; prepared CSV used by the dashboard.
- **Dashboard file:** `App_Design_Sound_of_America/data/concert_map_data_setlistfm.csv`
- **Important limitation:** Setlist.fm is crowd-sourced. The data represent documented records rather than every concert that occurred.

### 2. MusicBrainz and Genre-Enrichment Sources

Artist genre information used in the map-preparation workflow was enriched through several metadata sources where available:

- MusicBrainz: https://musicbrainz.org/doc/MusicBrainz_API
- Last.fm API: https://www.last.fm/api
- Wikidata SPARQL: https://query.wikidata.org/
- Discogs API: https://www.discogs.com/developers

Detailed genre labels are grouped into broader dashboard categories so the map remains readable. Artists whose genre could not be resolved are not treated as a known genre when the page calculates the displayed genre shares.

### 3. Billboard Hot 100 JSON Archive

- **Use in project:** Lifespan of a Hit.
- **Source used in code:** https://github.com/mhollingshead/billboard-hot-100
- **Format:** JSON files retrieved programmatically with requests.
- **Analysis period:** benchmark years from 1985–2025 using three comparable chart dates per year.

### 4. Billboard Hot 100 Historical CSV

- **Use in project:** Artist Staying Power.
- **Dataset:** Billboard Hot 100 history compiled by Sean Miller / data.world.
- **Dashboard file:** App_Design_Sound_of_America/data/Hot_Stuff.csv
- **Coverage used by the page:** 1958–2021.
- **Attribution stated in code:** CC BY-SA.

## Data Cleaning and Transformation

The project performs several transformations before visualization:

- strips and standardizes artist names where needed;
- converts Billboard chart dates to usable year fields;
- aggregates weekly Billboard observations to song-level records for Staying Power;
- aggregates song-level records to artist-level measures;
- normalizes detailed artist genre labels into broader map categories;
- uses fallback metadata sources when primary genre information is unavailable;
- excludes unresolved/uncategorized genre records from the denominator used for the displayed genre-share map;
- aggregates state/year/genre records before visualization;
- caches repeated Billboard JSON requests during an app session;
- includes safeguards for empty map selections and state/year combinations.

## Data Dictionary

### `concert_map_data_setlistfm.csv`

| Variable | Type | Description |
|---|---|---|
| `year` | Integer | Year associated with the documented live-performance records. |
| `state` | String | Two-letter U.S. state code used by the choropleth. |
| `genre` | String | Genre label used by the dashboard filter. |
| `genre_detailed` | String | More specific genre/tag retained from the enrichment process. |
| `event_count` | Integer | Number of sampled documented records associated with that grouping. |

### `Hot_Stuff.csv` — fields used by Staying Power

| Variable | Description |
| `Performer` | Artist/performer name. |
| `SongID` | Song identifier in the historical dataset. |
| `Song` | Song title. |
| `WeekID` | Weekly chart date. |
| `Peak Position` | Best chart position achieved by the song. |
| `Weeks on Chart` | Number of Hot 100 weeks recorded for the song observation. |

The Staying Power page transforms these fields into artist-level measures including distinct songs, total chart weeks, Top 10 hits, number-one hits, first/last chart year, career span, and the custom Staying Power Score.

### Billboard JSON — fields used by Lifespan of a Hit

| Variable | Description |
| `date` | Billboard chart date. |
| `artist` | Artist credited on the chart entry. |
| `weeks_on_chart` | Number of weeks the song has appeared on the Hot 100 as of that chart date. |

The analysis also uses chart order to identify the songs occupying the Top 10 in each sampled week.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/anastasia-stoltz/Age_of_AI_Final.git
cd Age_of_AI_Final/App_Design_Sound_of_America
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

Open the local address shown in the terminal, normally:

```text
http://127.0.0.1:8050/
```

## Environment Variables

The committed dashboard can run from the prepared data files without exposing API credentials. API keys used to regenerate or enrich data should be stored in a local `.env` file or as deployment environment variables and **must not be committed to GitHub**.

Development variables used by the data-collection/enrichment workflow may include:

```text
LASTFM_API_KEY=...
DISCOGS_API_KEY=...
SETLISTFM_API_KEY=...
BILLBOARD_CSV_PATH=...   # optional path override for Staying Power
```

`.env`, `__pycache__/`, and `*.pyc` are excluded by `.gitignore`.

## Requirements

The pinned dependencies are stored in:

`App_Design_Sound_of_America/requirements.txt`

They include:

- Dash
- Dash Bootstrap Components
- gunicorn
- pandas
- Plotly
- python-dotenv
- requests

## Testing and Validation

The repository includes development tests and validation scripts for:

- Billboard data behavior;
- enrichment-pipeline smoke testing;
- genre coverage;
- state coverage;
- Wikidata fallback/rescue logic.

The final app was also reviewed through manual interaction testing, including page navigation, dropdown/slider changes, map updates, state-click behavior, chart rendering, file paths, and deployment behavior.

## Render Deployment

The project is configured as a Render Web Service.

- **Live app:** https://age-of-ai-final.onrender.com
- **Branch:** `main`
- **Root Directory:** `App_Design_Sound_of_America`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:server --bind 0.0.0.0:$PORT`

`app.py` exposes the Flask server through:

```python
server = app.server
```

## Known Limitations

- **Setlist.fm coverage is incomplete and crowd-sourced.** The map represents documented setlists, not every live performance that occurred.
- **State/year samples are small.** A small number of documented performances can move a state's genre share substantially.
- **Genre classification is imperfect.** Some artists have missing, ambiguous, or multiple genre labels.
- **Broad genre categories simplify musical complexity.** They are useful for mapping but should not be interpreted as definitive artist identities.
- **Lifespan of a Hit samples three chart weeks per benchmark year.** It does not analyze every weekly Hot 100 chart between 1985 and 2025.
- **The Staying Power Score is a custom index.** Its weights are team choices rather than an industry-standard measure.
- **Historical Billboard coverage differs between pages.** Staying Power currently uses the historical CSV through 2021, while Lifespan of a Hit retrieves selected chart dates through 2026.

## AI Assistance

Generative AI was used as an assistive tool for selected design, debugging, data-interpretation review, documentation, and deployment tasks. AI output was reviewed, edited, tested, and either incorporated or discarded by the team.

See AI_USAGE.md for the tools used, representative high-level prompts, where AI assistance was applied, and how outputs were verified.

## Future Improvements

Possible extensions include:

- expand and refresh the live-music sample;
- improve genre-classification coverage and validation;
- analyze a more complete set of historical Billboard chart weeks;
- investigate factors that may be associated with longer modern chart lifespans;
- allow users to adjust the Staying Power Score weights as a scenario-analysis feature.

## Attribution

This project is an academic, non-commercial student project. Data and metadata remain subject to the terms and licenses of their original sources. The dashboard retains source attribution and describes important limitations so results are interpreted in the context of the underlying data.
