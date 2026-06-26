"""
Main Dash app for Galaga Lab
"""
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
import galaga_lab.Frontend.frontend_utils as frontu
import random
from importlib.resources import files

# =========== Global variables ==============
#CATALOG_PATH = "./catalog.yml"
CATALOG_PATH = files("galaga_lab") / "catalog.yml"

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
            html.H3("(Ga)laxy and c(L)uster (A)stronomy (G)enerative (A)cademic Lab"),
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
    """Build the initial sky chart with a fresh random field on app load.

    Dash callback fired by the ``init-interval`` timer (typically a one-shot
    interval that ticks once at startup). Generates a new random seed, builds a
    random-field figure via :func:`frontu.init_graph`, and stores the seed so
    the same field can be reproduced or extended by later callbacks.

    Args:
        n (int): Tick count from the ``init-interval`` component. Used only as
            the trigger; the value itself is ignored.
        exposure_time (float): Current value of the ``exposure-slider``, read as
            State and forwarded to the figure builder.

    Returns:
        tuple:
            - plotly.graph_objects.Figure: The assembled sky chart, written to
              ``main-graph.figure``.
            - int: The random seed used, written to ``field-seed.data`` for
              downstream reproducibility.
    """

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
    """Open the info panel for a clicked galaxy marker.

    Dash callback fired when a point on ``main-graph`` is clicked. Reads the
    clicked point's ``customdata`` (the ``[name, notes]`` pair attached by
    :func:`add_object`) and populates the info panel with it. Clicks on points
    that carry no ``customdata`` — such as the graticule lines, labels, or
    boundary — leave the panel untouched.

    Args:
        clickData (dict or None): Plotly click event for ``main-graph``. Expected
            to contain ``points[0].customdata`` as ``[name, notes]`` for galaxy
            markers.

    Returns:
        tuple:
            - bool: Whether the info panel is open, written to
              ``info-panel.is_open``.
            - str: Panel title (galaxy name), written to ``info-panel-title.children``.
            - str: Panel body (galaxy notes), written to ``info-panel-body.children``.

        Returns ``(no_update, no_update, no_update)`` when the clicked point has
        no ``customdata``, leaving the panel in its current state.
    """

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
    """Switch the chart between random-field and catalog views.

    Dash callback fired by either the random-field or catalog button. Determines
    which button was clicked (via ``ctx.triggered_id``), rebuilds the sky chart
    in the corresponding mode through :func:`frontu.init_graph`, and updates both
    buttons' outline state so the active mode reads as filled and the inactive
    one as outlined.

    Args:
        rf_clicks (int): Click count for ``btn-random-field``. Used only to
            trigger the callback; the value is ignored.
        cat_clicks (int): Click count for ``btn-catalog``. Used only to trigger
            the callback; the value is ignored.
        exposure_time (float): Current ``exposure-slider`` value, forwarded to
            the figure builder.
        seed (int or None): Stored field seed from ``field-seed.data``, reused so
            the random field stays consistent with the one created at init.

    Returns:
        tuple:
            - bool: ``btn-random-field.outline`` — False (filled) when random
              field is active, True (outlined) otherwise.
            - bool: ``btn-catalog.outline`` — False (filled) when catalog is
              active, True (outlined) otherwise.
            - plotly.graph_objects.Figure: The rebuilt chart, written to
              ``main-graph.figure``.
    """

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
    """Rebuild the sky chart when the exposure slider changes.

    Dash callback fired by the ``exposure-slider``. Recovers the current view
    mode from the random-field button's outline state, then rebuilds the chart
    at the new exposure via :func:`frontu.init_graph`, preserving whichever mode
    (random field or catalog) is currently displayed.

    Args:
        exposure_time (float): New ``exposure-slider`` value, forwarded to the
            figure builder.
        rf_outline (bool): ``btn-random-field.outline`` state, used to infer the
            current mode. Filled (``outline=False``) means the random field is
            showing; outlined (``outline=True``) means the catalog is showing.
        seed (int or None): Stored field seed from ``field-seed.data``, reused so
            the random field stays consistent across exposure changes. Ignored in
            catalog mode.

    Returns:
        plotly.graph_objects.Figure: The rebuilt chart at the new exposure,
        written to ``main-graph.figure``.
    """

    random_field_on = not rf_outline
    return frontu.init_graph(catalog_path=CATALOG_PATH, random_field=random_field_on,
                             exposure_time=exposure_time, seed=seed)

def galaga_lab():
    """Launch the Dash app and serve the sky-chart dashboard.

    Top-level entry point. Starts the Dash development server (``app.run``),
    which serves the interactive on-sky projection and registers all the
    callbacks defined in this module — initial field generation, galaxy-click
    info panels, random-field/catalog toggling, and exposure updates. Blocks
    until the server is stopped.

    Runs with ``debug=False``, so the app serves in production-style mode (no
    hot reloading, no in-browser error tracebacks).
    """
    app.run(debug=False)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
