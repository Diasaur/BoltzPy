
import numpy as np
import h5py

import boltzpy as bp
import boltzpy.constants as bp_c


class Geometry(bp.BaseClass):
    r"""Describes the spatial geometry of the Simulation.


    Parameters
    ----------
    shape : :obj:`array_like` [:obj:`int`]
        Shape of the space grid.
    rules : :obj:`array_like` [:obj:`Rule`], optional
        List of Initialization :obj:`Rules<Rule>`

    Attributes
    ----------
    shape : :obj:`~numpy.array` [:obj:`int`]
        Shape of the space grid.
    rules : :obj:`~numpy.array` [:obj:`Rule`], optional
        List of Initialization :obj:`Rules<Rule>`

    """
    def __init__(self, shape=None, rules=None):
        if type(shape) in [list, tuple]:
            shape = np.array(shape)
        if isinstance(rules, list):
            rules = np.array(rules, dtype=bp.Rule)
        self.check_parameters(shape=shape,
                              rules=rules)
        self.shape = shape
        if rules is None:
            rules = np.empty((0,), dtype=bp.Rule)
        self.rules = rules
        return

    #: :obj:`dict` : Default ascii char, for terminal print
    DEFAULT_ASCII = {"Inner Point": 'o',
                     'Boundary Point': '#',
                     'Constant_IO_Point': '>',
                     'Time_Variant_IO_Point': '~',
                     None: '?'
                     }

    @property
    def ndim(self):
        if self.shape is None:
            return None
        return self.shape.size

    @property
    def size(self):
        if self.shape is not None:
            return np.prod(self.shape)
        else:
            return None

    @property
    def affected_points(self):
        result = list()
        for rule in self.rules:
            result += list(rule.affected_points)
        assert len(result) == len(set(result))
        return result

    @property
    def unaffected_points(self):
        possible_points = set(range(int(self.size)))
        affected_points = set(self.affected_points)
        return possible_points - affected_points

    @property
    def size_of_model(self):
        sizes = [rule.initial_state.size for rule in self.rules]
        # todo assert all rule.initial_state.size must be equal in check_params
        assert len(set(sizes)) == 1
        return sizes[0]

    def add_rule(self, new_rule):
        """Add a :class:`Rule` to :attr:`rules` array.

        Parameters
        ----------
        new_rule : :obj:`~boltzpy.Rule`
            The Rule object to append
        """
        assert isinstance(new_rule, bp.Rule)
        assert set(new_rule.affected_points).issubset(self.unaffected_points)
        self.rules = np.append(self.rules, [new_rule])
        self.check_integrity(complete_check=False)
        return

    @property
    def is_set_up(self):
        if any(attr is None for attr in self.__dict__.values()):
            return False
        elif len(self.unaffected_points) != 0:
            return False
        else:
            self.check_integrity()
            return True

    # Todo Only Temporary!
    @property
    def init_array(self):
        init_arr = np.full(self.shape, -1, dtype=int)
        for (idx_r, r) in enumerate(self.rules):
            for idx_p in r.affected_points:
                init_arr[idx_p] = idx_r
        return init_arr

    @property
    def initial_state(self):
        """Fully initiallized initial state.

        Returns
        -------
        state : :class:`~numpy.array` [:obj:`float`]
            The initialized PSV-Grid.
            Array of shape
            (:attr:`Simulation.p.size
            <boltzpy.Grid.size>`,
            :attr:`Simulation.sv.size
            <boltzpy.SVGrid.size>`).
        """
        if not self.is_set_up:
            return None
        shape = (self.size, self.size_of_model)
        state = np.zeros(shape=shape, dtype=float)
        for rule in self.rules:
            for p in rule.affected_points:
                state[p, :] = rule.initial_state
        # Todo state = state.reshape(shape + (model_size,))
        return state

    #####################################
    #            Computation            #
    #####################################
    def collision(self, data):
        for rule in self.rules:
            rule.collision(data)
        return

    def transport(self, data):
        for rule in self.rules:
            rule.transport(data)
        # update data.state (transport writes into data.result)
        data.state[...] = data.result[...]
        return

    #####################################
    #           Serialization           #
    #####################################
    @staticmethod
    def load(hdf5_group):
        """Set up and return a :class:`Geometry` instance
        based on the parameters in the given HDF5 group.

        Parameters
        ----------
        hdf5_group : :obj:`h5py.Group <h5py:Group>`

        Returns
        -------
        self : :class:`Geometry`
        """
        assert isinstance(hdf5_group, h5py.Group)
        assert hdf5_group.attrs["class"] == "Geometry"

        # read parameters from file
        params = dict()
        for (key, value) in hdf5_group.items():
            # load rules iteratively
            if key == "rules":
                assert hdf5_group[key].attrs["class"] == "Array"
                size = hdf5_group[key].attrs["size"]
                value = np.empty(size, dtype=object)
                for (key_rule, group_rule) in hdf5_group[key].items():
                    # key_rule is a string in ["0", "1", "2",...]
                    # it denotes is (former) position in the array
                    idx_rule = int(key_rule)
                    value[idx_rule] = bp.Rule.load(group_rule)
                params[key] = value
            # load everything else directly
            else:
                params[key] = value[()]

        # construct Geometry
        self = Geometry(**params)
        self.check_integrity(complete_check=False)
        return self

    def save(self, hdf5_group):
        """Write the main parameters of the :obj:`Geometry` instance
        into the HDF5 group.

        Parameters
        ----------
        hdf5_group : :obj:`h5py.Group <h5py:Group>`
        """
        assert isinstance(hdf5_group, h5py.Group)
        self.check_integrity(complete_check=False)

        # Clean State of Current group
        for key in hdf5_group.keys():
            del hdf5_group[key]
        hdf5_group.attrs["class"] = "Geometry"

        # write attributes to file
        for (key, value) in self.__dict__.items():
            if key == "rules":
                # value is an array of rule objects
                assert isinstance(value, np.ndarray)
                assert value.dtype == bp.Rule
                # create group: "rules"
                hdf5_group.create_group(key)
                hdf5_group[key].attrs["class"] = "Array"
                hdf5_group[key].attrs["size"] = value.size
                # save all rules iteratively
                for (idx_rule, rule) in enumerate(value):
                    assert isinstance(rule, bp.Rule)
                    key_rule = str(idx_rule)
                    hdf5_group[key].create_group(key_rule)
                    rule.save(hdf5_group[key][key_rule])
            # save all other attributes directly
            else:
                hdf5_group[key] = value
        return

    #####################################
    #           Verification            #
    #####################################
    def check_integrity(self,
                        complete_check=True,
                        context=None):
        """Sanity Check.

        Assert all conditions in :meth:`check_parameters`.

        Parameters
        ----------
        complete_check : :obj:`bool`, optional
            If True, then all attributes must be assigned (not None).
            If False, then unassigned attributes are ignored.
        context : :class:`Simulation`, optional
            The Simulation, which this instance belongs to.
            This allows additional checks.
        """
        self.check_parameters(ndim=self.ndim,
                              shape=self.shape,
                              rules=self.rules,
                              complete_check=complete_check,
                              context=context)
        return

    @staticmethod
    def check_parameters(ndim=None,
                         shape=None,
                         rules=None,
                         complete_check=False,
                         context=None):
        """Sanity Check.

        Checks integrity of given parameters and their interactions.

        Parameters
        ----------
        ndim : :obj:`int`, optional
        shape : :obj:`tuple` [:obj:`int`], optional
        rules : :obj:`~numpy.array` [:obj:`Rule`], optional
        complete_check : :obj:`bool`, optional
            If True, then all parameters must be set (not None).
            If False, then unassigned parameters are ignored.
        context : :class:`Simulation`, optional
            The Simulation, which this instance belongs to.
            This allows additional checks.
        """
        assert isinstance(complete_check, bool)
        # For complete check, assert that all parameters are assigned
        if complete_check is True:
            assert all(param_val is not None
                       for (param_key, param_val) in locals().items()
                       if param_key != "context")
        if context is not None:
            assert isinstance(context, bp.Simulation)

        # check all parameters, if set
        if ndim is not None:
            assert isinstance(ndim, int)
            assert ndim in bp_c.SUPP_GRID_DIMENSIONS

        if shape is not None:
            assert isinstance(shape, np.ndarray)
            assert shape.dtype == int
            assert np.all(shape >= 1)
            if context is not None and context.p.shape is not None:
                assert shape == context.p.shape

        if rules is not None:
            assert isinstance(rules, np.ndarray)
            assert rules.dtype == bp.Rule
            assert rules.ndim == 1
            for rule in rules:
                assert isinstance(rule, bp.Rule)
                rule.check_integrity(complete_check=complete_check,
                                     context=context)
            # all points must be affected at most once
            affected_points = list()
            for rule in rules:
                affected_points += list(rule.affected_points)
            assert len(affected_points) == len(set(affected_points)), (
                "Some points are affected by more than one rule:"
                "{}".format(affected_points)
            )
            if context is not None and context.p.size is not None:
                assert len(affected_points) <= context.p.size
            # all points must be affected at least once
            if complete_check:
                assert len(affected_points) == np.prod(shape)
            # All rules must work on the same model
            sizes_of_model = list(rule.initial_state.size
                                  for rule in rules)
            assert len(set(sizes_of_model)) in [0, 1], (
                "Not all rules have equal model size: "
                "{}".format(sizes_of_model)
            )

        # check correct attribute relations
        if ndim is not None and shape is not None:
            assert len(shape) == ndim

        return

    def __str__(self):
        """:obj:`str` :
        A human readable string which describes all attributes of the instance."""
        description = ''
        for (key, value) in self.__dict__.items():
            if key == "rules":
                for (rule_idx, rule) in enumerate(self.rules):
                    description += "rules[{}]:\n".format(rule_idx)
                    rule_str = rule.__str__().replace('\n', '\n\t')
                    description += '\t' + rule_str
                    description += '\n'
                continue
            description += '{key}:\n\t{value}\n'.format(
                key=key,
                value=value.__str__().replace('\n', '\n\t'))
        return description
