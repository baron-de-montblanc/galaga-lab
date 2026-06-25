'''
File for classes and making the astro objects class and any subclasses/objects for galaxies, etc

Fill out docstrings...

Things to add: 
1. Ellipticity range dependent on SED type
2. Exposure-time-dependence so 
'''

import numpy as np
from astropy.cosmology import Planck18 as cosmo
import plotly.graph_objects as go
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.wcs import WCS

'''
SED Template: Spectral Energy Distribution is a galaxy's brightness as wavelength
Instead of modeling, just an approximated "type" by a dictionary that captures: 
1. base_color (intrisic g-r color)
2. mass_to_light (solar masses per solar luminosity)
ordered from red to blue

Wikipedia: elliptical and lenticular galaxies typically appearing redder due to older stellar populations, 
while spiral and irregular galaxies are often bluer, indicating ongoing star formation

Just kinda picked at random with minor amounts of logic
'''

SED_TEMPLATES = {"elliptical": (0.80, 3.0), "lenticular": (0.72, 2.5), "spiral": (0.55, 1.8),
                 "irregular": (0.42, 1.2), "starburst":  (0.30, 0.8)}


# Shared helper function
def make_wcs():
        wcs = WCS(naxis=2)
        wcs.wcs.crpix = [0, 0]
        wcs.wcs.cdelt = [1.0, 1.0]
        wcs.wcs.crval = [180, 0]          # center of projection
        wcs.wcs.ctype = ["RA---AIT", "DEC--AIT"]
        return wcs


class AstroObject: 
    def __init__(self, ra, dec, z, name=None, exposure_time=1.0):
        """
        ra, dec in degrees
        """
        self.ra    = ra
        self.dec   = dec 
        self.coord = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg))
        self.z     = z
        self.name  = name
        self.d     = cosmo.luminosity_distance(z).to_value("Mpc")
        self.color = 0
        self.mag   = 0
        self.exposure_time = exposure_time

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
        c    = np.clip((self.color - 0.3) / 0.6, 0.0, 1.0) #"clips" color to 0, 1
        blue = np.array([150, 180, 255])
        red  = np.array([255, 140, 110])

        r, g, b = (blue + c*(red-blue)).astype(int)
        return f"rgb({r}, {g}, {b})" #formatted this way for plotly 
    
    def peak_brightness(self, faint=25.0, bright=15.0, exposure_time=None):
        '''
        map magnitude to a peak brightness
        range it [0.05, 1] to test...
        Larger mag (fainter) = dimmer
        Less than 15 mag is the "core" 
        Greater than 25 (LSST depths) is 0.05, linear between (just for display)
        '''
        # easier integration to slider maybe?
        if exposure_time is None:
            exposure_time = self.exposure_time
        
        '''
        Could just do 
        for galaxy in the field: 
            set self.exposure_time to current slider value
        '''

        exposure_time = max(exposure_time, 1e-3)   # make slider min > 0

        floor = 0.12
        ceiling = 1.5 #was 1.0, 2.0 a bit too bright
        DEPTH_GAIN = 2.0 #for how "sensitive" the slider is/an object is to exposure time; 1.25 is realistic but unresponsive

        m_lim = faint + DEPTH_GAIN * np.log10(exposure_time)

        p = (m_lim - self.mag) / (faint - bright)
        return float(np.clip(p, floor, ceiling))
    
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
    def __init__(self, ra, dec, z, name, exposure_time,
            size    = 7, 
            type    = "spiral", 
            q       = 1,
            mass    = 1e12, 
            lensed  = False, 
            sed     = 'None', 
            agn_lum = 0.0,
            notes   = "",
            ):
        super().__init__(ra, dec, z, name, exposure_time)
        self.q     = q       # axis ratio
        self.angle = 0       # eventually add random axis-tilt for display
        self.mass  = mass    # solar masses
        #self.lensed = lensed 
        self.sed   = sed     # for stellar population type
        self.agn   = agn_lum # AGN activity
        self.type  = type    # Galaxy type
        self.size  = size    # Angular diameter in arcmin
        self.notes = notes   # string that describes the object

        #setting colors
        self.color = self.estimate_color()
        self.mag   = self.estimate_mag()
    
    def get_sed_template(self):
        return SED_TEMPLATES.get(self.sed, SED_TEMPLATES[self.type])

    def estimate_color(self):
        #pull template
        base_color = self.get_sed_template()[0]

        #crude redshift color shift
        color = base_color + self.z
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


    def prepare_figure_data(self):
        '''
        possible: incorporate ang diameter distance instead of div by 5
        '''
        sky_width_deg = self.size  # scale actual object size to size on the plot
        
        wcs = make_wcs()

        # Find pixel position of galaxy center
        cx, cy = wcs.all_world2pix([[self.ra, self.dec]], 0)[0]

        edge_ra  = wcs.all_world2pix([[self.ra + sky_width_deg, self.dec]], 0)[0][0]
        pix_width = abs(edge_ra - cx)

        n_pix = 200
        xs = np.linspace(cx - pix_width, cx + pix_width, n_pix)
        ys = np.linspace(cy - pix_width, cy + pix_width, n_pix)
        X, Y = np.meshgrid(xs, ys)

        dx, dy = X - cx, Y - cy

        th = np.radians(self.angle)
        xr = dx * np.cos(th) + dy * np.sin(th)
        yr = -dx * np.sin(th) + dy * np.cos(th)

        size = pix_width / 3.0
        r2 = (xr / size) ** 2 + (yr / (size * self.q)) ** 2

        grid = self.peak_brightness() * np.exp(-0.5 * r2)
        cs = [[0.0, "rgba(0,0,0,0)"], [1.0, self.get_hue()]]

        return xs, ys, grid, cs


    def visualize(self): 
        
        xs, ys, grid, cs = self.prepare_figure_data()
        fig = go.Figure(go.Heatmap(x=xs, y=ys, z=grid, zmin=0, zmax=1, colorscale=cs, showscale=False))

        return self.finish_visualize(fig, f"Galaxy with z={self.z} and {self.color:.2f}")

'''
Cluster class
'''    
class Cluster(AstroObject):
    def __init__ (self, ra, dec, z, name, q, n, r, exposure_time, bcg_scale=1.5):
        super().__init__(ra, dec, z, name, exposure_time)
        self.q = q # squash factor of cluster from y-axis
        self.ra = ra #Right Ascention, equatorial positon in sky
        self.dec = dec #Declination, angular distance from the equator
        self.z = z #Redshift
        self.n = n #Number of galaxies in cluster
        self.r = r #Radius of the cluster
        self.cluster_size = 0
        self.bcg_scale = bcg_scale
        self.members = self.generate_members() # initializes the cluster with its members

    def generate_members(self):
        '''
        four major arrrays: galaxy types, list of random masses for individual points, 
        ra and dec of all points
        '''
        #Galaxy RAs and Decs
        r_Mpc = self.r # radius of cluster in Mpc
        dA_Mpc = cosmo.angular_diameter_distance(self.z).value # distance from observer to cluster in Mpc
        cluster_size = np.degrees(r_Mpc/dA_Mpc) * 50 # gets angular size of cluster in degrees (from rads) and scales up
        self.cluster_size = cluster_size #saving this for later

        dx = np.random.normal(0, cluster_size, self.n) # returns array of random positions along x axis (RA)
        dy = self.q * np.random.normal(0, cluster_size, self.n) # returns array of random positions along y axis (dec), with a boundary defined by q
        cluster_ras = self.ra + dx # random list of individual galaxies' RAs in cluster 
        cluster_decs = self.dec + dy # random list of individual galaxies' decs in cluster 
        orient_angle = np.random.uniform(0, np.pi)
        
        #Galaxy masses
        cluster_ms = np.power(10, np.random.uniform(9, 11, self.n)) # generates array of standard masses for cluster galaxies

        #Galaxy redshifts
        cluster_zs = np.random.normal(0, 0.005, self.n) + self.z # generates array of cluster galaxy redshift

        #cluster_members = np.zeros(self.n)

        #Galaxy Types
        gal_types = np.array(["elliptical", "spiral", "irregular"])
        cl_gal_types = np.random.choice(gal_types, self.n, p=np.array([0.7,0.2,0.1]))

        # fix by appending instead of initializing
        '''
        cluster_members = np.array([], dtype=Galaxy)
        for i in range(self.n):
            gal= Galaxy(cluster_ras[i], cluster_decs[i], cluster_zs[i], cluster_ms[i], sed = cl_gal_types[i])
            cluster_members = np.append(cluster_members, gal)
        '''

        # loops over members to properly create Galaxy objects
        cluster_members = np.array([], dtype=Galaxy)

        # adjust size for jade's code
        member_size = cluster_size / 5

        for i in range(self.n):
            gal = Galaxy(cluster_ras[i], cluster_decs[i], cluster_zs[i],
                name=f"member_{i}", size=member_size, mass=cluster_ms[i], sed=cl_gal_types[i], exposure_time=self.exposure_time)
            cluster_members = np.append(cluster_members, gal)

        # add BCG
        bcg_name = f"BCG of {self.name}"
        bcg_size = member_size * self.bcg_scale #before doing this it gave a cool DM halo visualization
        bcg = Galaxy(self.ra, self.dec, self.z, q=0.7, mass=1e12, sed="elliptical",
                      name=bcg_name, 
                      size=bcg_size, exposure_time=self.exposure_time)
        bcg.angle = np.random.uniform(0, 180)
        cluster_members = np.insert(cluster_members, 0, bcg)

        return cluster_members
    
    def visualize_cluster(self):
        '''
        Visualize the cluster independently for testing
        '''
        cluster_fig = go.Figure()

        for galaxy in self.members: 
            xs, ys, grid, cs = galaxy.prepare_figure_data() 

            cluster_fig.add_trace(go.Heatmap(x=xs, y=ys, z=grid, 
                                zmin=0, zmax=1, colorscale=cs, showscale=False))
            
            title = f"Cluster at z={self.z:.3f} with {self.n} members"
        
        return self.finish_visualize(cluster_fig, title)



       



        