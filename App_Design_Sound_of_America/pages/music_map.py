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
                    "real, documented setlists. We queried it state by state and year "
                    "by year to make sure every state and each year from 2022–2026 is "
                    "represented, rather than just whatever was most recently added."),
                html.P(
                    "Genres are resolved per artist through a chain of sources "
                    "(MusicBrainz, Last.fm, Wikidata, and Discogs), then grouped into "
                    "broad categories like \"Rock\" or \"Electronic/Dance\" so the map "
                    "stays readable — the underlying data has hundreds of much more "
                    "specific micro-genres."),
                html.P(
                    "A few honest limitations: not every show that ever happened is in "
                    "setlist.fm, coverage is a sample rather than a full census, and "
                    "some artists' genres couldn't be resolved by any source and are "
                    "grouped as \"Unknown\" or \"Other/Uncategorized.\""),
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
        filtered, locations='state', locationmode='USA-states',
        color='event_count', scope='usa',
        color_continuous_scale='Reds', hover_name='state',
        labels={'event_count': 'Shows'},
        range_color=(0, max_count),  # fixed scale so years/genres stay comparable
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