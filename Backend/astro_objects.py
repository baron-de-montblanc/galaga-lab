'''
File for classes and making the astro objects class and any subclasses/objects for galaxies, etc

class AstroObject: Fed in RA/Dec from "random field" footprint so it makes sense
- Main object: RA, Dec, redshift, distance
- def visualize_object? For notebook testing

subclass Galaxy: 
- type/shape, lensed or not lensed, galaxy_mass
- Special factors (AGN, star-forming, relaxed, dwarf, etc.)
        Note: If this is implemented, it can be limited by redshift so needs to be accounted for in estimate_gal_color
- def estimate_color (since star forming galaxies may be different)
- def estimate_mag

subclass Star: 
- Stage of star formation, star_mass
- def estimate_color
- def estimate_mag

subclass Cluster: 
- radius, shape, mass
- def generate_members
'''

class AstroObject: 
    def __init__(self, ra, dec, z, d):
        self.ra = ra
        self.dec = dec 
        self.z = z
        self.d = d
        self.color = 0
        self.mag = 0
    
    def visualize(self): 
        ## quick plotly visualization
        ## visualize the object (not on the field) as an ellipse as a simple figure with color and "faintness" with magnitude
        ## should magnitude change the "shape" at all? Would edges be fainter/not seen like a gradient? 
        ## probably a gradient with a bright center at the given ra/dec
        pass

class Galaxy(AstroObject): 
    def __init__(self, ra, dec, z, d, q=1, mass=1e12, lensed=False, type='None'):
        super().__init__(ra, dec, z, d)
        self.q = 1 #axis ratio
        self.angle = 0 #eventually add random axis-tilt for display
        self.mass = mass #solar masses, to use astropy units? Not necessary?
        #self.lensed = lensed 
        self.type = type #'star-forming', 'AGN', 'dwarf', others?
    
    def estimate_color(self):
        #estimate galaxy color based on mass, type, z, d, and m
        return None
    
    def estimate_mag(self): 
        #estimate magnitude based on mass, type, z, d, and m
        #will this need to be before estimate_color, after estimate_color, entirely dependent?
        return None