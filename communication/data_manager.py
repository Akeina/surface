"""

Data Manager is used to maintain different states of data across the system.

** Functionality **

By importing the module you gain access to three global functions - 'get_data', 'set_data' and 'clear'.

You should use the 'get_data' function to gain access to the available resources. You may specify additional arguments,
which should be dictionary keys, to retrieve a part of the data. If no arguments are specified, the entire dictionary
is returned. The arguments passed should be strings (because the keys are stored as strings).

Set the additional 'transmit' keyword argument when retrieving the data, if the dictionary returned should only contain
the fields to be sent over the network. Dictionary keys of values to be sent over the network must be included in the
'_transmission_keys' set within the class, and agreed with the lower-level team beforehand. Set the argument to True to
retrieve such data. The base functionality otherwise stays the same as with the argument being (by default) False.

You should use the 'set_data' function to change the resources. For each keyword argument passed, the state of the data
dictionary under the given key will be changed to the given value.

You should use the 'clear' function to clear the cache (for example at start of the program) to save some memory.

** Constants and other values **

As mentioned before, you should modify the '_transmission_keys' set to include all the values that should be networked
with the Pi.

** Example **

Let axis_x = 10, axis_y = 20, axis_z = -15. To save these values into the data manager, call:

    set_data(axis_x=10, axis_y=20, axis_z=-15)

To retrieve the information about axis x and y, call:

    data = get_data('axis_x', 'axis_y')

The result of printing data is as follows:

    {'axis_x': 10, 'axis_y': 20}

** Author **

Kacper Florianski

"""

# TODO: Possibly replace with Cache (test with full software)
from diskcache import FanoutCache
from math import sqrt


class DataManager:

    def __init__(self):
        """

        Function used to initialise the data manager.

        ** Modifications **

            1. Modify the '_transmission_keys' set to specify which values should be transmitted to Pi.

        """

        # Initialise the data cache
        self._data = FanoutCache("cache", shards=8)

        # Create a set of keys matching data which should be sent over the network
        self._transmission_keys = {
            "Thr_FP", "Thr_FS", "Thr_AP", "Thr_AS", "Thr_TFP", "Thr_TFS", "Thr_TAP", "Thr_TAS", "Mot_R", "Mot_G",
            "Mot_F", "LED_M"
        }

        # Initialise safeguard-related fields
        self._init_safeguards()

    def get(self, *args, transmit=False) -> dict:
        """

        Function used to access the cache.

        Returns full dictionary if no args passed, or partial data if either args are passed or transmit is set to True.

        :param args: Keys to retrieve
        :param transmit: Boolean to specify if the transmission-only data should be retrieved
        :return: Data stored in the data manager

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

        ** Modifications **

            1. Modify the '_SAFEGUARD_KEYS' set to specify which values should be safeguarded.

            2. Modify the '_AMP_LIMIT' constant to specify the amp limit (I recommend picking a slightly smaller value).

            3. Modify the '_IDLE_VALUES' set to specify which values should be ignored (default values).

        """

        # Initialise the keys to safeguard
        self._SAFEGUARD_KEYS = {
            "Thr_FP", "Thr_FS", "Thr_AP", "Thr_AS", "Thr_TFP", "Thr_TFS", "Thr_TAP", "Thr_TAS", "Mot_F", "Mot_G",
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

        :param args: Args from the 'get' function

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

    # Create a free variable for the Data Manager
    d = DataManager()

    # Inner function to return the current state of the data
    def get_data(*args, transmit=False):
        return d.get(*args, transmit=transmit)

    # Inner function to alter the data
    def set_data(**kwargs):
        return d.set(**kwargs)

    # Inner function to clear the cache
    def clear():
        d.clear()

    return get_data, set_data, clear


# Create globally accessible functions to manage the data
get_data, set_data, clear = _init_manager()
