"""

Data Manager is used to maintain different states of data across the system.

** Usage **

By importing the module you gain access to two global functions - 'get_data' and 'set_data'.

You should use the 'get_data' function to gain access to the available resources. You may specify additional arguments,
which should be dictionary keys, to retrieve a part of the data. If no arguments are specified, the entire dictionary is
returned. The arguments passed should be strings (because the keys are stored as strings).

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


class DataManager:

    def __init__(self):

        # Declare data dictionary
        self._data = dict()

    def get(self, *args):

        # Return selected data or whole dictionary if no args passed
        return {key: self._data[key] for key in args} if args else self._data

    def set(self, **kwargs):

        # Update the data with the given keyword arguments
        for key, value in kwargs.items():
            self._data[key] = value


# Create a closure for the data manager
def _init_manager():

    # Create a free variable for the Data Manager
    d = DataManager()

    # Inner function to return the current state of the data
    def get_data(*args):
        return d.get(*args)

    # Inner function to alter the data
    def set_data(**kwargs):
        return d.set(**kwargs)

    return get_data, set_data


# Create globally accessible functions to manage the data
get_data, set_data = _init_manager()
