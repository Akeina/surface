"""

Controller is used to read and process game pad input.

** Usage **

By importing the module you gain access to the class 'Controller', and some additional methods.

You should create an instance of it and use the 'init' function to start reading the input. The class will keep reading
the controller data and lets you access it through multiple fields. A complete list is as follows:

* Axis (ints) *

    left_axis_x
    left_axis_y
    right_axis_x
    right_axis_y

* Triggers (ints) *

    left_trigger
    right_trigger

* Hat (ints) *

    hat_y
    hat_x

* Buttons (booleans) *

    button_A
    button_B
    button_X
    button_Y
    button_LB
    button_RB
    button_left_stick
    button_right_stick
    button_select
    button_start

In addition, you can change the constant values of axis' and triggers' min max, to adjust the expected output values. In
order to update the data manager with a certain value, adjust the '_create_data_manager_keys' method. Remember, you must
provide both the setter and the getter for the field as well as update the '_keys_to_update' set in such setter.

** Example **

The data manager will be referred to as 'dm'.

To create a controller object, call:

    controller = Controller(dm)

To start reading input, call:

    controller.init()

** Author **

Kacper Florianski

"""

from threading import Thread
from inputs import devices
from time import time


def normalise(value, current_min, current_max, intended_min, intended_max):
    """

    Function used to normalise a value to fit within a given range, knowing its actual range. MinMax normalisation.

    :param value: Value to be normalised
    :param current_min: The actual minimum of the value
    :param current_max: The actual maximum of the value
    :param intended_min: The expected minimum of the value
    :param intended_max: The expected maximum of the value
    :return: Normalised value

    """
    return int(intended_min + (value - current_min) * (intended_max - intended_min) / (current_max - current_min))


class Controller:

    def __init__(self, dm: "Data Manager"):

        # Store the data manager information
        self._dm = dm

        # Fetch the hardware reference via inputs
        try:
            self._controller = devices.gamepads[0]
        except IndexError:
            print("No game controllers detected.")
            return

        # Initialise the axis hardware values
        self._AXIS_MAX = 32767
        self._AXIS_MIN = -32768

        # Initialise the axis goal values
        self._axis_max = 2000
        self._axis_min = -2000

        # Initialise the axis hardware values
        self._TRIGGER_MAX = 255
        self._TRIGGER_MIN = 0

        # Initialise the axis goal values
        self._trigger_max = 255
        self._trigger_min = 0

        # Declare the sensitivity level (when to update the axis value), smaller value for higher sensitivity
        self._SENSITIVITY = 100

        # Calculate and store the middle value for the axis and the triggers
        self._axis_mid = (self._axis_max + self._axis_min) // 2
        self._trigger_mid = (self._trigger_max + self._trigger_min) // 2

        # Initialise the axis information
        self._left_axis_x = self._axis_mid
        self._left_axis_y = self._axis_mid
        self._right_axis_x = self._axis_mid
        self._right_axis_y = self._axis_mid

        # Initialise the triggers information
        self._left_trigger = self._trigger_mid
        self._right_trigger = self._trigger_mid

        # Initialise the hat information
        self._hat_y = 0
        self._hat_x = 0

        # Initialise the buttons information
        self.button_A = False
        self.button_B = False
        self.button_X = False
        self.button_Y = False
        self.button_LB = False
        self.button_RB = False
        self.button_left_stick = False
        self.button_right_stick = False
        self.button_select = False
        self.button_start = False

        # Initialise the event to field mapping
        self._create_dispatch_keys()

        # Initialise the data manager keys to field mapping
        self._create_data_manager_keys()

        # Initialise the data manager keys to update
        self._keys_to_update = set()

        # Initialise the inputs delay (to slow down with reading the data)
        self._UPDATE_DELAY = 0.01

    @property
    def left_axis_x(self):
        return normalise(self._left_axis_x, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @left_axis_x.setter
    def left_axis_x(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._left_axis_x - value) >= self._SENSITIVITY:
            self._left_axis_x = value
            self._keys_to_update.add("lax")

    @property
    def left_axis_y(self):
        return normalise(self._left_axis_y, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @left_axis_y.setter
    def left_axis_y(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._left_axis_y - value) >= self._SENSITIVITY:
            self._left_axis_y = value
            self._keys_to_update.add("lay")

    @property
    def right_axis_x(self):
        return normalise(self._right_axis_x, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @right_axis_x.setter
    def right_axis_x(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._right_axis_x - value) >= self._SENSITIVITY:
            self._right_axis_x = value
            self._keys_to_update.add("rax")

    @property
    def right_axis_y(self):
        return normalise(self._right_axis_y, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @right_axis_y.setter
    def right_axis_y(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._right_axis_y - value) >= self._SENSITIVITY:
            self._right_axis_y = value
            self._keys_to_update.add("ray")

    @property
    def left_trigger(self):
        return normalise(self._left_trigger, self._TRIGGER_MIN, self._TRIGGER_MAX, self._trigger_min, self._trigger_max)

    @left_trigger.setter
    def left_trigger(self, value):
        self._left_trigger = value
        self._keys_to_update.add("lt")

    @property
    def right_trigger(self):
        return normalise(self._right_trigger, self._TRIGGER_MIN, self._TRIGGER_MAX, self._trigger_min, self._trigger_max)

    @right_trigger.setter
    def right_trigger(self, value):
        self._right_trigger = value
        self._keys_to_update.add("rt")

    @property
    def hat_x(self):
        return self._hat_x

    @hat_x.setter
    def hat_x(self, value):
        self._hat_x = value
        self._keys_to_update.add("hx")

    @property
    def hat_y(self):
        return self._hat_y

    @hat_y.setter
    def hat_y(self, value):
        self._hat_y = value*(-1)
        self._keys_to_update.add("hy")

    def _create_dispatch_keys(self):

        self._dispatch_keys = {
            "ABS_X": "left_axis_x",
            "ABS_Y": "left_axis_y",
            "ABS_RX": "right_axis_x",
            "ABS_RY": "right_axis_y",
            "ABS_Z": "left_trigger",
            "ABS_RZ": "right_trigger",
            "ABS_HAT0X": "hat_x",
            "ABS_HAT0Y": "hat_y",
            "BTN_SOUTH": "button_A",
            "BTN_EAST": "button_B",
            "BTN_WEST": "button_X",
            "BTN_NORTH": "button_Y",
            "BTN_TL": "button_LB",
            "BTN_TR": "button_RB",
            "BTN_THUMBL": "button_left_stick",
            "BTN_THUMBR": "button_right_stick",
            "BTN_START": "button_select",
            "BTN_SELECT": "button_start"
        }

    def _create_data_manager_keys(self):

        self._data_manager_keys = {
            "lax": "left_axis_x",
            "lay": "left_axis_y",
            "rax": "right_axis_x",
            "ray": "right_axis_y",
            "lt": "left_trigger",
            "rt": "right_trigger",
            "hx": "hat_x",
            "hy": "hat_y",
        }

    def _dispatch_event(self, event):

        # Check if a registered event was passed
        if event.code in self._dispatch_keys:

            # Update the corresponding value
            self.__setattr__(self._dispatch_keys[event.code], event.state)

    def _tick_update_data(self):

        # Iterate over all keys that should be updated (use copy of the set to avoid runtime concurrency errors)
        for key in self._keys_to_update.copy():

            # Update the corresponding value
            self._dm.set_data(**{key: self.__getattribute__(self._data_manager_keys[key])})

    def _update_data(self):

        # Initialise the time counter
        timer = time()

        # Keep updating the data
        while True:

            # Update the data if enough time passed
            if time() - timer > self._UPDATE_DELAY:
                self._tick_update_data()
                timer = time()

    def _read(self):

        # Keep reading the input
        while True:

            # Get the current event
            event = self._controller.read()[0]

            # Distribute the event to a corresponding field
            self._dispatch_event(event)

    def init(self):

        # Check if the controller was correctly created
        if not hasattr(self, "_controller"):
            print("Controller initialisation error detected.")

        # Start the threads (to not block the main execution) with event dispatching and data updating
        else:
            Thread(target=self._read).start()
            Thread(target=self._update_data).start()

    def __str__(self):
        return "\n".join([
            "Left axis: ({}, {})".format(self.left_axis_x, self.left_axis_y),
            "Right axis: ({}, {})".format(self.right_axis_x, self.right_axis_y),
            "Hat: ({}, {})".format(self.hat_x, self.hat_y),
            "Triggers: LT: {}, RT: {}".format(self.left_trigger, self.right_trigger),
            "Buttons: A: {}, B: {}, X: {}, Y: {}".format(self.button_A, self.button_B, self.button_X, self.button_Y),
            "Buttons: Left stick: {}, Right stick: {}, LB: {}, RB: {}"
                .format(self.button_left_stick, self.button_right_stick, self.button_LB, self.button_RB),
            "Buttons: Select: {}, Start: {}".format(self.button_select, self.button_start)
        ])
