'''
File for the DASH interaction side
'''

from astropy.coordinates import SkyCoord
import numpy as np
import plotly.graph_objects as go
import yaml
from astropy import units as u
from Backend.astro_objects import Galaxy, make_wcs
from Backend.generate_field import generate_field


def add_object(fig, galaxy, xs, ys, grid, cs, usename=True):
    """On-Sky Object Position Projection

    Takes in go.Figure object from plotly, a Galaxy object from astro_objects.py and returns 
    a modified graph object for displaying through DASH. 

    Args:
        fig (go.Figure object): go.Figure object from plotly. Typically displaying a Galaxy object.
        ra (np.float): float value; degrees. Right Ascension to put on the on-sky projection. 
        dec (np.float): float value; degrees. Declination to put on the on-sky projection. 
        name (string): string value. Name of object on the sky. 
        color (string): Color of the marker on the graph
        size (int): integer value. Size of object on-sky
    
    Returns:
        fig (go.Figure object): go.Figure object from plotly. Modified graph object for displaying through DASH.
    """

    wcs = make_wcs()
    px = wcs.all_world2pix([[galaxy.coord.ra.deg, galaxy.coord.dec.deg]], 0)[0]

    ra_str  = galaxy.coord.ra.to_string(unit=u.hourangle, sep=('\u02b0', '\u1d50', '\u02e2'), pad=True)
    dec_str = galaxy.coord.dec.to_string(unit=u.deg, sep=('\u00b0', '\u2032', '\u2033'), pad=True, alwayssign=True)

    fig.add_trace(go.Heatmap(
        x          = xs, 
        y          = ys, 
        z          = grid,
        zmin       = 0,
        zmax       = 1,
        colorscale = cs,
        showscale  = False,
    ))

    fig.add_trace(go.Scatter(
        x=[px[0]], y=[px[1]], mode="markers",
        marker=dict(size=6, color="rgba(0,0,0,0)"),
        name=galaxy.name,
        hovertemplate=f"RA: {ra_str}<br>Dec: {dec_str}<extra></extra>",
        customdata=[[galaxy.name, galaxy.notes]],
    ))
    
    if usename:
        fig.add_annotation(
            x=px[0], y=px[1], text=galaxy.name,
            yshift=10, showarrow=False,
            font=dict(color="white", size=10),
        )

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


def add_catalog_objects(fig, catalog_path, exposure_time):
    """
    Loads in the catalog.yaml file and adds all objects to the graph. Calls add_object()
    """
    with open(catalog_path, "r") as f:
        catalog = yaml.safe_load(f)

    for obj in catalog["objects"]:

        coord  = SkyCoord(ra=obj["ra"], dec=obj["dec"], unit=(u.hourangle, u.deg))
        galaxy = Galaxy(
                ra            = coord.ra.to(u.deg).value,
                dec           = coord.dec.to(u.deg).value, 
                z             = float(obj["redshift"]), 
                name          = obj["name"],
                mass          = float(obj["mass_msun"]),
                q             = float(obj["q"]),
                type          = obj["type"],
                size          = float(obj["size_arcmin"]),
                notes         = obj["notes"],
                exposure_time = exposure_time,
            )

        xs, ys, grid, cs = galaxy.prepare_figure_data()
        fig = add_object(fig, galaxy, xs, ys, grid, cs, usename=True)

    return fig


def add_random_field(fig, exposure_time, seed):
    """
    Add random galaxy/cluster field instead of calatog objects
    """

    field = generate_field(ra_center=180.0, dec_center=0.0, width=360.0, height=180.0, 
                           n_gals=200, n_clusters=5, seed=None, exposure_time=5)
    
    for object in field:

        if isinstance(object, Galaxy):
            xs, ys, grid, cs = object.prepare_figure_data()
            fig = add_object(fig, object, xs, ys, grid, cs, usename=False)

        else:
            for galaxy in object.members:
                xs, ys, grid, cs = galaxy.prepare_figure_data()
                fig = add_object(fig, galaxy, xs, ys, grid, cs, usename=False)
    
    return fig



def init_graph(catalog_path, exposure_time, random_field=False, seed=None):
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
        paper_bgcolor="#111111",
        plot_bgcolor="#111111",
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


    # Now add objects
    if random_field:
        fig = add_random_field(fig, exposure_time=exposure_time, seed=seed)
    else:
        fig = add_catalog_objects(fig, catalog_path=catalog_path, exposure_time=exposure_time)

    return fig
