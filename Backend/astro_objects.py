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
