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

    # Create a free variable for the Data Manager TODO: Make it a singleton
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

# TODO: Remove this - temp test data
set_data(test_0=0, test_1=1, test_2=2)
