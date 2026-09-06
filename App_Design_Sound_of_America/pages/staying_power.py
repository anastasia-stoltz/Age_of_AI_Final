import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests

## Explores the longevity of artists acorss decades
## Esnure IDs have prefixes to avoid callback collisions i.e:
# stay-ranking
# stay-artist

dash.register_page(__name__,
    path="/staying-power",
    name="Artist Staying Power"
)


layout = html.Div([
    html.H1("Artist Staying Power"),
    html.P("This analysis is currently being developed by the team.")
    
])