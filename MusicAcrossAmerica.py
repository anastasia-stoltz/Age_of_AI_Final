import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output

dash.register_page(__name__, path='/musicacrossamerica', name='Music Across America')

BG = "#1D2A30"

# Loaded once when the page module is imported. Refresh the data by
# re-running collect_data.py, not by re-scraping on every page load.
df = pd.read_csv("concert_map_data.csv")

years = sorted(df["year"].unique())
genres = sorted(df["genre"].unique())
marks = {int(y): str(y) for y in years}
max_count = int(df["event_count"].max())

# Default to the earliest year (most complete data — later years thin out,
# since tours announce dates on a rolling basis) and the most-played genre
# overall, so the first thing people see is a full, readable map rather
# than a sparse one.
default_year = years[0]
default_genre = df.groupby("genre")["event_count"].sum().idxmax()

layout = html.Div(
    style={'minHeight': '100vh', 'maxWidth': '1250px', 'margin': '0 auto',
           'padding': '40px', 'backgroundColor': BG},
    children=[
        html.H1("Live Music in the US",
                style={'color': 'white', 'textAlign': 'center', 'fontSize': '30px'}),
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
            # The tooltip sits above the rail so it stops landing on the mark
            # labels; the padding keeps it from being clipped by the container.
            style={'padding': '28px'}),
        dcc.Graph(id='choropleth-map', style={'height': '70vh', 'minHeight': '520px'},
                  config={'displaylogo': False}),
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
        # Ticketmaster only lists on-sale/announced shows, so some
        # year+genre combinations (especially 2028, the furthest-out year)
        # genuinely have no listings yet rather than this being a bug.
        fig.add_annotation(
            text="No shows listed yet for this genre/year combination.",
            showarrow=False, x=0.5, y=0.5, xref='paper', yref='paper',
            font=dict(color='#9fbccd', size=16),
        )

    return fig