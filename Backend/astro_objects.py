'''
File for classes and making the astro objects class and any subclasses/objects for galaxies, etc

Fill out docstrings...
'''

import numpy as np
from astropy.cosmology import Planck18 as cosmo
import plotly.graph_objects as go

'''
SED Template: Spectral Energy Distribution is a galaxy's brightness as wavelength
Instead of modeling, just give it an approximated "type" by a dictionary that captures: 
1. base_color (intrisic g-r color)
2. mass_to_light (solar masses per solar luminosity)
ordered from red to blue

Wikipedia: elliptical and lenticular galaxies typically appearing redder due to older stellar populations, 
while spiral and irregular galaxies are often bluer, indicating ongoing star formation

Just kinda picked at random with minor amounts of logic
'''

SED_TEMPLATES = {"elliptical": (0.80, 3.0), "lenticular": (0.72, 2.5), "spiral": (0.55, 1.8),
                 "irregular": (0.42, 1.2), "starburst":  (0.30, 0.8)}


class AstroObject: 
    def __init__(self, ra, dec, z):
        self.ra = ra
        self.dec = dec 
        self.z = z
        self.d = cosmo.luminosity_distance(z).to_value("Mpc")
        self.color = 0
        self.mag = 0

    ## some shared physics/cosmology/coloring/display stuff
    def distance_modulus(self): 
        """
        apparent/absolute with z
        """
        return cosmo.distmod(self.z).value
    
    def get_hue(self): 
        '''
        Map color index (g-r) to an rgb string
        blue (~0.3) -> red (~0.9)

        Normalize the color over the [0,1] range for easier coloring
        Interpolate between a blue and a red rgb sequence
        Makes a direct blue-to-red scale
        '''
        c = np.clip((self.color - 0.3) / 0.6, 0.0, 1.0) #"clips" color to 0, 1
        blue = np.array([150, 180, 255])
        red = np.array([255, 140, 110])
        r, g, b = (blue + c*(red-blue)).astype(int)
        return f"rgb({r}, {g}, {b})" #formatted this way for plotly 
    
    def peak_brightness(self):
        '''
        map magnitude to a peak brightness
        range it [0.05, 1] to test...
        Larger mag (fainter) = dimmer
        Less than 15 mag is the "core" 
        Greater than 25 (LSST depths) is 0.05, linear between (just for display)
        '''
        faint = 25.0
        bright = 15.0

        p = (faint - self.mag) / (faint-bright)
        return float(np.clip(p, 0.05, 1.0))
    
    def finish_visualize(self, fig, title):

        dark = "rgb(10, 10, 30)"   # matching later colorscale I think
        fig.update_layout(title=title, width=600, height=600,
            paper_bgcolor="rgba(0,0,0,0)", # transparent around the plot
            plot_bgcolor=dark, # dark "sky" look
            xaxis_title="RA [deg]", yaxis_title="dec [deg]")
        fig.update_xaxes(autorange="reversed", showgrid=False, zeroline=False)
        fig.update_yaxes(scaleanchor="x", showgrid=False, zeroline=False)
        fig.show()
        return fig

class Galaxy(AstroObject): 
    def __init__(self, ra, dec, z, q=1, mass=1e12, lensed=False, sed = 'None', agn_lum = 0.0):
        super().__init__(ra, dec, z)
        self.q = q #axis ratio
        self.angle = 0 #eventually add random axis-tilt for display
        self.mass = mass #solar masses, to use astropy units? Not necessary?
        #self.lensed = lensed 
        self.sed = sed #for stellar population type
        self.agn = agn_lum #AGN activity

        #setting colors
        self.color = self.estimate_color()
        self.mag = self.estimate_mag()
    
    def get_sed_template(self):
        return SED_TEMPLATES.get(self.sed, SED_TEMPLATES["spiral"])

    def estimate_color(self):
        #pull template
        base_color = self.get_sed_template()[0]

        #crude redshift color shift
        color = base_color + 0.3 * self.z
        self.color = color
        return self.color 
    
    def estimate_mag(self): 
        #estimate magnitude based on mass, type, z, d, and m
        dist_mod = self.distance_modulus() #should just call astropy

        #get luminosity
        mass_to_light = self.get_sed_template()[1]
        stellar_lum = self.mass / mass_to_light #should by the solar luminosities
        lum = stellar_lum + self.agn #adds AGN light
        
        M_sun_r = 4.83 # solar absolute magnitude

        #lum to abs mag
        abs_mag = M_sun_r - 2.5*np.log10(lum)

        #abs mag to app mag
        self.mag = abs_mag + dist_mod

        return self.mag
    
    def visualize(self): 
        #temporarily build fake sky grid centered on galaxy
        width = 0.01
        n_pix = 200 

        xs = np.linspace(self.ra - width, self.ra + width, n_pix)
        ys = np.linspace(self.dec - width, self.dec + width, n_pix)
        X, Y = np.meshgrid(xs, ys) #builds grid

        #offsets for angles ("zeroing") 
        dx, dy = X - self.ra, Y-self.dec 

        #rotate coords for tilt of ellipse
        th = np.radians(self.angle)
        xr = dx*np.cos(th) + dy*np.sin(th)
        yr = -dx*np.sin(th) + dy*np.cos(th)

        #squash with ellipiticity
        size = width/3.0
        r2 = (xr / size) ** 2 + (yr / (size * self.q)) ** 2 #ellipticity equation

        # surface brightness gaussian -> bright core, faint edges
        # scaled by peak_brightness() so fainter galaxies render dimmer overall
        grid = self.peak_brightness() * np.exp(-0.5 * r2)

        # near-black background at 0 up to the galaxy's hue at 1
        cs = [[0.0, "rgb(10,10,30)"], [1.0, self.get_hue()]]
        fig = go.Figure(go.Heatmap(x=xs, y=ys, z=grid, zmin=0, zmax=1, colorscale=cs, showscale=False))

        return self.finish_visualize(fig, f"Galaxy with z={self.z} and {self.color:.2f}")