from dash import (
    Dash,
    html,
    dcc,
    callback,
    Output,
    Input,
    State,
    no_update,
    callback_context,
    ALL,
)

import dash
import math
import numpy as np
import plotly.graph_objects as go
import plotly.colors as colors
import dash_bootstrap_components as dbc
import json
import re
import uuid
import os

from flask import session, Flask

import galaga_lab.Frontend.frontend_utils as frontu


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

    # Fires once on page load
    dcc.Interval(id="init-interval", interval=1, max_intervals=1),

], fluid=True)


@callback(
    Output("main-graph", "figure"),
    Input("init-interval", "n_intervals"),
)
def initialize_graph(n):
    return frontu.init_graph(catalog_path=CATALOG_PATH)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
