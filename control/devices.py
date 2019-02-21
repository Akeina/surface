import control.tools as tl


# TODO: Finish the joystick class after testing with joystick control library
class Joystick:

    def __init__(self):

        # Declare the hardware values
        self._AXIS_MAX = 32767
        self._AXIS_MIN = -32768

        # Declare the goal values
        self._axis_max = 1000
        self._axis_min = -1000

        # Calculate and store the middle value for the axis
        self._axis_mid = (self._axis_max + self._axis_min) // 2

        # Initialise the axis information
        self._axis_x = self._axis_mid
        self._axis_y = self._axis_mid
        self._axis_z = self._axis_mid

    @property
    def axis_x(self):
        return self._axis_x

    @axis_x.setter
    def axis_x(self, value):
        self._axis_x = tl.normalise(value, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @property
    def axis_y(self):
        return self._axis_y

    @axis_y.setter
    def axis_y(self, value):
        self._axis_y = tl.normalise(value, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @property
    def axis_z(self):
        return self._axis_z

    @axis_z.setter
    def axis_z(self, value):
        self._axis_z = tl.normalise(value, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)


# TODO: Finish the controller class after testing with joystick control library
class Controller:

    def __init__(self):

        # Declare the hardware values
        self._AXIS_MAX = 32767
        self._AXIS_MIN = -32768

        # Declare the goal values
        self._axis_max = 2000
        self._axis_min = -2000

        # Calculate and store the middle value for the axis
        self._axis_mid = (self._axis_max + self._axis_min) // 2

        # Initialise the axis information
        self._left_axis_x = self._axis_mid
        self._left_axis_y = self._axis_mid
        self._right_axis_x = self._axis_mid
        self._right_axis_y = self._axis_mid

    @property
    def left_axis_x(self):
        return self._left_axis_x

    @left_axis_x.setter
    def left_axis_x(self, value):
        self._left_axis_x = tl.normalise(value, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @property
    def left_axis_y(self):
        return self._left_axis_y

    @left_axis_y.setter
    def left_axis_y(self, value):
        self._left_axis_y = tl.normalise(value, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @property
    def right_axis_x(self):
        return self._right_axis_x

    @right_axis_x.setter
    def right_axis_x(self, value):
        self._right_axis_x = tl.normalise(value, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @property
    def right_axis_y(self):
        return self._right_axis_y

    @right_axis_y.setter
    def right_axis_y(self, value):
        self._right_axis_y = tl.normalise(value, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

# TODO: Add abstractions of other devices, such as thrusters, mechanical arm etc.
