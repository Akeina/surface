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

In addition, you can change the constant values of axis' and triggers' min/max, to adjust the expected output values. To
update the data manager, adjust the '_data_manager_map' dictionary, where each key is the value to be set, and each
value corresponds to the property.

** Example **

To create a controller object, call:

    controller = Controller()

To start reading input, call:

    controller.init()

** Author **

Kacper Florianski

"""

import communication.data_manager as dm
from threading import Thread
from inputs import devices
from time import time
from pathos import helpers

# Fetch the Process class
Process = helpers.mp.Process


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

    def __init__(self):

        # Fetch the hardware reference via inputs
        try:
            self._controller = devices.gamepads[0]
        except IndexError:
            print("No game controllers detected.")
            return

        # Initialise the processes / threads
        # TODO: Change data_thread into Process, fix pickle-related issues (inputs library non-picklable)
        self._data_thread = Thread(target=self._update_data)
        self._controller_thread = Thread(target=self._read)

        # Initialise the axis hardware values
        self._AXIS_MAX = 32767
        self._AXIS_MIN = -32768

        # Initialise the axis goal values
        self._axis_max = 400
        self._axis_min = -400

        # Initialise the axis hardware values
        self._TRIGGER_MAX = 255
        self._TRIGGER_MIN = 0

        # Initialise the axis goal values
        self._trigger_max = 400
        self._trigger_min = 0

        # Declare the sensitivity level (when to update the axis value), smaller value for higher sensitivity
        self._SENSITIVITY = 100

        # Calculate and store the middle value for the axis and the triggers
        self._axis_mid = (self._axis_max + self._axis_min) // 2

        # Initialise the axis information
        self._left_axis_x = self._axis_mid
        self._left_axis_y = self._axis_mid
        self._right_axis_x = self._axis_mid
        self._right_axis_y = self._axis_mid

        # Initialise the triggers information
        self._left_trigger = 0
        self._right_trigger = 0

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

        # Initialise thruster PWM outputs
        self.thruster_FP = 1500
        self.thruster_FS = 1500
        self.thruster_AP = 1500
        self.thruster_AS = 1500
        self.thruster_TFP = 1500
        self.thruster_TFS = 1500
        self.thruster_TAP = 1500
        self.thruster_TAS = 1500

        # Initialise the event to attribute mapping
        self._dispatch_map = {
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

        # Initialise the data manager key to attribute mapping
        self._data_manager_map = {
            "lax": "left_axis_x",
            "lay": "left_axis_y",
            "rax": "right_axis_x",
            "ray": "right_axis_y",
            "lt": "left_trigger",
            "rt": "right_trigger",
            "hx": "hat_x",
            "hy": "hat_y",
            "blb": "button_LB",
            "brb": "button_RB",
            "tfs": "thruster_FS",
            "tfp": "thruster_FP",
            "tap": "thruster_AP",
            "tas": "thruster_AS",
            "ttfp": "thruster_TFP",
            "ttfs": "thruster_TFS",
            "ttap": "thruster_TAP",
            "ttas": "thruster_TAS"
        }

        # Create a separate set of the data manager keys, for performance reasons
        self._data_manager_keys = set(self._data_manager_map.keys()).copy()

        # Update the initial values
        self._tick_update_data()

        # Initialise the inputs delay (to slow down with writing the data)
        self._UPDATE_DELAY = 0.05

    @property
    def left_axis_x(self):
        return normalise(self._left_axis_x, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @left_axis_x.setter
    def left_axis_x(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._left_axis_x - value) >= self._SENSITIVITY:
            self._left_axis_x = value

    @property
    def left_axis_y(self):
        return normalise(self._left_axis_y, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @left_axis_y.setter
    def left_axis_y(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._left_axis_y - value) >= self._SENSITIVITY:
            self._left_axis_y = value

    @property
    def right_axis_x(self):
        return normalise(self._right_axis_x, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @right_axis_x.setter
    def right_axis_x(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._right_axis_x - value) >= self._SENSITIVITY:
            self._right_axis_x = value

    @property
    def right_axis_y(self):
        return normalise(self._right_axis_y, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @right_axis_y.setter
    def right_axis_y(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._right_axis_y - value) >= self._SENSITIVITY:
            self._right_axis_y = value

    @property
    def left_trigger(self):
        return normalise(self._left_trigger, self._TRIGGER_MIN, self._TRIGGER_MAX, self._trigger_min, self._trigger_max)

    @left_trigger.setter
    def left_trigger(self, value):
        self._left_trigger = value

    @property
    def right_trigger(self):
        return normalise(self._right_trigger, self._TRIGGER_MIN, self._TRIGGER_MAX, self._trigger_min, self._trigger_max)

    @right_trigger.setter
    def right_trigger(self, value):
        self._right_trigger = value

    @property
    def hat_x(self):
        return self._hat_x

    @hat_x.setter
    def hat_x(self, value):
        self._hat_x = value

    @property
    def hat_y(self):
        return self._hat_y

    @hat_y.setter
    def hat_y(self, value):
        self._hat_y = value*(-1)

    def _dispatch_event(self, event):

        # Check if a registered event was passed
        if event.code in self._dispatch_map:

            # Update the corresponding value
            self.__setattr__(self._dispatch_map[event.code], event.state)

    def _update_thrusters(self):

        # Values to be added to PWM thruster output
        t1 = t2 = t3 = t4 = t5 = t6 = t7 = t8 = 0

        # Speed when button pressed. Choose values between 1 and 400.
        button_speed = 400

        # Forward
        e = self.right_trigger
        if e:
            t1 += e
            t2 += e
            t3 += e
            t4 += e

        # Reverse
        e = self.left_trigger
        if e:
            t1 -= e
            t2 -= e
            t3 -= e
            t4 -= e

        # Yaw rotate
        e = self.right_axis_x
        if e:
            t1 += e
            t2 -= e
            t3 += e
            t4 -= e

        # Translate left
        e = self.button_X
        if e:
            t1 -= e*button_speed
            t2 += e*button_speed
            t3 += e*button_speed
            t4 -= e*button_speed

        # Translate right
        e = self.button_Y
        if e:
            t1 += e*button_speed
            t2 -= e*button_speed
            t3 -= e*button_speed
            t4 += e*button_speed

        # Pitch rotate
        e = self.left_axis_y
        if e:
            t5 += e
            t6 += e
            t7 -= e
            t8 -= e

        # Roll rotate
        e = self.left_axis_x
        if e:
            t5 += e
            t6 -= e
            t7 += e
            t8 -= e

        # Upward
        e = self.button_RB
        if e:
            t5 += e*button_speed
            t6 += e*button_speed
            t7 += e*button_speed
            t8 += e*button_speed

        # Downward
        e = self.button_LB
        if e:
            t5 -= e*button_speed
            t6 -= e*button_speed
            t7 -= e*button_speed
            t8 -= e*button_speed

        # Scale the values down if necessary not to overcome 400
        # t1 = t1 if t1 <= 400 else normalise(t1, 0, t1, 0, 400)
        # t2 = t2 if t2 <= 400 else normalise(t2, 0, t2, 0, 400)
        # t3 = t3 if t3 <= 400 else normalise(t3, 0, t3, 0, 400)
        # t4 = t4 if t4 <= 400 else normalise(t4, 0, t4, 0, 400)
        # t5 = t5 if t5 <= 400 else normalise(t5, 0, t5, 0, 400)
        # t6 = t6 if t6 <= 400 else normalise(t6, 0, t6, 0, 400)
        # t7 = t7 if t7 <= 400 else normalise(t7, 0, t7, 0, 400)
        # t8 = t8 if t8 <= 400 else normalise(t8, 0, t8, 0, 400)

        # TODO: Find out proper scaling for thrusters. Right now the output value saturates at 1900 when exceeded.
        # Saturates value at 400 when exceeded. Code equivalent to above.
        t1 = t1 if t1 < 400 else 400
        t2 = t2 if t2 < 400 else 400
        t3 = t3 if t3 < 400 else 400
        t4 = t4 if t4 < 400 else 400
        t5 = t5 if t5 < 400 else 400
        t6 = t6 if t6 < 400 else 400
        t7 = t7 if t7 < 400 else 400
        t8 = t8 if t8 < 400 else 400

        # Update the thruster PWM output
        self.thruster_FP = 1500 + t1
        self.thruster_FS = 1500 + t2
        self.thruster_AP = 1500 + t3
        self.thruster_AS = 1500 + t4
        self.thruster_TFP = 1500 + t5
        self.thruster_TFS = 1500 + t6
        self.thruster_TAP = 1500 + t7
        self.thruster_TAS = 1500 + t8

    def _tick_update_data(self):

        # Map joystick events to thruster PWM thruster output
        self._update_thrusters()

        # Iterate over all keys that should be updated (use copy of the set to avoid runtime concurrency errors)
        for key in self._data_manager_keys:

            # Update the corresponding value
            dm.set_data(**{key: self.__getattribute__(self._data_manager_map[key])})

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
            self._data_thread.start()
            self._controller_thread.start()

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
