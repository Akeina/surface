# TODO: Make this a singleton
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


# Create a globally accessible data manager
data = DataManager()

# TODO: Remove this - temp test data
data.set(test_0=0, test_1=1, test_2=2)
