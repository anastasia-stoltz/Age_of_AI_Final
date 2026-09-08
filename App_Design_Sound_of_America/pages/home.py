import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__,
    path="/",
    name="Home")

layout = html.Div([
    html.Div([
        dbc.Container([
            html.P("AN INTERACTIVE MUSIC ATLAS",
                   className="small-label"
            ),
            html.H1("The Sound of America",
                    className="main-title"
            ),
            html.Div(className="title-rule"),
            html.H3("How does American music change across place, time, and artists?",
                    className="main-question"
            ),
            html.P("Explore live music across the United States, how long hit songs stay on the charts, and the artists whose careers continue to endure.",
                   className="intro-text"
            ),
            dbc.Button("Explore the Music Map",
                       href="/music-map",
                       className="main-button"
            ),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.P("PLACE",
                               className="small-label"
                        ),
                        html.H4("Where music happens"),
                        html.P("Explore the geography of live music.")
                    ], className="story-item")
                ], md=4),
                dbc.Col([
                    html.Div([
                        html.P("TIME",
                               className="small-label"
                        ),
                        html.H4("How hits survive"),
                        html.P("See how the lifespan of chart success changes across eras.")
                    ], className="story-item")
                ], md=4),
                dbc.Col([
                    html.Div([
                        html.P("LEGACY",
                               className="small-label"
                        ),
                        html.H4("Who endures"),
                        html.P("Compare artists whose success stretches across generations.")
                    ], className="story-item")
                ], md=4)
            ], className="story-row")
        ])
    ], className="intro-section"),

    html.Div([
        dbc.Container([
            html.P("EXPLORE THE PROJECT",
                   className="section-label-light"
            ),
            html.H2("Three lenses. One musical story.",
                    className="section-title"
            ),
            html.P("Move from geography to chart history to artist longevity to see American music from three connected perspectives.",
                   className="section-text"
            ),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.P("01 · PLACE",
                               className="small-label"
                        ),
                        html.H3("Music Across America"),
                        html.P("Explore where live performances are documented across the United States and how the country's live-music footprint changes over time."),
                        html.P("Data: Setlist.fm and MusicBrainz",
                               className="source-text"
                        ),
                        dbc.Button("Explore the Map",
                                   href="/music-map",
                                   className="card-button"
                        )
                    ], className="project-card")
                ], md=4),
                dbc.Col([
                    html.Div([
                        html.P("02 · TIME",
                               className="small-label"
                        ),
                        html.H3("Lifespan of a Hit"),

                        html.P("Explore how long Billboard hits survive on the charts and how that has changed across eras."),
                        html.P("Data: Billboard Hot 100",
                               className="source-text"
                        ),
                        dbc.Button("Explore Hit Lifespans",
                                   href="/anatomy-of-a-hit",
                                   className="card-button"
                        )
                    ], className="project-card")
                ], md=4),
                dbc.Col([
                    html.Div([
                        html.P("03 · LEGACY",
                               className="small-label"
                        ),
                        html.H3("Staying Power"),
                        html.P("Compare artists across generations and examine what separates brief popularity from a lasting musical career."),
                        html.P("Data: Artist longevity metrics",
                               className="source-text"
                        ),
                        dbc.Button("Explore Artist Legacy",
                                   href="/staying-power",
                                   className="card-button"
                        )
                    ], className="project-card")
                ], md=4)
            ], className="g-4")
        ], className="main-section")
    ], className="project-section"),

    html.Div([
        dbc.Container([
            html.P("THE BIG PICTURE",
                   className="small-label"
            ),
            html.H2("American music is not one story.",
                    className="section-title"
            ),
            html.P("It is a geography, a changing chart, and a career over time. The Sound of America brings those perspectives together so users can move from where music happens, to how songs perform, to which artists endure.",
                   className="closing-text"
            )
        ], className="main-section")
    ], className="closing-section")
])