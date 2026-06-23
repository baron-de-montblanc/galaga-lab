'''
File for the DASH interaction side
'''

from astropy.coordinates import SkyCoord
import numpy as np
import plotly.graph_objects as go
import yaml
from astropy import units as u

from Backend.astro_objects import Galaxy, make_wcs


def add_object(fig, galaxy, xs, ys, grid, cs, color='red', size=8):

    wcs = make_wcs()
    px = wcs.all_world2pix([[galaxy.coord.ra.deg, galaxy.coord.dec.deg]], 0)[0]

    ra_str  = galaxy.coord.ra.to_string(unit=u.hourangle, sep=('\u02b0', '\u1d50', '\u02e2'), pad=True)
    dec_str = galaxy.coord.dec.to_string(unit=u.deg, sep=('\u00b0', '\u2032', '\u2033'), pad=True, alwayssign=True)

    fig.add_trace(go.Heatmap(
        x=xs, y=ys, z=grid,
        zmin=0, zmax=1,
        colorscale=cs,
        showscale=False,
    ))

    fig.add_trace(go.Scatter(
        x=[px[0]],
        y=[px[1]],
        mode="markers+text" if galaxy.name else "markers",
        marker=dict(color=color, size=size, symbol="circle",
            line=dict(color="white", width=0.5),
            opacity=0),
        text=[galaxy.name],
        textposition="top center",
        textfont=dict(color="white", size=10),
        name=galaxy.name or f"RA={galaxy.ra} Dec={galaxy.dec}",
        hovertemplate=(
            f"RA: {ra_str}<br>"
            f"Dec: {dec_str}<extra></extra>"
        ),
    ))

    fig.update_layout(
        hoverlabel=dict(
            bgcolor="rgba(20, 20, 50, 0.9)",   # background color
            bordercolor="rgba(255,255,255,0.3)", # border color
            font=dict(
                color="white",
                size=13,
                family="monospace",
            ),
        )
    )

    return fig


def add_catalog_objects(fig, catalog_path):
    """
    Loads in the catalog.yaml file and adds all objects to the graph. Calls add_object()
    """
    with open(catalog_path, "r") as f:
        catalog = yaml.safe_load(f)

    for obj in catalog["objects"]:

        coord  = SkyCoord(ra=obj["ra"], dec=obj["dec"], unit=(u.hourangle, u.deg))
        galaxy = Galaxy(
                ra   = coord.ra.to(u.deg).value,
                dec  = coord.dec.to(u.deg).value, 
                z    = float(obj["redshift"]), 
                name = obj["name"],
                mass = float(obj["mass_msun"]),
                q    = float(obj["q"]),
                type = obj["type"],
                size = float(obj["size_arcmin"]),
            )

        xs, ys, grid, cs = galaxy.prepare_figure_data()

        fig = add_object(fig, galaxy, xs, ys, grid, cs)

    return fig


def init_graph(catalog_path):
    """
    Build and return the empty sky-chart figure using astropy
    """
    wcs        = make_wcs()
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
