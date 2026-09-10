# AI Usage Appendix

## Overview

Generative AI was used as an assistance tool during development of **The Sound of America**. AI output was not treated as automatically correct or final. Suggestions were reviewed, edited, tested, and either incorporated, revised, or discarded based on the project requirements and the underlying data.

Only AI uses that can be confirmed from the project-development process are listed here.

## Tool Used

- **ChatGPT, Claude**

## Where AI Was Used

### 1. Shared App Structure and Visual Design

AI was used to help:

- review the multi-page Dash structure and navigation
- brainstorm a consistent visual identity across pages
- refine layout, spacing, typography, and color usage
- check consistency between the Home, Music Across America, Lifespan of a Hit, and Staying Power pages
- review accessibility considerations such as contrast and avoiding unnecessary color variation

### 2. Home Page and App Integration

AI was used to assist with:

- organizing the Home page story
- refining explanatory copy and navigation wording
- reviewing page integration so the project felt like one application rather than separate analyses
- troubleshooting shared CSS and layout behavior

### 3. Music Across America Page

AI was used extensively as a review and debugging for the live-music map including:

- reviewing the meaning of the Setlist.fm sample
- identifying that sampled event_count values should not be described as complete state concert totals
- refining the year/genre interaction
- adding and reviewing the click-a-state genre profile
- reviewing empty-data and edge-case behavior

AI was also used to investigate a possible historical expansion of the map. That experiment was not used in the final dashboard after the team determined that genre-enrichment coverage and external API reliability were not strong enough to support the broader historical claim. The final app retained the more defensible recent Setlist.fm sample.

### 4. Data Acquisition, Cleaning, and Interpretation Review

AI was used to assist with reasoning about and troubleshooting parts of the data workflow including:

- Setlist.fm API request structure and returned fields
- API-rate-limit and timeout issues
- genre-enrichment logic involving MusicBrainz and fallback metadata sources
- cache behavior and environment-variable setup
- identifying limitations that needed to be communicated to users.

AI assistance was used as a debugging and interpretation aid but data outputs were still inspected and tested by the team.

### 5. Billboard Analysis Pages

AI was used primarily as a review aid for the Billboard-based portions of the application by:

- checking whether the page narratives were understandable to a nontechnical user
- reviewing visual consistency with the rest of the application
- discussing how findings should be described without overstating what the data showed
- reviewing the transparency of the Staying Power scoring concept

The underlying Billboard calculations and final analytical outputs were checked against the project data and running app.

### 6. Git, GitHub, and Render Deployment

AI was used to help troubleshoot:

- Git branches, staging, commits, merges, and merge conflicts
- avoiding accidental commits of .env, cache files, and abandoned experimental files
- synchronizing local and remote repository state
- Render repository/branch/root-directory configuration
- production start-command requirements
- interpretation of Render deployment logs

### 7. Documentation and Presentation

AI was used to assist with:

- reviewing the project against the assignment rubric
- drafting and refining documentation language
- README completeness checks
- data-source and limitation wording
- poster organization and wording
- preparation of the project story for presentation

## Representative High-Level Prompt / Request Examples

The following are representative summaries of the kinds of requests used during development:

- “Review the current Dash project against the final-project rubric and identify anything missing.”
- “Help simplify this map code while preserving the existing data collection and genre-enrichment work.”
- “Explain whether these Setlist.fm counts can be interpreted as total concerts.”
- “Help calculate genre share correctly within each state.”
- “Review the dashboard pages for visual consistency and accessibility.”
- “Help troubleshoot this Git merge conflict without overwriting a teammate’s work.”
- “Help diagnose why the Render deployment is not updating.”

## Where AI Output Was Incorporated

AI-assisted suggestions contributed:

- shared layout and styling refinements
- Home-page narrative organization
- selected code debugging and simplification
- Git and deployment troubleshooting
- documentation wording
- poster and presentation wording

Not every AI suggestion was used. Some proposed approaches were tested and intentionally discarded when they did not meet the team’s standards for accuracy, simplicity, or data quality.

## Human Verification and Editing

AI-assisted work was verified through human review and testing including:

- running the Dash application locally
- testing page navigation
- changing dropdowns and sliders and checking resulting visuals
- clicking states on the map and checking the profile output
- reviewing calculations against the underlying CSV/API-derived data
- checking Setlist.fm sampling assumptions before making analytical claims
- reviewing data limitations and changing language when claims were too strong

## Final Responsibility

The submitted analysis, code, documentation, and presentation remain the responsibility of the project team. AI was used as an assistive development and review tool, not as a substitute for understanding, validation, or final decision-making.
