import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests

## Visualization of Sound of America
## Esnure IDs have prefixes to avoid callback collisions ex: 
# map-year
# map-metric
# map-chart

dash.register_page(__name__,
    path="/music-map",
    name="Music Map"
)


layout = html.Div([
        html.H1("Music Map"),
        html.P("This analysis is currently being developed by the team.")
])