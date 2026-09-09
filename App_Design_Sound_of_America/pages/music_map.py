import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import os

dash.register_page(__name__, path='/music-map', name='Music Across America')

BG = "#0F1720"
IVORY = "#F4F1EA"
GOLD = "#E8B86D"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, "..", "data", "concert_map_data_setlistfm.csv"))

# Bucket raw genres into broad categories here, at load time, rather than
# assuming the CSV was already produced by a collector version that does
# this -- that assumption has broken more than once tonight already.
_GENRE_BUCKET_RULES = [
    ("Metal", ["metal", "grindcore", "deathcore", "mathcore", "djent", "thrash"]),
    ("Punk/Hardcore", ["punk", "hardcore", "screamo", "emo", "riot grrrl",
                        "psychobilly", "swancore", "emoviolence"]),
    ("Hip-Hop/Rap", ["hip hop", "hip-hop", "rap", "trap", "crunk", "boom bap",
                      "gangsta", "cloud rap", "horrorcore", "nerdcore", "g-funk",
                      "dark plugg"]),
    ("Electronic/Dance", ["electronic", "edm", "dubstep", "house", "techno",
                           "trance", "electro", "synth", "dance", "breakbeat",
                           "breakcore", "breaks", "drum n bass", "drum and bass",
                           "downtempo", "ambient", "industrial", "ebm", "wave",
                           "goa", "chiptune", "glitch", "ghettotech", "hyperpop",
                           "rave", "hardstyle", "trip hop", "electronica",
                           "big beat", "eurodance", "acid ", "disco", "new age",
                           "lo-fi", "future bass", "drone"]),
    ("Reggae/Ska", ["reggae", "dub", "ska", "dancehall"]),
    ("Jazz/Blues", ["jazz", "blues", "big band", "swing", "dixieland", "lounge",
                     "bop"]),
    ("R&B/Soul/Funk", ["soul", "funk", "new jack swing", "r&b", "rnb"]),
    ("Country/Folk/Americana", ["country", "bluegrass", "americana", "folk",
                                 "cowboy", "appalachian", "norteño", "red dirt",
                                 "singer-songwriter", "acoustic"]),
    ("Christian/Gospel", ["christian", "gospel", "religious"]),
    ("Classical", ["classical", "opera", "choral", "chamber", "orchestral"]),
    ("Comedy/Spoken Word", ["comedy", "parody", "satire", "spoken word",
                             "audiobook", "cookbook", "cabaret", "drag"]),
    ("World", ["afrobeat", "cumbia", "salsa", "mariachi", "flamenco", "calypso",
               "zamrock", "hawaiian", "latin", "celtic", "polka", "k-pop",
               "filmi"]),
    ("Pop", ["pop"]),
    ("Rock", ["rock", "grunge", "psych", "indie", "jam band", "shoegaze",
              "surf", "aor", "alternative"]),
]


def _bucket_genre(raw_genre):
    genre = str(raw_genre or "").lower().strip()
    if not genre or genre == "unknown":
        return "Unknown"
    for bucket_name, keywords in _GENRE_BUCKET_RULES:
        if any(keyword in genre for keyword in keywords):
            return bucket_name
    return "Other/Uncategorized"


if df["genre"].nunique() > 20:
    df["genre"] = df["genre"].apply(_bucket_genre)
    df = df.groupby(["year", "state", "genre"])["event_count"].sum().reset_index()

df = df[~df["genre"].isin(["Unknown", "Other/Uncategorized"])].copy()

years = sorted(df["year"].unique())
genres = sorted(df["genre"].unique())
marks = {int(y): {'label': str(y), 'style': {'color': IVORY, 'fontWeight': '600'}} for y in years}

# Default to the most recent COMPLETE year, not just the last one -- 2026
# is year-to-date (through September only) and would otherwise become the
# default view simply for being newest, showing a less complete picture
# first.
default_year = years[-2] if 2026 in years and len(years) >= 2 else years[-1]
default_genre = df.groupby("genre")["event_count"].sum().idxmax()

layout = html.Div(
    style={'minHeight': '100vh', 'maxWidth': '1250px', 'margin': '0 auto',
           'padding': '40px', 'backgroundColor': BG},
    children=[
        html.P("PLACE", className="small-label"),
        html.H1("Music Across America", className="section-title"),

        html.P(
            "How does the mix of documented live music differ across U.S. states?",
            style={'color': IVORY, 'fontSize': '22px', 'maxWidth': '780px'}
        ),

        html.P(
            "Choose a genre and year. Darker gold means that genre makes up a larger "
            "share of the state's genre-identified setlists.",
            style={'color': '#B7BEC7', 'maxWidth': '780px', 'lineHeight': '1.5'}
        ),

        html.Div(
            dcc.Dropdown(
                id='genre-picker',
                className='hit-dropdown',
                options=[{'label': g.title(), 'value': g} for g in genres],
                value=default_genre,
                clearable=False
            ),
            style={'maxWidth': '320px', 'marginTop': '24px'}
        ),

        html.Div(
            dcc.Slider(
                id='year-slider',
                min=years[0],
                max=years[-1],
                value=default_year,
                marks=marks,
                step=None,
                tooltip={'placement': 'top', 'always_visible': True}
            ),
            style={'padding': '28px 8px'}
        ),

        html.P(id='map-summary', style={'color': '#B7BEC7'}),

        dcc.Graph(
            id='choropleth-map',
            style={'height': '70vh', 'minHeight': '520px'},
            config={'displaylogo': False}
        ),

        html.Div([
            html.P("STATE SOUND PROFILE", className="small-label"),
            html.H3("Click a state to explore its genre mix",
                    id='state-profile-title', style={'color': IVORY}),
            dcc.Graph(id='state-profile-chart', config={'displaylogo': False})
        ], style={'marginTop': '28px', 'padding': '22px',
                  'backgroundColor': '#18222D',
                  'borderLeft': f'4px solid {GOLD}', 'borderRadius': '8px'}),

        html.Details(
            style={'color': '#B7BEC7', 'maxWidth': '780px', 'margin': '24px 0 0 0',
                   'lineHeight': '1.6', 'fontSize': '14px'},
            children=[
                html.Summary("About this data",
                             style={'color': GOLD, 'cursor': 'pointer'}),
                html.P(
                    "Concert data comes from Setlist.fm, a crowd-sourced archive of "
                    "documented live-performance setlists."
                ),
                html.P(
                    "Artist genres were identified through "
                    "MusicBrainz, Last.fm, Wikidata, and Discogs, then grouped into broad categories."
                ),
                html.P(
                    "Because the genre data is sample-based, the map shows each genre's "
                    "share of genre-identified setlists within a state rather than total concert "
                    "activity or listener preference."
                ),
                html.P(
                    "Each state/year sample is roughly 10-20 genre-identified "
                    "setlists, so shares can swing sharply on a small number "
                    "of shows — a state's top genre might reflect just one or "
                    "two large tours that happened to be logged that year, "
                    "not necessarily a broader pattern. Treat single "
                    "percentages as suggestive, not statistically precise."
                )
            ]
        )
    ]
)


@dash.callback(
    Output('choropleth-map', 'figure'),
    Output('map-summary', 'children'),
    Input('year-slider', 'value'),
    Input('genre-picker', 'value'),
)
def update_map(selected_year, genre):
    year_df = df[df['year'] == selected_year]

    totals = year_df.groupby('state')['event_count'].sum().rename('sample_total')
    selected = (year_df[year_df['genre'] == genre]
                .groupby('state')['event_count'].sum().rename('genre_count'))

    filtered = pd.concat([totals, selected], axis=1).fillna(0).reset_index()
    filtered['genre_share'] = filtered.apply(
        lambda r: (r['genre_count'] / r['sample_total'] * 100) if r['sample_total'] > 0 else None,
        axis=1)

    fig = px.choropleth(
        filtered,
        locations='state',
        locationmode='USA-states',
        color='genre_share',
        scope='usa',
        color_continuous_scale=[[0, "#F4F1EA"], [0.45, "#E8C98F"], [1, GOLD]],
        custom_data=['genre_count', 'sample_total'],
        labels={'genre_share': f'{genre.title()} share (%)'}
    )

    fig.update_traces(
        marker_line_color=BG,
        marker_line_width=0.6,
        hovertemplate=(
            "<b>%{location}</b><br>" + genre.title()
            + ": %{z:.1f}% of genre-identified setlists<br>"
            + "Genre records: %{customdata[0]:.0f}<br>"
            + "Genre-identified setlists: %{customdata[1]:.0f}<extra></extra>"
        )
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        geo=dict(bgcolor=BG, lakecolor=BG, landcolor="#3E3839"),
        paper_bgcolor=BG,
        font_color=IVORY,
        coloraxis_colorbar=dict(title='Share (%)', thickness=14, len=0.6)
    )

    if filtered['genre_share'].notna().sum() == 0:
        fig.add_annotation(
            text="No genre-identified shows found for this genre and year.",
            showarrow=False, x=0.5, y=0.5, xref='paper', yref='paper',
            font=dict(color='#B7BEC7', size=16),
        )
        summary = f"No documented {genre.title()} shows found for {selected_year}."
        return fig, summary

    leader = filtered.loc[filtered['genre_share'].idxmax()]
    summary = (
        f"In {selected_year}, {leader['state']} has the highest sampled "
        f"{genre.title()} share at {leader['genre_share']:.1f}%."
    )

    return fig, summary


@dash.callback(
    Output('state-profile-title', 'children'),
    Output('state-profile-chart', 'figure'),
    Input('choropleth-map', 'clickData'),
    Input('year-slider', 'value'),
    Input('genre-picker', 'value'),
)
def update_state_profile(click_data, selected_year, selected_genre):
    if click_data is None:
        fig = px.bar()
        fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color=IVORY,
                          xaxis={'visible': False}, yaxis={'visible': False})
        fig.add_annotation(text="Click a state on the map.", showarrow=False)
        return "Click a state to explore its genre mix", fig

    state = click_data['points'][0]['location']
    state_df = df[(df['state'] == state) & (df['year'] == selected_year)]

    if state_df.empty:
        fig = px.bar()
        fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color=IVORY,
                          xaxis={'visible': False}, yaxis={'visible': False})
        fig.add_annotation(
            text=f"No genre-identified shows found for {state} in {selected_year}.",
            showarrow=False)
        return f"{state} Sound Profile · {selected_year}", fig

    profile = (state_df.groupby('genre', as_index=False)['event_count'].sum()
               .sort_values('event_count', ascending=False))
    profile['share'] = profile['event_count'] / profile['event_count'].sum() * 100
    profile = profile.head(8).sort_values('share')

    colors = [GOLD if g == selected_genre else "#D7D1C7" for g in profile['genre']]

    fig = px.bar(
        profile,
        x='share',
        y='genre',
        orientation='h',
        text='share',
        labels={'share': 'Share of genre-identified setlists (%)', 'genre': ''}
    )
    fig.update_traces(marker_color=colors, texttemplate='%{text:.1f}%')
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color=IVORY,
                      margin=dict(l=20, r=70, t=20, b=50))

    return f"{state} Sound Profile · {selected_year}", fig