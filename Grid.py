import numpy as np
import math


#############################################################################
#                 Creation of Space and Velocity Grids/Arrays               #
#############################################################################
class Grid:
    """A simple class for Positional-, Time- or Velocity-Grids.

    Attributes:
        dim (int):
            Grid dimensionality
        boundaries (:obj:'np.ndarray'):
            Describes (physical) size and position of the grid.
            Array of shape=(3,) and dtype=float
        d (float):
            Step size of the grid.
        n (int):
            Denotes the total number of grid points.
        shape (str):
            Shape of Grid can only be rectangular so far
        ftype (type or np.dtype):
            Determines data type of floats.
    """
    # Todo Add unit tests
    # Todo Add "check for consistency" method
    # Todo Add Circular shape
    # Todo Add adaptive Grids
    GRID_SHAPES = ['rectangular']
    DATA_TYPES = [np.float16, np.float32, np.float64]

    def __init__(self, data_type=float):
        self.dim = 0
        self.boundaries = np.zeros((3, 2), dtype=data_type)
        self.d = 0.0
        self.n = 0
        self.shape = 'NOT INITIALIZED'
        self.fType = data_type

    def __compute_n(self):
        assert self.d is not 0.0
        assert not np.array_equal(self.boundaries,
                                  np.zeros((3, 2), dtype=self.fType))
        if self.shape is 'rectangular':
            # Calculate number of grid points per dimension and total number
            _l = self.boundaries[:, 1] - self.boundaries[:, 0]
            # _n_dim = np.array(floor(_l / self.d) + 1, dtype=self.fType)
            # for i_d in range(dim):
            #     if _l[i_d] - (_n_dim[i_d] - 1) * self.d < 1E-7:
            # # Todo Solve rounding issue 0.4-0.3 = 0.100000002
            # Adjust boundaries if small error to multiples of d
            _n_dim = np.array(np.ceil(_l / self.d) + 1, dtype=int)
            # TODO readjust self.d, if necessary? How?
            return int(_n_dim.prod())
        else:
            print("ERROR - Unspecified Grid Shape")
            assert False

    def check_integrity(self):
        assert type(self.dim) is int
        assert self.dim in [1, 2, 3]
        assert type(self.boundaries) is np.ndarray
        assert self.boundaries.dtype == self.fType
        assert self.boundaries.shape == (3, 2)
        # Todo assert boundaries have positive width, or are both 0,
        # Todo depending on dim
        assert type(self.d) is self.fType
        assert self.d > 0
        assert type(self.n) is int
        assert self.n >= 2
        assert self.shape in Grid.GRID_SHAPES
        #  Todo assert that boundaries, d and n match (dep. on shape)
        assert self.n is self.__compute_n()
        assert type(self.fType) in [type, np.dtype]
        # Todo make tis assertion work
        # assert type(self.fType) in Grid.DATA_TYPES

    def __initialize_without_n(self, dim, boundaries, d, shape):
        self.dim = dim
        self.boundaries[0:dim, :] = np.array(boundaries, dtype=self.fType)
        self.d = self.fType(d)
        self.shape = shape
        self.n = self.__compute_n()

    def initialize(self,
                   dim,
                   boundaries,
                   d,
                   n,
                   shape):
        # Case Switches, 3 possible cases
        sw_b = boundaries is not None
        sw_d = d is not None
        sw_n = n is not None
        # Total number not defined
        if sw_b and sw_d and not sw_n:
            self.__initialize_without_n(dim,
                                        boundaries,
                                        d,
                                        shape)
        else:
            print('Exactly 2 of [Boundaries, Step Size, Total Number]'
                  'must be submitted')
            assert False

    def __make_rectangular_grid(self):
        assert self.shape == 'rectangular'
        # Todo Remove redundance (__compute_n)
        # Calculate number of grid points per dimension and total number
        _length = self.boundaries[:, 1] - self.boundaries[:, 0]
        _n_dim = np.array(np.ceil(_length / self.d) + 1,
                          dtype=int)
        _grid_dimension = (self.n, self.dim)
        # Todo Till here
        # Create list of 1D grids for each dimension
        _list_of_1D_grids = [np.linspace(self.boundaries[i_d, 0],
                                         self.boundaries[i_d, 1],
                                         _n_dim[i_d])
                             for i_d in range(self.dim)]
        # Create mesh grid from 1D grids
        _mesh_list = np.meshgrid(*_list_of_1D_grids)    # *[a,b,c] = a,b,c
        grid = np.array(_mesh_list)
        # bring meshgrid into desired order/structure
        if self.dim is 2:
            grid = np.array(grid.transpose((2, 1, 0)))
        elif self.dim is 3:
            grid = np.array(grid.transpose((2, 1, 3, 0)))
        elif self.dim is not 1:
            print("Error")
        grid = grid.reshape(_grid_dimension)
        self.isConstructed = True
        return grid

    def make_grid(self):
        if self.shape is 'rectangular':
            return self.__make_rectangular_grid()
        else:
            print("ERROR - Unspecified Grid Shape")
            assert False

    def print(self):
        print("Dimension = {}".format(self.dim))
        print("Boundaries = \n{}".format(self.boundaries))
        print("Number of Grid Points = {}".format(self.n))
        print("Step Size = {}".format(self.d))
        print("Shape = {}".format(self.shape))
        print("Data Type = {}".format(self.fType))
        print("")

# t = Grid()
# # Todo right Number?
# t.initialize_without_n(3,
#                        [[0.0, 2.0], [0.3, 0.4], [0.0, 1.0]],
#                        0.1,
#                        'rectangular')
# t.initialize_without_n(1, [[0.3, 0.4]], 0.1, 'rectangular')
# t.check_integrity()
# # t.initialize_without_n(2, [[0, 1], [0, 1]], 0.1, 'rectangular')
#
# t.print()