'''
File for the DASH interaction side
'''

from astropy.wcs import WCS
import numpy as np
import plotly.graph_objects as go
import yaml


def add_object(fig, ra, dec, name, color="#44D9E9", size=8):
    """
    Takes in a go.Figure object and an RA/Dec value (in degrees).
    Adds a dot at the projected Hammer-Aitoff location.
    Returns the modified figure.
    """
    wcs = _make_wcs()
    px = wcs.all_world2pix([[ra, dec]], 0)[0]

    fig.add_trace(go.Scatter(
        x=[px[0]],
        y=[px[1]],
        mode="markers+text" if name else "markers",
        marker=dict(color=color, size=size, symbol="circle",
                    line=dict(color="white", width=0.5)),
        text=[name],
        textposition="top center",
        textfont=dict(color="white", size=10),
        name=name or f"RA={ra} Dec={dec}",
        hovertemplate=(
            f"<b>{name}</b><br>"
            f"RA: {ra:.4f}°<br>"
            f"Dec: {dec:.4f}°<extra></extra>"
        ),
    ))

    return fig


def add_catalog_objects(fig, catalog_path):
    """
    Loads in the catalog.yaml file and adds all objects to the graph. Calls add_object()
    """
    with open(catalog_path, "r") as f:
        catalog = yaml.safe_load(f)

    for obj in catalog["objects"]:
        fig = add_object(fig, ra=obj["ra"], dec=obj["dec"], name=obj["name"])

    return fig


def _make_wcs():
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [0, 0]
    wcs.wcs.cdelt = [1.0, 1.0]
    wcs.wcs.crval = [180, 0]          # center of projection
    wcs.wcs.ctype = ["RA---AIT", "DEC--AIT"]
    return wcs


def init_graph(catalog_path):
    """
    Build and return the empty sky-chart figure using astropy
    """
    wcs        = _make_wcs()
    n_pts      = 400
    grid_color = "rgba(255,255,255,0.15)"
    label_color= "rgba(255,255,255,0.55)"
    traces     = []

    # ── Dec parallels (sweeps through RA) ──────────────────────────
    ra_sweep = np.linspace(0.5, 359.5, n_pts)
    for dec in range(-90, 91, 15):
        sky = np.column_stack([ra_sweep, np.full(n_pts, float(dec))])
        px  = wcs.all_world2pix(sky, 0)
        traces.append(go.Scatter(
            x=px[:, 0], y=px[:, 1],
            mode="lines",
            line=dict(color=grid_color, width=0.8),
            hoverinfo="skip",
            showlegend=False,
        ))
        # Label on the central meridian (RA = 180)
        lx, ly = wcs.all_world2pix([[180, dec]], 0)[0]
        traces.append(go.Scatter(
            x=[lx + 3], y=[ly],
            mode="text",
            text=[f"{dec:+d}°"],
            textfont=dict(color=label_color, size=9),
            hoverinfo="skip",
            showlegend=False,
        ))

    # ── RA meridians (sweeps through Dec) ─────────────────────────
    dec_sweep = np.linspace(-89.9, 89.9, n_pts)
    for ra_h in range(0, 24):
        ra_deg = ra_h * 15.0
        sky = np.column_stack([np.full(n_pts, ra_deg), dec_sweep])
        px  = wcs.all_world2pix(sky, 0)
        traces.append(go.Scatter(
            x=px[:, 0], y=px[:, 1],
            mode="lines",
            line=dict(color=grid_color, width=0.8),
            hoverinfo="skip",
            showlegend=False,
        ))
        # Label along the equator (Dec = 0)
        lx, ly = wcs.all_world2pix([[ra_deg, 0]], 0)[0]
        traces.append(go.Scatter(
            x=[lx], y=[ly - 6],
            mode="text",
            text=[f"{ra_h}h"],
            textfont=dict(color=label_color, size=9),
            hoverinfo="skip",
            showlegend=False,
        ))

    # ── Outer boundary ellipse ────────────────────────────────────────────────
    theta = np.linspace(0, 2 * np.pi, 500)
    # boundary in WCS pixel coords
    bx = 163.0 * np.cos(theta)
    by =  82.0 * np.sin(theta)
    traces.append(go.Scatter(
        x=bx, y=by,
        mode="lines",
        line=dict(color="rgba(255,255,255,0.35)", width=1.2),
        hoverinfo="skip",
        showlegend=False,
    ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor="#1A0933",
        plot_bgcolor="#1A0933",
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(
            visible=False,
            range=[-175, 175],
            scaleanchor="y",
            scaleratio=1,
        ),
        yaxis=dict(
            visible=False,
            range=[-95, 95],
        ),
        showlegend=False,
        dragmode="pan",
    )


    # Now add catalog objects
    fig = add_catalog_objects(fig, catalog_path=catalog_path)

    return fig
