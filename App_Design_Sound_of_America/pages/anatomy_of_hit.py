import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests
from functools import lru_cache


# --------------------------------------------------
# PAGE REGISTRATION
# --------------------------------------------------

dash.register_page(
    __name__,
    path="/anatomy-of-a-hit",
    name="Lifespan of a Hit"
)


# --------------------------------------------------
# COLORS
# --------------------------------------------------

BG = "#0f1720"
SECTION_BG = "#131d27"
BORDER = "#303945"
GOLD = "#d9ad5b"
BLUE = "#81b6fa"
CREAM = "#f4f1ea"


# --------------------------------------------------
# BILLBOARD DATA
# --------------------------------------------------

@lru_cache(maxsize=None)
def get_chart(date):
    url = (
        "https://raw.githubusercontent.com/"
        "mhollingshead/billboard-hot-100/main/date/"
        f"{date}.json"
    )

    response = requests.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    chart = response.json()

    df = pd.DataFrame(
        chart["data"]
    )

    df["chart_date"] = chart["date"]

    return df


# Three comparable chart weeks per year
YEAR_DATES = {
    1985: ["1985-04-06", "1985-07-06", "1985-10-05"],
    1990: ["1990-04-07", "1990-07-07", "1990-10-06"],
    1995: ["1995-04-08", "1995-07-08", "1995-10-07"],
    2000: ["2000-04-08", "2000-07-08", "2000-10-07"],
    2005: ["2005-04-09", "2005-07-09", "2005-10-08"],
    2010: ["2010-04-10", "2010-07-10", "2010-10-09"],
    2015: ["2015-04-11", "2015-07-11", "2015-10-10"],
    2020: ["2020-04-11", "2020-07-11", "2020-10-10"],
    2025: ["2025-04-05", "2025-07-05", "2025-10-04"]
}


@lru_cache(maxsize=None)
def summarize_year(year):
    hot100_weeks = []
    top10_weeks = []
    unique_artist_counts = []

    for date in YEAR_DATES[year]:
        chart = get_chart(date)

        hot100_weeks.append(
            chart["weeks_on_chart"].mean()
        )

        top10_weeks.append(
            chart.head(10)["weeks_on_chart"].mean()
        )

        unique_artist_counts.append(
            chart["artist"].nunique()
        )

    return {
        "year": year,
        "avg_hot100": round(
            sum(hot100_weeks) / len(hot100_weeks),
            2
        ),
        "avg_top10": round(
            sum(top10_weeks) / len(top10_weeks),
            2
        ),
        "avg_unique_artists": round(
            sum(unique_artist_counts) / len(unique_artist_counts),
            2
        )
    }


# --------------------------------------------------
# DROPDOWN OPTIONS
# --------------------------------------------------

year_options = [
    {
        "label": str(year),
        "value": year
    }
    for year in YEAR_DATES
]


# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

layout = dbc.Container([

    html.Div([

        html.P(
            "TIME",
            className="small-label"
        ),

        html.H1(
            "Lifespan of a Hit",
            className="section-title"
        ),

        html.P(
            "How has the staying power of a Billboard hit changed over time?",
            className="section-text"
        ),

        html.P(
            "Each year uses three Billboard Hot 100 charts from April, July, "
            "and October. For songs currently in the Top 10, weeks on chart "
            "refers to their total time on the Hot 100.",
            className="source-text"
        )

    ], className="mt-4 mb-4"),


    dbc.Row([

        dbc.Col([

            html.Label("Compare Year 1"),

            dcc.Dropdown(
                id="hit-year-1",
                options=year_options,
                value=1985,
                clearable=False,
                className="hit-dropdown"
            )

        ], md=6),

        dbc.Col([

            html.Label("Compare Year 2"),

            dcc.Dropdown(
                id="hit-year-2",
                options=year_options,
                value=2025,
                clearable=False,
                className="hit-dropdown"
            )

        ], md=6)

    ], className="mb-4"),


    dcc.Loading(
        id="hit-loading",
        type="circle",
        children=[

            html.Div([

                html.P(
                    "HIT LIFESPAN",
                    className="small-label"
                ),

                html.H2(
                    "Hits are staying on the chart longer",
                    className="section-title"
                ),

                html.Div(
                    id="hit-lifespan-comparison"
                )

            ], className="project-card mb-4"),


            dcc.Graph(
                id="hit-lifespan-trend"
            ),


            html.Div([

                html.P(
                    "ARTIST VARIETY",
                    className="small-label"
                ),

                html.H2(
                    "Fewer artists are sharing the spotlight",
                    className="section-title"
                ),

                html.Div(
                    id="hit-artist-comparison"
                )

            ], className="project-card mb-4"),


            dcc.Graph(
                id="hit-artist-trend"
            ),


            html.Div([

                html.P(
                    "WHAT CHANGED?",
                    className="small-label"
                ),

                html.Div(
                    id="hit-insight"
                )

            ], className="finding-card mt-4 mb-5")

        ]
    )

], fluid=True)


# --------------------------------------------------
# CALLBACK
# --------------------------------------------------

@callback(
    Output("hit-lifespan-comparison", "children"),
    Output("hit-artist-comparison", "children"),
    Output("hit-lifespan-trend", "figure"),
    Output("hit-artist-trend", "figure"),
    Output("hit-insight", "children"),
    Input("hit-year-1", "value"),
    Input("hit-year-2", "value")
)
def update_hit_comparison(year1, year2):

    summary1 = summarize_year(year1)
    summary2 = summarize_year(year2)


    # --------------------------------------------------
    # LIFESPAN COMPARISON
    # --------------------------------------------------

    lifespan_comparison = dbc.Row([

        dbc.Col([

            html.P(
                "ALL HOT 100 SONGS",
                className="small-label"
            ),

            html.Div([

                html.Div([
                    html.H4(str(year1)),
                    html.H2(
                        f"{summary1['avg_hot100']} weeks"
                    )
                ]),

                html.H2("→"),

                html.Div([
                    html.H4(str(year2)),
                    html.H2(
                        f"{summary2['avg_hot100']} weeks"
                    )
                ])

            ], style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "gap": "20px"
            })

        ], md=6),

        dbc.Col([

            html.P(
                "SONGS CURRENTLY IN THE TOP 10",
                className="small-label"
            ),

            html.Div([

                html.Div([
                    html.H4(str(year1)),
                    html.H2(
                        f"{summary1['avg_top10']} weeks"
                    )
                ]),

                html.H2("→"),

                html.Div([
                    html.H4(str(year2)),
                    html.H2(
                        f"{summary2['avg_top10']} weeks"
                    )
                ])

            ], style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "gap": "20px"
            })

        ], md=6)

    ], className="g-4")


    # --------------------------------------------------
    # ARTIST VARIETY COMPARISON
    # --------------------------------------------------

    artist_difference = (
        summary2["avg_unique_artists"]
        - summary1["avg_unique_artists"]
    )

    if summary1["avg_unique_artists"] != 0:
        artist_pct_change = (
            artist_difference
            / summary1["avg_unique_artists"]
            * 100
        )
    else:
        artist_pct_change = 0


    if artist_pct_change < 0:
        artist_change_text = (
            f"{abs(artist_pct_change):.1f}% fewer unique artists"
        )
    elif artist_pct_change > 0:
        artist_change_text = (
            f"{abs(artist_pct_change):.1f}% more unique artists"
        )
    else:
        artist_change_text = (
            "No change in unique artist count"
        )


    artist_comparison = html.Div([

        html.Div([

            html.Div([
                html.H4(str(year1)),
                html.H2(
                    f"{summary1['avg_unique_artists']}"
                ),
                html.P(
                    "average unique artists"
                )
            ]),

            html.H1("→"),

            html.Div([
                html.H4(str(year2)),
                html.H2(
                    f"{summary2['avg_unique_artists']}"
                ),
                html.P(
                    "average unique artists"
                )
            ])

        ], style={
            "display": "flex",
            "justifyContent": "space-around",
            "alignItems": "center",
            "textAlign": "center",
            "gap": "30px"
        }),

        html.H3(
            artist_change_text,
            className="mt-3"
        )

    ])


    # --------------------------------------------------
    # FULL TREND DATA
    # --------------------------------------------------

    lifespan_rows = []
    artist_rows = []

    for year in YEAR_DATES:

        summary = summarize_year(year)

        lifespan_rows.append({
            "Year": year,
            "Metric": "All Hot 100 Songs",
            "Weeks": summary["avg_hot100"]
        })

        lifespan_rows.append({
            "Year": year,
            "Metric": "Songs Currently in Top 10",
            "Weeks": summary["avg_top10"]
        })

        artist_rows.append({
            "Year": year,
            "Unique Artists": summary["avg_unique_artists"]
        })


    lifespan_df = pd.DataFrame(
        lifespan_rows
    )

    artist_df = pd.DataFrame(
        artist_rows
    )


    # --------------------------------------------------
    # LIFESPAN TREND CHART
    # --------------------------------------------------

    lifespan_fig = px.line(
        lifespan_df,
        x="Year",
        y="Weeks",
        color="Metric",
        markers=True,
        title="How Hit Lifespans Changed, 1985–2025",
        color_discrete_sequence=[
            GOLD,
            BLUE
        ]
    )

    lifespan_fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=SECTION_BG,
        font_color=CREAM,
        title_font_color=CREAM,
        legend_title_text="",
        margin=dict(
            l=40,
            r=20,
            t=70,
            b=40
        )
    )

    lifespan_fig.update_xaxes(
        gridcolor=BORDER
    )

    lifespan_fig.update_yaxes(
        gridcolor=BORDER,
        title="Average Weeks on Hot 100",
        rangemode="tozero"
    )


    # --------------------------------------------------
    # ARTIST VARIETY TREND CHART
    # --------------------------------------------------

    artist_fig = px.line(
        artist_df,
        x="Year",
        y="Unique Artists",
        markers=True,
        title="How Artist Variety Changed, 1985–2025"
    )

    artist_fig.update_traces(
        line=dict(
            color=GOLD
        ),
        marker=dict(
            color=GOLD
        )
    )

    artist_fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=SECTION_BG,
        font_color=CREAM,
        title_font_color=CREAM,
        margin=dict(
            l=40,
            r=20,
            t=70,
            b=40
        )
    )

    artist_fig.update_xaxes(
        gridcolor=BORDER
    )

    artist_fig.update_yaxes(
        gridcolor=BORDER,
        title="Average Unique Artists",
        rangemode="tozero"
    )


    # --------------------------------------------------
    # DYNAMIC TAKEAWAY
    # --------------------------------------------------

    hot100_difference = (
        summary2["avg_hot100"]
        - summary1["avg_hot100"]
    )

    top10_difference = (
        summary2["avg_top10"]
        - summary1["avg_top10"]
    )


    if hot100_difference > 0:
        hot100_phrase = (
            f"{abs(hot100_difference):.2f} weeks longer"
        )
    elif hot100_difference < 0:
        hot100_phrase = (
            f"{abs(hot100_difference):.2f} weeks shorter"
        )
    else:
        hot100_phrase = (
            "about the same amount of time"
        )


    if top10_difference > 0:
        top10_phrase = (
            f"{abs(top10_difference):.2f} weeks longer"
        )
    elif top10_difference < 0:
        top10_phrase = (
            f"{abs(top10_difference):.2f} weeks shorter"
        )
    else:
        top10_phrase = (
            "about the same amount of time"
        )


    insight = html.P(
        f"Compared with {year1}, songs on the Hot 100 in {year2} "
        f"had been charting {hot100_phrase} on average. "
        f"For songs occupying the Top 10, the difference was "
        f"{top10_phrase}. "
        f"Meanwhile, the average number of unique artists changed "
        f"from {summary1['avg_unique_artists']} to "
        f"{summary2['avg_unique_artists']}."
    )


    return (
        lifespan_comparison,
        artist_comparison,
        lifespan_fig,
        artist_fig,
        insight
    )