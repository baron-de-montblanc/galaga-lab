def galaxy_field(population_size):
    """
    Randomly generates a chosen number of points (population size) of uniform 
    distribution over a polar graph.
    """
    r = 1 * np.sqrt(np.random.rand(population_size))
    theta = 2 * np.pi * np.random.rand(population_size)
    plt.polar(theta,r,'ro')