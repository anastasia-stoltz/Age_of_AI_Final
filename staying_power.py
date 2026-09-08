import os
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html
from dotenv import load_dotenv

load_dotenv()

dash.register_page(__name__, path="/staying-power", name="Artist Staying Power")

MIN_CHARTING_SONGS = 2  # exclude one-hit wonders so the ranking stays meaningful

# ==========================================================================
# Billboard Hot 100 weekly chart history (1958-2021)
# ==========================================================================
# Dataset: "Billboard Hot 100" compiled by Sean Miller, originally published
# on data.world (https://data.world/kcmillersean/billboard-hot-100-1958-2017)
# and mirrored on Kaggle. Licensed CC BY-SA: redistribution and adaptation
# are permitted with attribution and share-alike terms.
#
# This is a static CSV, not a live API. Download "Hot Stuff.csv" from the
# dataset and place it in the project's data/ folder (App_Design_Sound_of_America/data/,
# a sibling of apis/, assets/, and pages/) - or set BILLBOARD_CSV_PATH in .env to
# point somewhere else.
BILLBOARD_CSV_ENV_VAR = "BILLBOARD_CSV_PATH"
# pages/staying_power.py -> parent is pages/, parent.parent is the app root.
DEFAULT_BILLBOARD_CSV = Path(__file__).resolve().parent.parent / "data" / "Hot Stuff.csv"
BILLBOARD_ATTRIBUTION = (
    "Chart data: Billboard Hot 100 (1958-2021), compiled by Sean Miller / data.world, CC BY-SA."
)


def _resolve_billboard_csv_path():
    return Path(os.environ.get(BILLBOARD_CSV_ENV_VAR, DEFAULT_BILLBOARD_CSV))


def _load_billboard_song_level():
    csv_path = _resolve_billboard_csv_path()
    if not csv_path.exists():
        raise FileNotFoundError(
            f"[staying_power] Hot Stuff.csv not found at {csv_path}. "
            f"Download it from the Billboard Hot 100 dataset (data.world/Kaggle, CC BY-SA) "
            f"and set {BILLBOARD_CSV_ENV_VAR} or place it at that path."
        )

    raw = pd.read_csv(csv_path)
    raw["Performer"] = raw["Performer"].astype(str).str.strip()

    raw["chart_year"] = pd.to_datetime(raw["WeekID"], errors="coerce").dt.year
    song_level = (
        raw.groupby(["Performer", "SongID", "Song"], as_index=False)
        .agg(
            peak_position=("Peak Position", "min"),
            chart_weeks=("Weeks on Chart", "max"),
            year=("chart_year", "min"),
        )
        .rename(columns={"Performer": "artist", "Song": "song"})
        .drop(columns=["SongID"])
    )
    if song_level.empty:
        raise ValueError("[staying_power] Hot Stuff.csv produced no usable rows.")
    return song_level


def _billboard_artist_summary(df):
    by_artist = (
        df.groupby("artist", as_index=False)
        .agg(
            distinct_songs=("song", "nunique"),
            total_chart_weeks=("chart_weeks", "sum"),
            top_10_hits=("peak_position", lambda s: (s <= 10).sum()),
            number_one_hits=("peak_position", lambda s: (s == 1).sum()),
            first_chart_year=("year", "min"),
            last_chart_year=("year", "max"),
        )
    )
    by_artist["career_span_years"] = by_artist["last_chart_year"] - by_artist["first_chart_year"] + 1
    by_artist["staying_power_score"] = (
        by_artist["distinct_songs"] * 1.5
        + by_artist["total_chart_weeks"] * 0.35
        + by_artist["top_10_hits"] * 4
        + by_artist["number_one_hits"] * 5
        + by_artist["career_span_years"] * 1.2
    )
    by_artist = by_artist[by_artist["distinct_songs"] >= MIN_CHARTING_SONGS].reset_index(drop=True)
    return by_artist


DATA = _load_billboard_song_level()
ARTIST_METRICS = _billboard_artist_summary(DATA)
MAX_ARTISTS_SHOWN = min(25, max(3, len(ARTIST_METRICS)))
DEFAULT_TOP_N = min(7, MAX_ARTISTS_SHOWN)

METRIC_OPTIONS = {
    "Staying Power Score": "staying_power_score",
    "Distinct Charting Songs": "distinct_songs",
    "Total Chart Weeks": "total_chart_weeks",
    "Top 10 Hits": "top_10_hits",
    "Number-One Hits": "number_one_hits",
    "Career Span (Years)": "career_span_years",
}

layout = html.Div(
    [
        dbc.Container(
            [
                html.P("LEGACY", className="small-label"),
                html.H1("Artist Staying Power", className="main-title"),
                html.P(
                    "Staying power isn't about how big one song got \u2014 it's about how much of a "
                    "lasting mark an artist left on the Hot 100. An artist who kept charting new "
                    "songs across decades scores higher here than one who dominated a single era "
                    "and then disappeared.",
                    className="intro-text",
                    style={"maxWidth": "680px", "marginTop": "0.5rem"},
                ),
                html.Div(
                    [
                        html.Div(
                            "The composite score blends five measures pulled from six decades of "
                            "Hot 100 history, each weighted by how strongly it reflects lasting impact:",
                            style={"color": "#C7CCD9", "marginBottom": "0.75rem", "maxWidth": "680px"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [html.Span("Number-one hits", style={"color": "#F4F1EA"}), html.Span(" \u00d7 5", style={"color": "#E8B86D", "fontWeight": "600"})],
                                    style={"display": "flex", "justifyContent": "space-between", "padding": "0.35rem 0", "borderBottom": "1px solid rgba(244,241,234,0.08)"},
                                ),
                                html.Div(
                                    [html.Span("Top 10 hits", style={"color": "#F4F1EA"}), html.Span(" \u00d7 4", style={"color": "#E8B86D", "fontWeight": "600"})],
                                    style={"display": "flex", "justifyContent": "space-between", "padding": "0.35rem 0", "borderBottom": "1px solid rgba(244,241,234,0.08)"},
                                ),
                                html.Div(
                                    [html.Span("Total weeks on chart", style={"color": "#F4F1EA"}), html.Span(" \u00d7 0.35", style={"color": "#E8B86D", "fontWeight": "600"})],
                                    style={"display": "flex", "justifyContent": "space-between", "padding": "0.35rem 0", "borderBottom": "1px solid rgba(244,241,234,0.08)"},
                                ),
                                html.Div(
                                    [html.Span("Career span, in years", style={"color": "#F4F1EA"}), html.Span(" \u00d7 1.2", style={"color": "#E8B86D", "fontWeight": "600"})],
                                    style={"display": "flex", "justifyContent": "space-between", "padding": "0.35rem 0", "borderBottom": "1px solid rgba(244,241,234,0.08)"},
                                ),
                                html.Div(
                                    [html.Span("Distinct songs charted", style={"color": "#F4F1EA"}), html.Span(" \u00d7 1.5", style={"color": "#E8B86D", "fontWeight": "600"})],
                                    style={"display": "flex", "justifyContent": "space-between", "padding": "0.35rem 0"},
                                ),
                            ],
                            style={"maxWidth": "420px"},
                        ),
                    ],
                    style={
                        "marginTop": "1.5rem",
                        "padding": "1.25rem 1.5rem",
                        "border": "1px solid rgba(244,241,234,0.12)",
                        "borderRadius": "8px",
                        "background": "rgba(244,241,234,0.03)",
                        "maxWidth": "680px",
                    },
                ),
            ],
            className="main-section",
        ),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Ranking measure", htmlFor="stay-ranking"),
                                dcc.Dropdown(
                                    id="stay-ranking",
                                    options=[{"label": k, "value": v} for k, v in METRIC_OPTIONS.items()],
                                    value="staying_power_score",
                                    clearable=False,
                                ),
                            ],
                            md=8,
                        ),
                        dbc.Col(
                            [
                                html.Label("Top artists shown", htmlFor="stay-top-n"),
                                dcc.Slider(
                                    id="stay-top-n",
                                    min=3,
                                    max=MAX_ARTISTS_SHOWN,
                                    step=1,
                                    marks={i: str(i) for i in range(3, MAX_ARTISTS_SHOWN + 1, max(1, MAX_ARTISTS_SHOWN // 8))},
                                    value=DEFAULT_TOP_N,
                                ),
                            ],
                            md=4,
                        ),
                    ],
                    className="g-4",
                ),
                dcc.Graph(id="stay-ranking-chart"),
                html.H4("Artist Metric Table"),
                html.Div(id="stay-table-container"),
                html.P(BILLBOARD_ATTRIBUTION, className="small-label", style={"marginTop": "1rem"}),
            ],
            className="main-section",
        ),
    ]
)


@callback(
    Output("stay-ranking-chart", "figure"),
    Output("stay-table-container", "children"),
    Input("stay-ranking", "value"),
    Input("stay-top-n", "value"),
)
def update_ranking_chart(selected_metric, top_n):
    ranked = ARTIST_METRICS.sort_values(selected_metric, ascending=False).head(top_n)
    label = next((k for k, v in METRIC_OPTIONS.items() if v == selected_metric), selected_metric)
    ordered = ranked.sort_values(selected_metric, ascending=True)

    # Bar length already encodes rank, so a fading color scale on top just makes
    # lower bars harder to read. One solid accent, high contrast on a dark page.
    BAR_COLOR = "#E8B86D"       # warm gold, matches the LEGACY/title accent
    TEXT_COLOR = "#F4F1EA"      # off-white for labels/ticks
    GRID_COLOR = "rgba(244, 241, 234, 0.12)"

    fig = px.bar(
        ordered,
        x=selected_metric,
        y="artist",
        orientation="h",
        labels={"artist": "Artist", selected_metric: label},
        title=f"Top {top_n} Artists by {label}",
    )
    fig.update_traces(
        marker_color=BAR_COLOR,
        marker_line_width=0,
        texttemplate="%{x:,.1f}",
        textposition="outside",
        textfont_color=TEXT_COLOR,
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>" + label + ": %{x:,.1f}<extra></extra>",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_COLOR),
        title_font=dict(color=TEXT_COLOR, size=18),
        margin=dict(l=20, r=60, t=60, b=20),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, color=TEXT_COLOR),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", color=TEXT_COLOR),
    )

    table = dbc.Table.from_dataframe(
        ranked.sort_values(selected_metric, ascending=False).round(2),
        striped=True,
        bordered=True,
        hover=True,
        id="stay-table",
    )
    return fig, table
