"""

Data Manager is used to maintain different states of data across the system.

** Usage **

By importing the module you gain access to two global functions - 'get_data' and 'set_data'.

You should use the 'get_data' function to gain access to the available resources. You may specify additional arguments,
which should be dictionary keys, to retrieve a part of the data. If no arguments are specified, the entire dictionary is
returned. The arguments passed should be strings (because the keys are stored as strings).

Set the additional 'transmit' keyword argument when retrieving the data, if the dictionary returned should only contain
the fields that should be sent over the network. Each item to be sent over the network must be specified in the
'_transmission_keys' set within the class, and agreed with the lower-level team beforehand. Set the argument to True to
retrieve such data. The base functionality otherwise stays the same as with the argument being (by default) False.

You should use the 'set_data' function to change the resources. For each keyword argument passed, the state of the
data dictionary under the given key will be changed to the given value.

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


class DataManager:

    def __init__(self):

        # Initialise the data cache
        self._data = FanoutCache("cache", shards=4)

        # Create a set of keys matching data which should be sent over the network
        self._transmission_keys = {
            "Thr_FP", "Thr_FS", "Thr_AP", "Thr_AS", "Thr_TFP", "Thr_TFS", "Thr_TAP", "Thr_TAS",
            'LED_M', "Mot_R", "Mot_G",
        }

    def get(self, *args, transmit=False):

        # If the data retrieved is meant to be sent over the network
        if transmit:

            # Return selected data or transmission-specific dictionary if no args passed
            return {key: self._data[key] for key in args if key in self._transmission_keys} if args else \
                   {key: self._data[key] for key in self._transmission_keys if key in self._data}

        # Return selected data or whole dictionary if no args passed
        return {key: self._data[key] for key in args} if args else {key: self._data[key] for key in self._data}

    def set(self, **kwargs):

        # Update the data with the given keyword arguments
        for key, value in kwargs.items():
            self._data[key] = value

    def clear(self):
        self._data.clear()


# Create a closure for the data manager
def _init_manager():

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
