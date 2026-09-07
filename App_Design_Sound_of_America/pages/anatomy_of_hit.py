import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests
from functools import lru_cache


## Explore how chart success has evolved across eras ##
## Ensure IDs have prefixes to avoid callback collisions ##

dash.register_page(
    __name__,
    path="/anatomy-of-a-hit",
    name="Anatomy of a Hit"
)


# --------------------------------------------------
# DATA HELPER
# --------------------------------------------------

def get_chart(date):
    url = (
        "https://raw.githubusercontent.com/"
        "mhollingshead/billboard-hot-100/main/date/"
        f"{date}.json"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    chart = response.json()

    df = pd.DataFrame(chart["data"])
    df["chart_date"] = chart["date"]

    return df


# Same three non-holiday comparison points for each year
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

print("ANATOMY YEARS LOADED:", list(YEAR_DATES.keys()))

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
            sum(unique_artist_counts) /
            len(unique_artist_counts),
            2
        )
    }


# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

# --------------------------------------------------
# PAGE LAYOUT
# --------------------------------------------------

year_options = [
    {"label": str(year), "value": year}
    for year in YEAR_DATES
]


layout = dbc.Container([

    html.H1(
        "Anatomy of a Hit",
        className="mt-4"
    ),

    html.P(
        "How has the staying power of a Billboard hit changed over time?"
    ),

    # Year comparison dropdowns
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

    # Loading indicator appears while callback is updating
    dcc.Loading(
        id="hit-loading",
        type="circle",
        children=[

            # Weeks-on-chart cards
            dbc.Row([

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(
                                "Avg. Weeks on Hot 100",
                                className="card-title"
                            ),
                            html.H2(
                                id="hit-hot100-year1"
                            )
                        ])
                    ),
                    md=3
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(
                                "Avg. Weeks on Hot 100",
                                className="card-title"
                            ),
                            html.H2(
                                id="hit-hot100-year2"
                            )
                        ])
                    ),
                    md=3
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(
                                "Avg. Weeks in Top 10",
                                className="card-title"
                            ),
                            html.H2(
                                id="hit-top10-year1"
                            )
                        ])
                    ),
                    md=3
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(
                                "Avg. Weeks in Top 10",
                                className="card-title"
                            ),
                            html.H2(
                                id="hit-top10-year2"
                            )
                        ])
                    ),
                    md=3
                )

            ], className="mb-4"),

            # Unique artist cards
            dbc.Row([

                dbc.Col(
                    html.Div([
                        html.H5(
                            "Average Unique Artists",
                            className="card-title"
                        ),
                        html.H2(
                            id="hit-artists-year1"
                        )
                    ], className="project-card"),
                    md=6
                ),

                dbc.Col(
                    html.Div([
                        html.H5(
                            "Average Unique Artists",
                            className="card-title"
                        ),
                        html.H2(
                            id="hit-artists-year2"
                        )
                    ], className="project-card"),
                    md=6
                )

            ], className="mb-4"),

            # Comparison chart
            dcc.Graph(
                id="hit-comparison-chart"
            ),

            # Written comparison
            html.Div(
                id="hit-insight",
                className="mt-3 mb-5"
            )

        ]
    )

], fluid=True)

# --------------------------------------------------
# CALLBACK
# --------------------------------------------------

@callback(
    Output("hit-hot100-year1", "children"),
    Output("hit-hot100-year2", "children"),
    Output("hit-top10-year1", "children"),
    Output("hit-top10-year2", "children"),
    Output("hit-artists-year1", "children"),
    Output("hit-artists-year2", "children"),
    Output("hit-comparison-chart", "figure"),
    Output("hit-insight", "children"),
    Input("hit-year-1", "value"),
    Input("hit-year-2", "value")
)
def update_hit_comparison(year1, year2):

    summary1 = summarize_year(year1)
    summary2 = summarize_year(year2)

    chart_df = pd.DataFrame([
        {
            "Year": str(year1),
            "Metric": "Avg. Weeks on Hot 100",
            "Value": summary1["avg_hot100"]
        },
        {
            "Year": str(year1),
            "Metric": "Avg. Weeks in Top 10",
            "Value": summary1["avg_top10"]
        },
        {
            "Year": str(year2),
            "Metric": "Avg. Weeks on Hot 100",
            "Value": summary2["avg_hot100"]
        },
        {
            "Year": str(year2),
            "Metric": "Avg. Weeks in Top 10",
            "Value": summary2["avg_top10"]
        }
    ])

    fig = px.bar(
        chart_df,
        x="Metric",
        y="Value",
        color="Year",
        barmode="group",
        title="How Long Do Hits Stay on the Chart?",
        color_discrete_sequence=[
             "#d9ad5b",   # warm gold
             "#81b6fa"    # muted blue
        ]
        )

    fig.update_layout(
        paper_bgcolor="#0f1720",
        plot_bgcolor="#131d27",
        font_color="#f4f1ea",
        title_font_color="#f4f1ea",
        legend_title_font_color="#f4f1ea"
        )

    fig.update_xaxes(
        gridcolor="#303945",
        zerolinecolor="#303945"
        )

    fig.update_yaxes(
        gridcolor="#303945",
        zerolinecolor="#303945"
        )

    difference = (
        summary2["avg_hot100"]
        - summary1["avg_hot100"]
    )

    if difference > 0:
        direction = "longer"
    elif difference < 0:
        direction = "shorter"
    else:
        direction = "about the same amount of time"

    insight = html.P(
        f"In this comparison, songs on the Hot 100 in "
        f"{year2} had been charting an average of "
        f"{abs(difference):.2f} weeks {direction} "
        f"than songs in {year1}. "
        f"The average number of unique artists was "
        f"{summary1['avg_unique_artists']} in {year1} "
        f"and {summary2['avg_unique_artists']} in {year2}."
    )

    return (
        f"{summary1['avg_hot100']} weeks",
        f"{summary2['avg_hot100']} weeks",
        f"{summary1['avg_top10']} weeks",
        f"{summary2['avg_top10']} weeks",
        f"{summary1['avg_unique_artists']}",
        f"{summary2['avg_unique_artists']}",
        fig,
        insight
    )