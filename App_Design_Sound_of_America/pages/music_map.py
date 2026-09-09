import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import os

dash.register_page(__name__, path='/music-map', name='Music Across America')

BG = "#1D2A30"

#changed to allow for directory differences
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, "..", "data", "concert_map_data_setlistfm.csv"))

years = sorted(df["year"].unique())
genres = sorted(df["genre"].unique())
marks = {
    int(y): {'label': str(y), 'style': {'color': '#EAF2F8', 'fontWeight': '600'}}
    for y in years
}
max_count = int(df["event_count"].max())


default_year = years[-2] if len(years) >= 2 else years[-1]
default_genre = df.groupby("genre")["event_count"].sum().idxmax()

layout = html.Div(
    style={'minHeight': '100vh', 'maxWidth': '1250px', 'margin': '0 auto',
           'padding': '40px', 'backgroundColor': BG},
    children=[
        html.H1("Live Music in the US",
                style={'color': 'white', 'textAlign': 'center', 'fontSize': '30px'}),
        html.P(
            "This map shows how live music activity is spread across the United States, "
            "broken down by genre and year. Each state is shaded by how many documented "
            "shows took place there for the genre and year you select — darker means more "
            "shows. Use it to see where different genres tour most, and how that's shifted "
            "year to year.",
            style={'color': '#9fbccd', 'backgroundColor': BG, 'textAlign': 'center',
                   'maxWidth': '780px', 'margin': '0 auto 12px auto', 'lineHeight': '1.5'}),
        html.P("Pick a genre, drag the slider to change year.",
               style={'color': '#9fbccd', 'backgroundColor': BG, 'textAlign': 'center',
                      'margin': '0 0 20px 0'}),
        html.Div(
            dcc.Dropdown(id='genre-picker',
                         className='hit-dropdown',
                         options=[{'label': g.title(), 'value': g} for g in genres],
                         value=default_genre, clearable=False),
            style={'maxWidth': '320px', 'margin': '0 auto'}),
        html.Div(
            dcc.Slider(id='year-slider', min=years[0], max=years[-1], value=default_year,
                       marks=marks, step=None,
                       tooltip={'placement': 'top', 'always_visible': True}),
            style={'padding': '28px'}),
        dcc.Graph(id='choropleth-map', style={'height': '70vh', 'minHeight': '520px'},
                  config={'displaylogo': False}),
        html.Details(
            style={'color': '#9fbccd', 'maxWidth': '780px', 'margin': '24px auto 0 auto',
                   'lineHeight': '1.6', 'fontSize': '14px'},
            children=[
                html.Summary(
                    "About this data",
                    style={'color': 'white', 'cursor': 'pointer', 'fontSize': '15px',
                           'marginBottom': '8px'}),
                html.P(
                    "Concert data comes from setlist.fm, a crowd-sourced archive of "
                    "documented live-performance setlists. The Overall Live Music view "
                    "uses state-by-year totals to compare activity across all 50 states "
                    "and selected years."
                    ),
                html.P(
                    "The Explore by Genre view uses a sample of setlists collected for "
                    "each state and year. Artist genres were identified through MusicBrainz, "
                    "Last.fm, Wikidata, and Discogs, then grouped into broad categories. "
                    "Because this view is sample-based, it represents genre mix rather than "
                    "the total number of performances."
                    ),
                html.P(
                    "Setlist.fm does not document every concert, so these results should "
                    "not be interpreted as a complete census of live music. Some artists "
                    "could not be reliably classified and appear as \"Unknown\" or \"Other.\""
                    ),
                html.P(
                    "Data was last retrieved from the setlist.fm API on September 8, 2026, "
                    "and cached locally to improve dashboard speed and comply with API "
                    "request limits. Because setlist.fm is continually updated, the dataset "
                    "requires periodic refreshes. Data for 2026 represents the year to date."),
            ]),
    ]
)


@dash.callback(
    Output('choropleth-map', 'figure'),
    Input('year-slider', 'value'),
    Input('genre-picker', 'value'),
)
def update_map(selected_year, genre):
    filtered = df[(df['year'] == selected_year) & (df['genre'] == genre)]

    fig = px.choropleth(
    filtered,
    locations='state',
    locationmode='USA-states',
    color='event_count',
    scope='usa',
    color_continuous_scale=[
        [0, "#E4EBF2"],
        [0.35, "#81B6FA"],
        [0.7, "#397B9B"],
        [1, "#D9AD5B"]
    ],
    hover_name='state',
    labels={'event_count': 'Shows'},
    range_color=(0, max_count),
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        geo=dict(bgcolor=BG, lakecolor=BG, landcolor="#3E3839"),
        paper_bgcolor=BG, font_color='white',
        coloraxis_colorbar=dict(title='Shows', thickness=14, len=0.6),
    )
    fig.update_traces(marker_line_color=BG, marker_line_width=0.6)

    if filtered.empty:
        fig.add_annotation(
            text="No documented shows found for this genre and year.",
            showarrow=False, x=0.5, y=0.5, xref='paper', yref='paper',
            font=dict(color='#9fbccd', size=16),
        )

    return fig