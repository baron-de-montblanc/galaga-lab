from dash import (
    Dash,
    html,
    dcc,
    callback,
    Output,
    Input,
    no_update,
)

import dash_bootstrap_components as dbc
import os

from flask import Flask

import Frontend.frontend_utils as frontu


# =========== Global variables ==============

CATALOG_PATH = "./catalog.yml"

# ====== Initialize the webserver ============

server = Flask(__name__)
server.secret_key = os.urandom(24)

app = Dash(__name__, external_stylesheets=[dbc.themes.VAPOR], server=server)


app.layout = dbc.Container([

    dbc.Row([

        dbc.Col(
            html.H1("GALAGA LAB"),
            width=12, className="text-center"
        ),

    ], className="my-2"),

    dbc.Row([
        dbc.Col(
            dcc.Graph(id="main-graph", style={"width": "100%", "height": "70vh"}),
            width=12, className="mb-0"
        ),
    ], className="mt-0", justify="center", align="center"),

    dbc.Row([
        dbc.Col([
            dbc.Button([
                html.Span("Random Field", style={"display": "block", "font-size": "16px"}),
                html.Span("ON", style={"display": "block", "font-size": "12px", "margin-top": "4px"}, id="on-off-switch"),
            ], id="toggle-button", style={"text-align": "center", "flex":"1"}, outline=False, color="primary", n_clicks=0),
        ], width='auto'),
    ]),

    dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle(id="info-panel-title", style={
                "position": "absolute",
                "left": "50%",
                "transform": "translateX(-50%)",
            }),
            className="position-relative",
        ),
        dbc.ModalBody(id="info-panel-body", className="text-center"),
    ], id="info-panel", is_open=False, size="md"),

    # Fires once on page load
    dcc.Interval(id="init-interval", interval=1, max_intervals=1),

], fluid=True)


@callback(
    Output("main-graph", "figure"),
    Input("init-interval", "n_intervals"),
)
def initialize_graph(n):
    return frontu.init_graph(catalog_path=CATALOG_PATH, random_field=True)


@callback(
    Output("info-panel", "is_open"),
    Output("info-panel-title", "children"),
    Output("info-panel-body", "children"),
    Input("main-graph", "clickData"),
    prevent_initial_call=True,
)
def on_galaxy_click(clickData):
    if not clickData:
        return False, "", ""

    point = clickData["points"][0]
    if "customdata" not in point:
        return no_update, no_update, no_update

    name, notes = point["customdata"]
    return True, name, notes


@callback(
        Output("toggle-button", "outline"),
        Output("on-off-switch", "children"),
        Output("main-graph", "figure", allow_duplicate=True),
        Input("toggle-button", "n_clicks"),
        prevent_initial_call=True
)
def toggle_flags(nclicks):

    random_field_on = nclicks % 2 == 0

    # update graph
    fig = frontu.init_graph(catalog_path=CATALOG_PATH, random_field=random_field_on)

    return (
        not random_field_on,
        "ON" if random_field_on else "OFF",
        fig,
    )


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
