from dash import (
    Dash,
    html,
    dcc,
    callback,
    Output,
    Input,
    State,
    no_update,
    ctx,
)

import dash_bootstrap_components as dbc
import os
from flask import Flask
import Frontend.frontend_utils as frontu
import random


# =========== Global variables ==============

CATALOG_PATH = "./catalog.yml"

# ====== Initialize the webserver ============

server = Flask(__name__)
server.secret_key = os.urandom(24)

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], server=server)


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
            dbc.ButtonGroup([
                dbc.Button("Random Field", id="btn-random-field", color="primary", outline=False, n_clicks=0),
                dbc.Button("Catalog", id="btn-catalog", color="primary", outline=True, n_clicks=0),
            ], id="mode-toggle"),
        ], width='auto'),
    ], justify="center", class_name="my-2"),

    dbc.Row([
        dbc.Col([
            dcc.Slider(min=0, max=100, marks=None,
                value=10,
                id='exposure-slider',
                updatemode='mouseup',
            ),
            html.Label("Exposure Time", htmlFor="exposure-slider",
                    className="d-block text-center mb-1"),
        ], width=12),
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
    # Random seed for the random field
    dcc.Store(id="field-seed"),

], fluid=True)


@callback(
    Output("main-graph", "figure"),
    Output("field-seed", "data"),
    Input("init-interval", "n_intervals"),
    State("exposure-slider", "value"),
)
def initialize_graph(n, exposure_time):
    seed = random.randrange(2**32)
    fig = frontu.init_graph(catalog_path=CATALOG_PATH, random_field=True,
                             exposure_time=exposure_time, seed=seed)
    
    return fig, seed


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
    Output("btn-random-field", "outline"),
    Output("btn-catalog", "outline"),
    Output("main-graph", "figure", allow_duplicate=True),
    Input("btn-random-field", "n_clicks"),
    Input("btn-catalog", "n_clicks"),
    State("exposure-slider", "value"),
    State("field-seed", "data"),
    prevent_initial_call=True
)
def toggle_view(rf_clicks, cat_clicks, exposure_time, seed):

    random_field_on = ctx.triggered_id == "btn-random-field"

    # update graph
    fig = frontu.init_graph(catalog_path=CATALOG_PATH, random_field=random_field_on, exposure_time=exposure_time, seed=seed)

    return (
        not random_field_on,   # btn-random-field: filled when active
        random_field_on,       # btn-catalog: filled when active
        fig,
    )


@callback(
    Output("main-graph", "figure", allow_duplicate=True),
    Input("exposure-slider", "value"),
    State("btn-random-field", "outline"),
    State("field-seed", "data"),
    prevent_initial_call=True,
)
def update_exposure(exposure_time, rf_outline, seed):
    # btn-random-field is filled (outline=False) exactly when the random field is showing
    random_field_on = not rf_outline
    return frontu.init_graph(catalog_path=CATALOG_PATH, random_field=random_field_on,
                             exposure_time=exposure_time, seed=seed)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
