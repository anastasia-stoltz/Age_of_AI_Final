import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

# Initialize the App
app = dash.Dash(__name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title="The Sound of America",
    external_stylesheets=[dbc.themes.COSMO]
)
server = app.server # For deployment

# Navigation bar shared by every page.
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavLink("Home", href="/", active="exact"),
        dbc.NavLink("Music Across America",
            href="/music-map",
            active="exact"
        ),
        dbc.NavLink("Anatomy of a Hit",
            href="/anatomy-of-a-hit",
            active="exact"
        ),
        dbc.NavLink("Staying Power",
            href="/staying-power",
            active="exact"
        ),
    ],
    brand="The Sound of America",
    brand_href="/",
    color="dark",
    dark=True,
    className="sound-navbar"
)

# The overall app layout
app.layout = html.Div([
    navbar,
        dash.page_container
])


if __name__ == "__main__":
    app.run(debug=True)