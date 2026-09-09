## The Sound of America ##

The Sound of America is a multi-page Dash application that explores how American music changes across place, time, and artists. The project combines live-performance geography with historical Billboard chart data to let users explore where live music is documented, how long hit songs stay on the charts, and which artists have demonstrated the greatest long-term chart presence.

## Project Question ##

How does American music change across place, time, and artists?

The dashboard approaches that question through three connected views:

Place — Music Across America: Where are different genres of live music documented across the United States, and how does that pattern change by year?

Time — Lifespan of a Hit: How has the amount of time a Billboard Hot 100 hit remains on the chart changed across eras?

Legacy — Artist Staying Power: Which artists demonstrate the strongest long-term chart presence when success is measured across multiple dimensions?

Audience and Value

The dashboard is designed for music fans and curious users who want to explore patterns in American popular music without needing to work directly with raw music-industry datasets. Instead of presenting one static analysis, the app lets users change genres, years, comparison periods, and ranking measures to investigate the data themselves.

Live App

## Render: https://age-of-ai-final.onrender.com/

GitHub repository: https://github.com/anastasia-stoltz/Age_of_AI_Final

Team One

Christian Fannell

Tracy Frey

Sean McElwain

Anastasia Stoltz

Team Contributions

Home page, navigation, shared design, Music Across America integration, final app integration, and Render deployment: Christian Fannell, Anastasia Stoltz

Lifespan of a Hit analysis/page: Tracy Frey

Artist Staying Power analysis/page: Sean McElwain

Setlist.fm data collection and genre-enrichment pipeline: Anastasia Stoltz

Testing, documentation, poster, and final QA: Anastaia Stolz, Christian Fannell, Sean McElwain and Tracy Frey

## Application Pages

Home

The landing page introduces the project as an interactive music atlas and organizes the app around three perspectives: Place, Time, and Legacy. It also provides navigation to each analysis page and will eventually display one headline finding from each analysis.

Music Across America

This page displays an interactive U.S. choropleth based on prepared Setlist.fm concert/setlist data. Users can:

select a broad music genre;

move across available years with a year slider;

compare geographic patterns across U.S. states;

hover over states to inspect documented show counts.

The current prepared map dataset covers 2022–2026 and contains 3,539 data rows plus a header, with five fields: year, state, broad genre, detailed genre, and event count.

The map should be interpreted as a view of documented Setlist.fm activity, not as a complete census of every concert that occurred in the United States. Setlist.fm is crowd-sourced, so coverage varies by artist, location, and time.

# Current development task: before final submission, verify that rows are aggregated to one state-level value per selected broad genre and year before the choropleth is drawn.

Lifespan of a Hit

This page compares historical Billboard Hot 100 chart behavior across selected years. The current implementation samples three comparable chart weeks — April, July, and October — for each benchmark year from 1985 through 2025.

Users choose two years and the page updates:

average weeks on the Hot 100;

average weeks on chart for songs currently in the Top 10;

average number of unique artists represented;

a historical lifespan trend chart;

an artist-variety trend chart;

a written comparison generated from the selected years.

Because this page samples three weeks per benchmark year rather than every weekly chart, its findings should be described as patterns in the selected comparable samples rather than a complete census of every Hot 100 week.

Artist Staying Power

This page aggregates Billboard Hot 100 history by artist and allows users to rank artists using several measures:

Staying Power Score;

distinct charting songs;

total chart weeks;

Top 10 hits;

number-one hits;

career span in years.

Artists with only one charting song are excluded from the ranking so the page focuses on repeated chart presence rather than one-hit appearances.

The project-created Staying Power Score is:

Staying Power Score =
    1.5 × Distinct Charting Songs
  + 0.35 × Total Chart Weeks
  + 4 × Top 10 Hits
  + 5 × Number-One Hits
  + 1.2 × Career Span in Years

This is a team-designed composite measure, not an official Billboard metric. Its weights are analytical choices and should be explained as such.

Data Sources

1. Setlist.fm

Use in project: live-performance geography and documented setlists by state/year.

Source: https://api.setlist.fm/docs/

Format: REST API returning JSON during data collection; prepared CSV used by the dashboard.

Current app file: App_Design_Sound_of_America/data/concert_map_data_setlistfm.csv

Important limitation: Setlist.fm is crowd-sourced. Counts represent documented records rather than every concert that occurred.

2. MusicBrainz and Genre-Enrichment Sources

Artist genre information used in the map-preparation workflow is enriched through several sources where available:

MusicBrainz: https://musicbrainz.org/doc/MusicBrainz_API

Last.fm API: https://www.last.fm/api

Wikidata SPARQL: https://query.wikidata.org/

Discogs API: https://www.discogs.com/developers

Genres are normalized into broader categories so the map remains usable. Some artists cannot be confidently classified and may appear as Unknown or Other/Uncategorized.

3. Billboard Hot 100 JSON Archive

Use in project: Lifespan of a Hit.

Source used in code: https://github.com/mhollingshead/billboard-hot-100

Format: JSON files retrieved programmatically with requests.

Current analysis period: benchmark years from 1985–2025, using three comparable chart dates per year.

4. Billboard Hot 100 Historical CSV

Use in project: Artist Staying Power.

Dataset: Billboard Hot 100 history compiled by Sean Miller / data.world.

Current app file: App_Design_Sound_of_America/data/Hot_Stuff.csv

Coverage used by the page: 1958–2021.

Attribution stated in code: CC BY-SA.

Data Cleaning and Transformation

The project performs several transformations before visualization:

strips and standardizes artist names where needed;

converts chart dates to years;

aggregates weekly Billboard observations to song-level records for Staying Power;

aggregates song-level records to artist-level metrics;

normalizes detailed music genres into broader map categories;

retains an Unknown/Other category when genre resolution is incomplete;

uses cached web requests in the Lifespan page to avoid repeatedly downloading the same Billboard chart JSON during one app session.

# Before final submission, the team should document any additional cleaning completed after this README draft and verify key values against the underlying files.

Data Dictionary

concert_map_data_setlistfm.csv

Variable

Type

Description

year

Integer

Year of the documented live-performance records.

state

String

Two-letter U.S. state code used by the choropleth.

genre

String

Broad normalized genre category used by the dashboard filter.

genre_detailed

String

More specific genre/tag retained from the enrichment process.

event_count

Integer

Number of prepared documented events associated with that row.

Hot_Stuff.csv — fields used by Staying Power

Variable

Description

Performer

Artist/performer name.

SongID

Song identifier in the historical dataset.

Song

Song title.

WeekID

Weekly chart date.

Peak Position

Best chart position achieved by the song.

Weeks on Chart

Number of Hot 100 weeks recorded for the song observation.

The Staying Power page transforms these fields into artist-level measures including distinct songs, total chart weeks, Top 10 hits, number-one hits, first/last chart year, career span, and the custom Staying Power Score.

Billboard JSON — fields used by Lifespan of a Hit

Variable

Description

date

Billboard chart date.

artist

Artist credited on the chart entry.

weeks_on_chart

Number of weeks the song has appeared on the Hot 100 as of that chart date.

The analysis also uses chart ordering to examine the songs currently occupying the Top 10.

Project Structure

Age_of_AI_Final/
│
├── App_Design_Sound_of_America/
│   ├── apis/
│   │   ├── census_api.py
│   │   ├── discogs_api.py
│   │   ├── lastfm_api.py
│   │   ├── musicbrainz_api.py
│   │   ├── setlist_api.py
│   │   └── wikidata_api.py
│   │
│   ├── assets/
│   │   └── style.css
│   │
│   ├── data/
│   │   ├── Hot_Stuff.csv
│   │   ├── artist_enriched_genre_cache.json
│   │   ├── artist_genre_cache.json
│   │   ├── concert_map_data_setlistfm.csv
│   │   └── raw_setlists_cache.csv
│   │
│   ├── pages/
│   │   ├── home.py
│   │   ├── music_map.py
│   │   ├── anatomy_of_hit.py
│   │   └── staying_power.py
│   │
│   ├── tests/
│   │   ├── billboard_test.py
│   │   ├── enrichment_pipeline_smoke_test.py
│   │   ├── genre_coverage_test.py
│   │   ├── state_coverage_test.py
│   │   ├── wikidata_rescue_test.py
│   │   └── data_feasibility_results.txt
│   │
│   ├── app.py
│   ├── requirements.txt
│   └── .gitignore
│
├── MusicAmericaSetlistTest/
├── MusicAmericaTicketmasterTest/
├── Pitches_&_Lab_qmd/
├── .gitignore
└── README.md

Local Setup

1. Clone the repository

git clone https://github.com/anastasia-stoltz/Age_of_AI_Final.git
cd Age_of_AI_Final/App_Design_Sound_of_America

2. Create or activate a Python environment

Use your preferred Python environment. The project was developed with Python and Dash in VS Code.

3. Install dependencies

pip install -r requirements.txt

The pinned dependencies currently include Dash, Dash Bootstrap Components, pandas, Plotly, requests, python-dotenv, and gunicorn.

4. Run the app

python app.py

Open the local address shown in the terminal, normally:

http://127.0.0.1:8050/

Environment Variables

The committed dashboard can run from the prepared data files without exposing API credentials. API keys used to regenerate or enrich data should be stored in a local .env file or as deployment environment variables and must not be committed to GitHub.

Possible development variables include:

LASTFM_API_KEY=...
DISCOGS_API_KEY=...
SETLISTFM_API_KEY=...
BILLBOARD_CSV_PATH=...   # optional path override for Staying Power

Only include variables that the current data-collection workflow actually requires. .env, __pycache__/, and *.pyc are excluded by .gitignore.

Testing

The repository currently includes feasibility and coverage tests for the data pipeline, including:

Billboard data testing;

genre coverage;

state coverage;

enrichment-pipeline smoke testing;

Wikidata rescue logic.

Before final submission: [ADD THE EXACT COMMAND(S) USED TO RUN THE FINAL TEST SUITE AND THE FINAL RESULT.]

Example placeholder:

python tests/state_coverage_test.py

Render Deployment

The final project is intended to be deployed as a Render Web Service.

Use the following configuration:

Root Directory: App_Design_Sound_of_America

Branch: main

Build Command:

pip install -r requirements.txt

Start Command:

gunicorn app:server --bind 0.0.0.0:$PORT

Instance Type: Free

app.py already exposes the Flask server through:

server = app.server

Final deployment status: [ADD RENDER URL AND DATE VERIFIED]

Known Limitations

Setlist.fm coverage is incomplete and crowd-sourced. The map represents documented setlists, not every live performance that occurred.

Genre classification is imperfect. Some artists have missing, ambiguous, or multiple genre labels, requiring normalization and fallback sources.

Broad genre categories simplify musical complexity. They are useful for mapping but should not be interpreted as definitive artist identities.

Lifespan of a Hit samples three chart weeks per benchmark year. It does not analyze every weekly Hot 100 chart between 1985 and 2025.

The Staying Power Score is a custom index. Its weights are team choices rather than an industry-standard measure.

Historical Billboard coverage differs between pages. The Staying Power dataset currently ends in 2021, while the Lifespan page retrieves selected chart dates through 2025.

# [ADD ANY ADDITIONAL LIMITATION DISCOVERED DURING FINAL QA.]

# Current Final-Project Checklist

Multi-page Dash structure

Home page and shared navigation

Shared visual theme / CSS

U.S. choropleth visualization

Billboard time-series visualizations

Artist-ranking bar chart and table

External data sources

User controls on all analysis pages

requirements.txt

Basic data-pipeline tests

===============================================================
        # TO DO
================================================================  
Verify map state-level aggregation for each selected year/genre

Confirm at least 4 callback decorators across the final integrated app

Replace Home page finding placeholders with verified findings

Complete final integration and cross-page style QA

Verify every source/attribution and licensing statement

Complete AI Usage Appendix/comments

Deploy to Render and verify the public URL

Add final poster screenshots and final presentation finding

AI Assistance

Generative AI has been used as an assistant during parts of the project for tasks such as brainstorming dashboard structure, discussing layout and CSS choices, troubleshooting Dash integration, reviewing code, and drafting documentation. Team members are responsible for reviewing, editing, testing, and understanding all code and written material included in the final submission.

Before submission, add the team's complete AI-use record here or link to a separate appendix:

Tools used: ChatGPT, Claude

## AI Usage

The team usedgenerative AI tools as assistants during development.

Used for:
- brainstorming dashboard structure and page organization
- helping design the shared navigation and CSS
- troubleshooting Dash multi-page routing
- assisting with callback structure
- reviewing API integration approaches
- identifying potential data-cleaning and aggregation issues
- helping prepare deployment configuration for Render
- drafting documentation and README structure

Example high-level prompts:
- "Help us create a multi-page Dash architecture for three music analyses."
- "Explain how to create an interactive U.S. choropleth with callbacks."
- "Review this map aggregation logic for correctness."
- "Help prepare our Dash project for Render deployment."

Verification/editing:
All generated code was reviewed and edited by team members. The team ran the application locally, checked calculations against the underlying data, and modified generated code and text to fit the project's requirements and design.

Uses: layout/design brainstorming, Dash multi-page structure, navigation setup, callback planning, debugging, API/data integration guidance, aggregation and logic review, Render deployment preparation, requirements.txt setup, documentation drafting, README development, and code review.

Human verification: AI-assisted code was reviewed line by line by team members, run locally in VS Code, and modified to match the project structure and course requirements. Dashboard pages, navigation, callbacks, filters, file paths, and visual outputs were tested manually. Calculations and aggregations were checked against the underlying CSV/API data, and AI-generated wording was edited for accuracy, clarity, and consistency with the team’s intended story. Deployment-related code and package requirements were compared against the course instructions before being added.

# Key Findings

Replace these placeholders only after the team has verified the calculations against the final data.

# Place — Music Across America: [ADD ONE VERIFIED MAP FINDING]

# Time — Lifespan of a Hit: [ADD ONE VERIFIED BILLBOARD LIFESPAN FINDING]

# Legacy — Staying Power: [ADD ONE VERIFIED ARTIST-LONGEVITY FINDING]

Future Improvements

Possible extensions include:

a click-a-state interaction that reveals a state-level genre trend over time;

population normalization for live-performance counts;

additional validation of genre assignments;

more complete historical Billboard sampling;

adjustable weights for the Staying Power Score;

richer cross-page storytelling connecting geography, chart longevity, and artist legacy.

Attribution

This project is an academic, non-commercial student project. Data and metadata remain subject to the terms and licenses of their original sources. The dashboard should retain visible attribution for Setlist.fm and the Billboard datasets, and any additional attribution required by MusicBrainz, Last.fm, Wikidata, or Discogs where those sources contribute to displayed data.