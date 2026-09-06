import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import requests

## Explore how chart succcess has evolved acorss eras ##
## Esnure IDs have prefixes to avoid callback collisions e.g: 
# hit-decade
# hit-chart

dash.register_page(__name__,
    path="/anatomy-of-a-hit",
    name="Anatomy of a Hit"
)


layout = html.Div([
    html.H1("Anatomy of a Hit"),
    html.P("This analysis is currently being developed by the team.")
])