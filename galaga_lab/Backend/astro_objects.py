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
STARFORMING = {"spiral", "irregular", "starburst"}

SED_TEMPLATES = {"elliptical": (0.80, 3.0), "lenticular": (0.72, 2.5), "spiral": (0.55, 1.8),
                 "irregular": (0.42, 1.2), "starburst":  (0.30, 0.8)}

GAL_TRIVIA =   {   "elliptical":    [
                                        "Ellliptical galaxies store all the retired stars. All of them are old and red, with too little gas left to make new ones.",
                                        "An elliptical galaxy like this likely grew this big by swalloring up smaller galaxies over billions of years in events called mergers."
                                    ], 
                    "lenticular":   [
                                        "Lenticular galaxies have a disk like a spiral, but are like elliptical galaxies in that they have little star-forming gas left.",
                                        "Lenticular galaxies are like a spiral galaxies that just relaxed and chilled out."
                                    ], 
                    "spiral":       [
                                        "The \"arms\" in the spiral shapes of these galaxies are stellar nurseries: Bright regions where new stars are constantly being born, emitting blue light.",
                                        "Our own Milky Way is a spiral galaxy like this one, so we're constantly getting new stellar siblings!"
                                    ],
                    "irregular":    [
                                        "Irregular galaxies are often chaotic in shape, due to collisions or gravitational tugs with neighbors.",
                                        "Most are small and have a ton of star-forming gas, but lack the structure of spiral galaxies."
                                    ], 
                    "starburst":    [
                                        "Starburst galaxies form stars faster than other star-forming galaxies, hence the name!",
                                        "This galaxy has likely just merged with another, giving it a ton of new gas to make stars with."
                                    ]
                }

# name helper functions
def mass_phrase(mass):
    """Format a mass as a human-readable phrase, e.g. "3 trillion".

    Args:
        mass (float): Mass in solar masses.

    Returns:
        str: Mass rounded to a whole number with a magnitude word
            ("million", "billion", or "trillion").
    """
    if mass >= 1e12: 
        return f"{mass/1e12:.0f} trillion"
    if mass >= 1e9:  
        return f"{mass/1e9:.0f} billion"
    return f"{mass/1e6:.0f} million"


def distance_phrase(d_mpc): 
    """Format a distance as a human-readable phrase, e.g. "1.4 billion light-years".

    Args:
        d_mpc (float): Distance in megaparsecs.

    Returns:
        str: Distance converted to light-years with a magnitude word
            ("million" below 1000 Mly, otherwise "billion").
    """
    mly = d_mpc * 3.262 
    if mly < 1000: 
        return f"{mly:,.0f} million light-years"
    return f"{mly/1000:.1f} billion light-years"


def visibility(mag): 
    """Classify how hard an object is to observe from its magnitude.

    Args:
        mag (float): Apparent magnitude (brighter objects have lower values).

    Returns:
        str: "easy" (mag < 20), "moderate" (20 <= mag < 23), or "hard" (mag >= 23).
    """
    if mag < 20: 
        return "easy"
    if mag < 23: 
        return "moderate"
    return "hard"


def redshift_note(z):
    """Return a plain-language note describing an object's redshift.

    Args:
        z (float): Redshift.

    Returns:
        str: A descriptive sentence whose tone scales with z, from a nearby
            neighbor (z < 0.1) up through the early universe (z >= 1.5).
    """
    if z < 0.1:  
        return "It's one of our cosmic neighbors, relatively close by."
    if z < 0.3:  
        return "Its light traveled a good chunk of cosmic history to reach us, being slightly stretched to redder light in a process called redshifting."
    if z < 0.7:  
        return "We see it as it was billions of years ago, a window into the younger universe, stretched by space itself expanding into redder light."
    if z < 1.5:  
        return "Cosmic expansion has noticeably stretched its light toward the red, and we're seeing it when the universe was much younger."
    return "Its light has been stretched dramatically by the expansion of the universe, carrying an image of the early universe."


def cluster_designation(ra, dec):
    """Build a cluster's catalog designation from its coordinates.

    Args:
        ra (float): Right ascension in degrees.
        dec (float): Declination in degrees.

    Returns:
        str: A name like "Cluster J180.5+12.3", with a signed declination.
    """
    if dec >= 0:
        sign = "+"  
    else: 
        sign = "-"
    return f"Cluster J{ra:.1f}{sign}{abs(dec):.1f}"


def sat_sentence(cluster_name, bcg_name): 
    """Build a sentence describing a satellite galaxy's cluster membership.

    Args:
        cluster_name (str): Name of the host cluster.
        bcg_name (str): Name of the brightest central galaxy.

    Returns:
        str: A sentence stating the galaxy belongs to the cluster and orbits
            its brightest central galaxy.
    """
    return (f"It is a member of {cluster_name}, gravitationally bound into a massive cluster "
            f"and orbiting the cluster's brightest central galaxy, {bcg_name}.")


def bcg_sentence(cluster_name):
    """Build a sentence describing a brightest central galaxy (BCG).

    Args:
        cluster_name (str): Name of the cluster the galaxy anchors.

    Returns:
        str: A sentence identifying the galaxy as the cluster's BCG, with a
            note on how BCGs grow by mergers.
    """
    return (f"It is the Brightest Central Galaxy of {cluster_name}, the giant elliptical at the "
            f"cluster's heart. BCGs grow enormous over billions of years by merging with infalling "
            f"galaxies, making them among the oldest and most massive galaxies known.")


# Shared helper function
def make_wcs():
    """Build the Aitoff WCS used to project sky coordinates to chart pixels.

    Sets up a 2D Aitoff (RA---AIT/DEC--AIT) projection centered at RA=180deg,
    Dec=0deg, with a 1deg-per-pixel scale and the reference pixel at the origin.

    Returns:
        astropy.wcs.WCS: The configured WCS, shared by the figure builders.
    """
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [0, 0]
    wcs.wcs.cdelt = [1.0, 1.0]
    wcs.wcs.crval = [180, 0]          # center of projection
    wcs.wcs.ctype = ["RA---AIT", "DEC--AIT"]
    return wcs


class AstroObject: 
    def __init__(self, ra, dec, z, name=None, exposure_time=1.0):
        """Initialize an astronomical object at a sky position and redshift.

        Args:
            ra (float): Right ascension in degrees.
            dec (float): Declination in degrees.
            z (float): Redshift. Used to derive luminosity distance.
            name (str, optional): Object name. Defaults to None.
            exposure_time (float, optional): Exposure time used in later
                brightness/visibility calculations. Defaults to 1.0.

        Attributes:
            coord (SkyCoord): Sky position built from ra/dec.
            d (float): Luminosity distance in Mpc, from z via the cosmology.
            color (float): Placeholder, set later. Initialized to 0.
            mag (float): Placeholder magnitude, set later. Initialized to 0.
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
        """Return the distance modulus (m − M) for this object's redshift.

        Returns:
            float: Distance modulus in magnitudes, from z via the cosmology.
        """
        return cosmo.distmod(self.z).value
    
    def get_hue(self): 
        """Map this object's color index (g-r) to a blue-red RGB string.

        Normalizes the color index to [0, 1], then linearly interpolates between a
        blue and a red, so blue is bluer/younger and red is redder/older.

        Returns:
            str: A Plotly-style color, e.g. "rgb(120, 100, 200)".
        """
        c    = np.clip((self.color - 0.3) / 1.2, 0.0, 1.0) #"clips" color to 0, 1; wider range accounts for redshift shift
        blue = np.array([70, 130, 255])
        red  = np.array([255, 70, 50])

        r, g, b = (blue + c*(red-blue)).astype(int)
        return f"rgb({r}, {g}, {b})" #formatted this way for plotly
    
    def peak_brightness(self, faint=25.0, bright=15.0):
        """Map this object's magnitude to a display brightness, scaled by exposure.

        Computes a limiting magnitude from the exposure time, then linearly maps
        this object's magnitude into a brightness value (fainter = dimmer), clipped
        to a display range. Longer exposures push the limiting magnitude fainter, so
        dim objects brighten.

        Args:
            faint (float): Magnitude mapping to the low end of brightness (survey
                depth, e.g. LSST ~25). Defaults to 25.0.
            bright (float): Magnitude mapping to the high end (the "core"). Defaults
                to 15.0.

        Returns:
            float: Display brightness, clipped to [0.30, 1.5]. Not physical — tuned
                for rendering.
        """
        exposure_time = max(self.exposure_time, 1e-3)   # make slider min > 0

        floor = 0.30
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
    def __init__(self, ra, dec, z, name, exposure_time=1.0,
            size    = 7, 
            type    = "spiral", 
            q       = 1,
            mass    = 1e12, 
            lensed  = False, 
            sed     = 'None', 
            agn_lum = 0.0,
            notes   = None,
            ):
        super().__init__(ra, dec, z, name, exposure_time)
        self.q     = q       # axis ratio
        self.angle = 0       # eventually add random axis-tilt for display
        self.mass  = mass    # solar masses
        #self.lensed = lensed 
        self.exposure_time = exposure_time
        self.sed   = sed     # for stellar population type
        self.agn   = agn_lum # AGN activity
        self.type  = type    # Galaxy type
        self.size  = size    # Angular diameter in arcmin
        self.name   = name
        self.notes = notes if notes else self.describe()   # string that describes the object

        #setting colors
        self.color  = self.estimate_color()
        self.mag    = self.estimate_mag()
    
    def get_sed_template(self):
        return SED_TEMPLATES.get(self.sed, SED_TEMPLATES[self.type])
    
    def effective_type(self):
        return self.sed if self.sed in SED_TEMPLATES else self.type #this is from messy code I don't feel like fixing yet
    
    def describe(self):
        """
        Layman, educational descriptor built from this galaxy's own physical properties. 
        Returns a string to be concat'd onto name.
        """
        etype = self.effective_type()
        star_forming = etype in STARFORMING

        lookback = cosmo.lookback_time(self.z).to_value("Gyr")
        d_com = cosmo.comoving_distance(self.z).to_value("Mpc")
        wl = ("bluer, shorter-wavelength light from hot, young stars" if star_forming
              else "redder, longer-wavelength light from old, cool stars")

        base = (f"This is a {etype} galaxy of about {mass_phrase(self.mass)} solar masses, "
                f"glowing mostly in {wl}. It sits at redshift z = {self.z:.2f}, about "
                f"{distance_phrase(d_com)} away, so its light left it roughly "
                f"{lookback:.1f} billion years ago. At magnitude {self.mag:.1f} it would be "
                f"{visibility(self.mag)} to spot.")

        tidbits = [("It's actively forming new stars." if star_forming
                   else "It has mostly stopped forming stars ('red and dead').")]
        
        if self.agn > 0:
            tidbits.append("It hosts an active galactic nucleus: a supermassive black hole "
                           "blazing as it feeds on surrounding gas.")
            
        tidbits.append(redshift_note(self.z))

        pool = GAL_TRIVIA.get(etype, [])

        if pool:
            seed = int(round(self.z, 4) * 1e6 + self.mass) % (2**32)   # deterministic per object
            tidbits.append(np.random.default_rng(seed).choice(pool))

        return base + " " + " ".join(tidbits)

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


    def prepare_figure_data(self, display_scale=0.8):
        '''
        possible: incorporate ang diameter distance instead of div by 5
        '''
        sky_width_deg = self.size * display_scale  # scale actual object size to size on the plot

        wcs = make_wcs()

        # Find pixel position of galaxy center
        cx, cy = wcs.all_world2pix([[self.ra, self.dec]], 0)[0]

        # Use small offset toward projection center (RA=180) to avoid RA wrap at 0/360
        delta = -0.1 if self.ra > 180 else 0.1
        edge_x = wcs.all_world2pix([[self.ra + delta, self.dec]], 0)[0][0]
        pix_per_deg = abs(edge_x - cx) / abs(delta)
        pix_width = min(pix_per_deg * sky_width_deg, 15.0)  # cap so no object floods the frame

        n_pix = int(np.clip(pix_width * 20, 20, 200))
        xs = np.linspace(cx - pix_width, cx + pix_width, n_pix)
        ys = np.linspace(cy - pix_width, cy + pix_width, n_pix)
        X, Y = np.meshgrid(xs, ys)

        dx, dy = X - cx, Y - cy

        th = np.radians(self.angle)
        xr = dx * np.cos(th) + dy * np.sin(th)
        yr = -dx * np.sin(th) + dy * np.cos(th)

        size = pix_width / 2.0
        r2 = (xr / size) ** 2 + (yr / (size * self.q)) ** 2

        grid = self.peak_brightness() * np.exp(-0.5 * r2)
        hue = self.get_hue()
        # parse rgb values from hue string for faint anchor
        rgb = hue[4:-1].split(", ")
        faint_hue = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.08)"
        cs = [[0.0, "rgba(0,0,0,0)"], [0.15, faint_hue], [1.0, hue]]

        return xs, ys, grid, cs


    def visualize(self): 
        
        xs, ys, grid, cs = self.prepare_figure_data()
        fig = go.Figure(go.Heatmap(x=xs, y=ys, z=grid, zmin=0, zmax=1, colorscale=cs, showscale=False))

        return self.finish_visualize(fig, f"Galaxy with z={self.z} and {self.color:.2f}")

'''
Cluster class
'''    
class Cluster(AstroObject):
    def __init__(self, ra, dec, z, q, n, r, seed=None, exposure_time=1, bcg_scale=1.5):
        """Initialize a galaxy cluster and generate its member galaxies.

        Args:
            ra (float): Right ascension in degrees.
            dec (float): Declination in degrees.
            z (float): Redshift.
            q (float): Squash factor along the y-axis (cluster ellipticity).
            n (int): Number of member galaxies.
            r (float): Cluster radius.
            seed (int, optional): Seed for reproducible member generation.
                Defaults to None.
            exposure_time (float, optional): Exposure time forwarded to members.
                Defaults to 1.
            bcg_scale (float, optional): Size/brightness boost for the brightest
                central galaxy. Defaults to 1.5.

        Attributes:
            bcg_name (str): Name of the brightest central galaxy.
            members (list): Member galaxies, built by generate_members().
        """
        name = cluster_designation(ra, dec)
        super().__init__(ra, dec, z, name=name, exposure_time=exposure_time)
        self.q = q # squash factor of cluster from y-axis
        self.ra = ra #Right Ascention, equatorial positon in sky
        self.dec = dec #Declination, angular distance from the equator
        self.z = z #Redshift
        self.n = n #Number of galaxies in cluster
        self.r = r #Radius of the cluster
        self.cluster_size = 0
        self.bcg_scale = bcg_scale
        self.bcg_name = f"{self.name} BCG"
        self.seed = seed
        self.members = self.generate_members() # initializes the cluster with its members

    def generate_members(self):
        """Generate the cluster's member galaxies, including a central BCG.

        Draws ``n`` members from the cluster's seeded RNG: positions are scattered
        around the cluster center with a Gaussian spread (squashed by ``q`` in Dec),
        masses are drawn log-uniformly, redshifts are jittered around the cluster z,
        and types are sampled (mostly elliptical). A brightest central galaxy is
        built at the cluster center and inserted at index 0.

        Returns:
            np.ndarray: Array of Galaxy objects, with the BCG first followed by
                ``n - 1`` satellites.
        """
        if self.seed:
            rng = np.random.default_rng(self.seed)
        else: 
            rng = np.random.default_rng(seed=42)

        #Galaxy RAs and Decs
        r_Mpc = self.r # radius of cluster in Mpc
        dA_Mpc = cosmo.angular_diameter_distance(self.z).value # distance from observer to cluster in Mpc
        cluster_size = np.degrees(r_Mpc/dA_Mpc) * 50 # gets angular size of cluster in degrees (from rads) and scales up
        self.cluster_size = cluster_size #saving this for later

        dx = rng.normal(0, cluster_size, self.n) # returns array of random positions along x axis (RA)
        dy = self.q * rng.normal(0, cluster_size, self.n) # returns array of random positions along y axis (dec), with a boundary defined by q
        cluster_ras  = (self.ra + dx) % 360.0                 # RA wraps around the sky
        cluster_decs = np.clip(self.dec + dy, -90.0, 90.0)    # Dec capped at the poles
        # orient_angle = rng.uniform(0, np.pi)
        
        #Galaxy masses
        cluster_ms = np.power(10, rng.uniform(9, 11, self.n)) # generates array of standard masses for cluster galaxies

        #Galaxy redshifts
        cluster_zs = rng.normal(0, 0.005, self.n) + self.z # generates array of cluster galaxy redshift

        #cluster_members = np.zeros(self.n)

        #Galaxy Types
        gal_types = np.array(["elliptical", "spiral", "irregular"])
        cl_gal_types = rng.choice(gal_types, self.n, p=np.array([0.7,0.2,0.1]))

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

        '''
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
        '''

        member_size = 1.0  # fixed size independent of cluster spread

        # BCG
        bcg = Galaxy(self.ra, self.dec, self.z, name=self.bcg_name,
                    size=member_size * self.bcg_scale, type="elliptical", sed="elliptical",
                    mass=5e12, exposure_time=self.exposure_time)
        bcg.name += " " + bcg_sentence(self.name)

        cluster_members = np.array([], dtype=Galaxy)
        for i in range(self.n - 1):
            gal = Galaxy(cluster_ras[i], cluster_decs[i], cluster_zs[i],
                        name=f"{cl_gal_types[i].capitalize()} gallaxy",
                        size=member_size, mass=cluster_ms[i], sed=cl_gal_types[i],
                        exposure_time=self.exposure_time)
            gal.notes += " " + sat_sentence(self.name, self.bcg_name)
            cluster_members = np.append(cluster_members, gal)

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



       



        