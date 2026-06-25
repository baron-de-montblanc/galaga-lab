'''
File for generating the field and functions associated with that
'''
import numpy as np
import plotly.graph_objects as go
from .astro_objects import AstroObject, Galaxy, Cluster
from astropy.cosmology import Planck18 as cosmo

# setting arrays
gal_types = np.array(["elliptical", "lenticular", "spiral", "irregular", "starburst"])
type_weights = np.array([0.20, 0.15, 0.35, 0.20, 0.10])

# helper function
def angular_sizes_from_z(zs, rng, z_ref=0.3, size_ref=1.5, scatter=0.25):
    zs = np.asarray(zs, dtype=float)
    dA = cosmo.angular_diameter_distance(zs).to_value("Mpc")
    dA_ref = cosmo.angular_diameter_distance(z_ref).to_value("Mpc")

    sizes  = size_ref * dA_ref / dA
    sizes *= rng.lognormal(mean=0.0, sigma=scatter, size=zs.shape)
    return sizes

def generate_field(ra_center=180.0, dec_center=0.0, width=4.0, height=4.0, 
                   n_gals=200, n_clusters=2, exposure_time=1, seed=None):
    rng = np.random.default_rng(seed)

    ra_low = ra_center - width/2
    ra_high = ra_center + width/2
    dec_low = dec_center - width/2
    dec_high = dec_center + width/2

    # generate random positions
    ras = rng.uniform(ra_low, ra_high, n_gals)
    sin_1 = np.sin(np.radians(dec_low))
    sin_2 = np.sin(np.radians(dec_high))
    decs = np.degrees(np.arcsin(rng.uniform(sin_1, sin_2, n_gals)))

    # field making
    field = np.array([], dtype=AstroObject)

    zs = rng.gamma(shape=2.0, scale=0.25, size=n_gals)
    types = rng.choice(gal_types, size=n_gals, p=type_weights) 
    masses = np.power(10, rng.uniform(7, 11, n_gals))
    sizes = angular_sizes_from_z(zs, rng)

    for i in range(n_gals): 
        g = Galaxy(ras[i], decs[i], zs[i], name=f"{types[i].capitalize()} gallaxy", 
                   size=sizes[i], sed=types[i], mass=masses[i],
                   exposure_time = exposure_time)
        field = np.append(field, g)
    
    # generate random positions
    cl_ras = rng.uniform(ra_low, ra_high, n_clusters)
    sin_1 = np.sin(np.radians(dec_low))
    sin_2 = np.sin(np.radians(dec_high))
    cl_decs = np.degrees(np.arcsin(rng.uniform(sin_1, sin_2, n_clusters))) 

    for i in range(n_clusters):
        c = Cluster(ra=cl_ras[i], dec=cl_decs[i], z=rng.uniform(0.1, 0.6), 
                    q=rng.uniform(0.5, 1.0), n=int(rng.integers(15, 30)),
                    r=rng.uniform(0.8, 2.0), name=f"gen_cl_{i}", exposure_time=exposure_time)
        field = np.append(field, c)
    
    return field

def visualize_field(field, title='Random galaxy field'): 
    fig = go.Figure() 

    #flattening clusters to galaxies
    gals = np.array([], dtype=Galaxy)
    for object in field: 
        members = getattr(object, "members", None)

        # for clusters
        if members is not None: 
            gals = np.append(gals, members)
        else: #its galaxy
            gals = np.append(gals, object)
    
    # loop over for data visual
    for gal in gals: 
        xs, ys, grid, cs = gal.prepare_figure_data()
        fig.add_trace(go.Heatmap(x=xs, y=ys, z=grid, zmin=0, zmax=1,
                                 colorscale=cs, showscale=False))
    
    dark = "rgb(10, 10, 30)"
    fig.update_layout(title=f"{title} ({len(gals)} objects)",
                      width=700, height=700,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=dark,
                      xaxis_title="RA [pix]", yaxis_title="dec [pix]")
    fig.update_xaxes(autorange="reversed", showgrid=False, zeroline=False)
    fig.update_yaxes(scaleanchor="x", showgrid=False, zeroline=False)
    fig.show()
    return fig




    