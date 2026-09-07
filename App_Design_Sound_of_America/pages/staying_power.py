import dash
from dash import Input, Output, callback, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

dash.register_page(__name__, path="/staying-power", name="Artist Staying Power")


def _build_sample_data():
    records = [
        {"artist": "Taylor Swift", "song": "Love Story", "year": 2008, "peak_position": 4, "chart_weeks": 32},
        {"artist": "Taylor Swift", "song": "Blank Space", "year": 2014, "peak_position": 1, "chart_weeks": 36},
        {"artist": "Taylor Swift", "song": "Anti-Hero", "year": 2022, "peak_position": 1, "chart_weeks": 28},
        {"artist": "Drake", "song": "Best I Ever Had", "year": 2009, "peak_position": 2, "chart_weeks": 30},
        {"artist": "Drake", "song": "God's Plan", "year": 2018, "peak_position": 1, "chart_weeks": 37},
        {"artist": "Drake", "song": "First Person Shooter", "year": 2023, "peak_position": 1, "chart_weeks": 18},
        {"artist": "Beyonce", "song": "Crazy in Love", "year": 2003, "peak_position": 1, "chart_weeks": 27},
        {"artist": "Beyonce", "song": "Single Ladies", "year": 2008, "peak_position": 1, "chart_weeks": 28},
        {"artist": "Beyonce", "song": "Break My Soul", "year": 2022, "peak_position": 1, "chart_weeks": 20},
        {"artist": "The Weeknd", "song": "Can't Feel My Face", "year": 2015, "peak_position": 1, "chart_weeks": 26},
        {"artist": "The Weeknd", "song": "Blinding Lights", "year": 2019, "peak_position": 1, "chart_weeks": 57},
        {"artist": "The Weeknd", "song": "Save Your Tears", "year": 2020, "peak_position": 1, "chart_weeks": 41},
        {"artist": "Adele", "song": "Rolling in the Deep", "year": 2010, "peak_position": 1, "chart_weeks": 34},
        {"artist": "Adele", "song": "Hello", "year": 2015, "peak_position": 1, "chart_weeks": 26},
        {"artist": "Adele", "song": "Easy on Me", "year": 2021, "peak_position": 1, "chart_weeks": 30},
        {"artist": "Ed Sheeran", "song": "The A Team", "year": 2011, "peak_position": 16, "chart_weeks": 32},
        {"artist": "Ed Sheeran", "song": "Shape of You", "year": 2017, "peak_position": 1, "chart_weeks": 59},
        {"artist": "Ed Sheeran", "song": "Bad Habits", "year": 2021, "peak_position": 2, "chart_weeks": 38},
        {"artist": "Rihanna", "song": "Umbrella", "year": 2007, "peak_position": 1, "chart_weeks": 33},
        {"artist": "Rihanna", "song": "Diamonds", "year": 2012, "peak_position": 1, "chart_weeks": 27},
        {"artist": "Rihanna", "song": "Work", "year": 2016, "peak_position": 1, "chart_weeks": 32},
    ]
    return pd.DataFrame(records)


def _artist_summary(df):
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
    return by_artist


DATA = _build_sample_data()
ARTIST_METRICS = _artist_summary(DATA)

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
                    "Compare artists by chart longevity. Rank by a single metric or use a composite score.",
                    className="intro-text",
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
                                    max=10,
                                    step=1,
                                    marks={i: str(i) for i in range(3, 11)},
                                    value=7,
                                ),
                            ],
                            md=4,
                        ),
                    ],
                    className="g-4",
                ),
                dcc.Graph(id="stay-ranking-chart"),
                html.H4("Artist Metric Table"),
                dbc.Table.from_dataframe(
                    ARTIST_METRICS.sort_values("staying_power_score", ascending=False).round(2),
                    striped=True,
                    bordered=True,
                    hover=True,
                    id="stay-table",
                ),
            ],
            className="main-section",
        ),
    ]
)


@callback(
    Output("stay-ranking-chart", "figure"),
    Input("stay-ranking", "value"),
    Input("stay-top-n", "value"),
)
def update_ranking_chart(selected_metric, top_n):
    ranked = ARTIST_METRICS.sort_values(selected_metric, ascending=False).head(top_n)
    label = next((k for k, v in METRIC_OPTIONS.items() if v == selected_metric), selected_metric)
    fig = px.bar(
        ranked.sort_values(selected_metric, ascending=True),
        x=selected_metric,
        y="artist",
        orientation="h",
        color=selected_metric,
        color_continuous_scale="Blues",
        labels={"artist": "Artist", selected_metric: label},
        title=f"Top {top_n} Artists by {label}",
    )
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20), coloraxis_showscale=False)
    return fig