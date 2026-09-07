import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__,
    path="/",
    name="Home"
)


layout = html.Div([
    html.Div([
        dbc.Container([
            html.P("AN INTERACTIVE MUSIC ATLAS",
                   className="small-label"),
            html.H1("The Sound of America",
                    className="main-title"),
            html.H3("How does American music change across place, time, and artists?",
                    className="main-question"),
            html.P("Explore live music across the United States, the characteristics of successful songs and the artists whose careers continue to endure.",
                   className="intro-text"),
            dbc.Button("Explore the Music Map",
                       href="/music-map",
                       className="main-button")
        ])
    ], className="intro-section"),

    dbc.Container([
        html.H2("Explore the Project",
                className="section-title"),
        html.P("The Sound of America looks at music through three different perspectives.",
               className="section-text"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.P("PLACE",
                           className="small-label"),
                    html.H3("Music Across America"),
                    html.P("Explore where live performances are documented across the United States "
                        "and how the country's live-music footprint changes over time."),
                    html.P("Data: Setlist.fm and MusicBrainz",
                           className="source-text"),
                    dbc.Button("Explore the Map",
                               href="/music-map",
                               className="card-button")
                ], className="project-card")
            ], md=4),
            dbc.Col([
                html.Div([
                    html.P("TIME",
                           className="small-label"),
                    html.H3("Anatomy of a Hit"),
                    html.P("Explore how the songs that reach the charts have changed across musical eras "
                        "and what characteristics are associated with chart success."),
                    html.P("Data: Billboard",
                           className="source-text"),
                    dbc.Button("Explore Hit Songs",
                               href="/anatomy-of-a-hit",
                               className="card-button")
                ], className="project-card")
            ], md=4),
            dbc.Col([
                html.Div([
                    html.P("LEGACY",
                           className="small-label"),
                    html.H3("Staying Power"),
                    html.P("Compare artists across generations and examine what separates brief popularity from a lasting musical career."),
                    html.P("Data: Artist longevity metrics",
                           className="source-text"),
                    dbc.Button("Explore Artist Legacy",
                               href="/staying-power",
                               className="card-button")
                ], className="project-card")
            ], md=4)
        ], className="g-4")
    ], className="main-section"),
    dbc.Container([
        html.H2("What We Discover",
                className="section-title"),
        html.P("Once each analysis is complete, we will highlight one major finding from each part of the project here.",
               className="section-text"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.P("PLACE",
                           className="small-label"
                    ),
                    html.H4("Music Map finding coming soon")
                ], className="finding-card")
            ], md=4),
            dbc.Col([
                html.Div([
                    html.P("TIME",
                           className="small-label"),
                    html.H4("Anatomy of a Hit finding coming soon")
                ], className="finding-card")
            ], md=4),
            dbc.Col([
                html.Div([
                    html.P("LEGACY",
                           className="small-label"),
                    html.H4("Staying Power finding coming soon")
                ], className="finding-card")
            ], md=4)
        ], className="g-4")
    ], className="main-section")
])