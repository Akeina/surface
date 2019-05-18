"""
Data Manager
************

Description
===========

Data Manager is used to maintain different states of data across the system.

Functionality
=============

DataManager
-----------

The :class:`DataManager` class features disc caching functionality to provide accessibility and modifiability across
different modules and processes, as well as additionally safeguards the networked values against too high current.

The :func:`get_data`, :func:`set_data` and :func:`clear` globally accessible functions provide ways of interacting with
the manager.

.. warning::

    You should never create an instance of :class:`DataManager` yourself, and instead use the 3 functions mentioned.

Execution
---------

You should simply import the module::

    import communication.data_manager as dm

.. note::

    Remember to always `clear` the manager at the start of your program.

Functions & classes
-------------------

.. note::

    Remember that the code is further described by in-line comments and docstrings.

The following list shortly summarises the functionality of each code component within the :class:`DataManager` class:

    1. :func:`__init__` builds the manager
    2. :func:`get` accesses the data
    3. :func:`set` modifies the data
    4. :func:`clear` clears the disc cache
    5. :func:`_init_safeguards` initialises the safeguard-related fields
    6. :func:`_safeguard_transmission_data` safeguards the data before networking it

Additionally, the :func:`_init_manager` function is used to initialise and enclose the manager on import statement,
as well as provide the functions to interact with it indirectly.

Modifications
=============

It is recommended that you adjust the `CACHE_PATH` constant to store your cache in the proper place.

.. warning::

    You should be using a SSD drive for cache storage to avoid the delay.

Additionally, you should modify the :func:`__init__` function, especially the `self._transmission_keys` mapping.

Authorship
==========

Kacper Florianski
"""

from diskcache import FanoutCache
from math import sqrt
from os import path

# Build the cache PATH
CACHE_PATH = path.join("C:", "Coding", "Python", "ROV", "cache")


class DataManager:

    def __init__(self):
        """
        Constructor function used to initialise the data manager.

        Adjust the `shards` amount in the cache constructor to increase or decrease the amount of parallelism in
        data-related computations, as well as modify the `self._transmission_keys` set to specify which data should be
        networked to the middle-level software.
        """

        # Initialise the data cache
        self._data = FanoutCache(CACHE_PATH, shards=8)

        # Create a set of keys matching data which should be sent over the network
        self._transmission_keys = {
            "Thr_FP", "Thr_FS", "Thr_AP", "Thr_AS", "Thr_TFP", "Thr_TFS", "Thr_TAP", "Thr_TAS", "Mot_R", "Mot_G",
            "Mot_F"
        }

        # Initialise safeguard-related fields
        self._init_safeguards()

    def get(self, *args, transmit=False) -> dict:
        """
        Function used to access the cached values. Guards against over-current on networked data.

        Example of usage::

            partial_data = get("Mot_G")  # returns a dictionary with a single entry
            full_data = get()  # returns a dictionary with several entries
            transmission_full = get(transmit=True)  # returns a dictionary with values which are networked

        :param args: Keys to retrieve (returns all keys if no args are passed)
        :param transmit: Boolean to specify if only the transmission data should be retrieved
        :return: Dictionary of the data
        """

        # If the data retrieved is meant to be sent over the network
        if transmit:

            # Return selected data or transmission-specific dictionary if no args passed
            return self._safeguard_transmission_data(*args)

        # Return selected data or whole dictionary if no args passed
        return {key: self._data[key] for key in args if key in self._data} if args \
            else {key: self._data[key] for key in self._data}

    def set(self, **kwargs):
        """
        Function used to modify the cache.

        Example of usage::

            set(Mot_G=1500)  # Does self._data["Mot_G"] = 1500

        :param kwargs: Key, value pairs of data to modify.
        """

        # Update the data with the given keyword arguments
        for key, value in kwargs.items():
            self._data[key] = value

    def clear(self):
        """
        Function used to clear the cache.
        """

        self._data.clear()

    def _init_safeguards(self):
        """
        Function used to initialise all fields related to the safeguarding operations.

        You should modify::

            1. 'self._SAFEGUARD_KEYS' set to specify which values should be safeguarded.
            2. 'self._AMP_LIMIT' constant to specify the amp limit (pick a slightly smaller value than required).
            3. 'self._IDLE_VALUES' set to specify which values should be ignored (default values).
        """

        # Initialise the keys to safeguard
        self._SAFEGUARD_KEYS = {
            "Thr_FP", "Thr_FS", "Thr_AP", "Thr_AS", "Thr_TFP", "Thr_TFS", "Thr_TAP", "Thr_TAS",
            "Mot_F", "Mot_G", "Mot_R"
        }

        # Initialise the current limit
        self._AMP_LIMIT = 99

        # Initialise the values to ignore
        self._IDLE_VALUES = {1500}

        # Initialise the quadratic function's hyper parameters
        a = 0.00009537964
        b = -0.2864872
        c = 214.9513

        # Initialise the amp calculation approximation function
        self._amp = lambda x: a * (x ** 2) + b * x + c

        # Initialise the scaling function (where v is the expected, scaled amp)
        self._safeguard_scale = lambda v: ((-b + sqrt(b**2 - 4*a*(c - v))) / (2*a),
                                           (-b - sqrt(b**2 - 4*a*(c - v))) / (2*a))

    def _safeguard_transmission_data(self, *args):
        """
        Function used to safeguard the values that are to be transmitted to Raspberry Pi and further.

        :param args: Args from the `get` function
        """

        # Fetch selected data or transmission-specific dictionary if no args passed
        data = {key: self._data[key] for key in args if key in self._transmission_keys and key in self._data} if args \
            else {key: self._data[key] for key in self._transmission_keys if key in self._data}

        # Select the safeguard data to scale it
        safeguard_data = {key: data[key] for key in self._SAFEGUARD_KEYS if key in data}

        # Calculate how much current would be taken by each value
        amps = {key: self._amp(value) for key, value in safeguard_data.items()}

        # Calculate the total current
        current = sum(amps.values())

        # Safeguard the values if the limit was passed
        if current > self._AMP_LIMIT:

            # Find the ratio
            ratio = self._AMP_LIMIT / current

            # Iterate over the data to scale the values
            for key in safeguard_data:

                # Find the vales by solving the quadratic equation
                values = self._safeguard_scale(amps[key]*ratio)

                # Check if the value should be considered
                if safeguard_data[key] not in self._IDLE_VALUES:

                    # Override current value with the closer one
                    if abs(safeguard_data[key] - values[0]) <= abs(safeguard_data[key] - values[1]):
                        safeguard_data[key] = values[0]
                    else:
                        safeguard_data[key] = values[1]

        # Return modified data
        return safeguard_data


# Create a closure for the data manager
def _init_manager():
    """
    Function used to create a closure for the data manager.

    :return: Enclosed functions
    """

    # Create a free variable for the :class:`DataManager`
    d = DataManager()

    # Inner function to return the current state of the data
    def get_data(*args, transmit=False):
        """
        Encloses :func:`DataManager.get`.

        :param args: Keys passed to get
        :param transmit: Boolean passed to get
        :return: Result of the :func:`get` function
        """

        return d.get(*args, transmit=transmit)

    # Inner function to alter the data
    def set_data(**kwargs):
        """
        Encloses :func:`DataManager.set`.

        :param kwargs: Key, value pairs passed to set
        """

        d.set(**kwargs)

    # Inner function to clear the cache
    def clear():
        """
        Encloses :func:`DataManager.clear`.
        """

        d.clear()

    # Return the enclosed functions
    return get_data, set_data, clear


# Create globally accessible functions to manage the data
get_data, set_data, clear = _init_manager()
