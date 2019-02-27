from threading import Thread
from inputs import devices
from time import sleep


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
        self._controller = devices.gamepads[0]

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

        # Initialise the inputs delay (to slow down with reading the data)
        self._READ_DELAY = 0.01

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
        self._hat_y = value

    def _dispatch_event(self, event):

        # Listen to non-button changes (these values will have getters and setters)
        if event.code[:4] == "ABS_":

            # Listen to axis change
            if event.code == "ABS_X":
                self.left_axis_x = event.state
            elif event.code == "ABS_Y":
                self.left_axis_y = event.state
            elif event.code == "ABS_RX":
                self.right_axis_x = event.state
            elif event.code == "ABS_RY":
                self.right_axis_y = event.state

            # Listen to trigger change
            elif event.code == "ABS_Z":
                self.left_trigger = event.state
            elif event.code == "ABS_RZ":
                self.right_trigger = event.state

            # Listen to hat change
            elif event.code == "ABS_HAT0X":
                self.hat_x = event.state
            elif event.code == "ABS_HAT0Y":
                self.hat_y = event.state

        # Listen to button changes
        else:
            if event.code == "BTN_SOUTH":
                self.button_A = bool(event.state)
            elif event.code == "BTN_EAST":
                self.button_B = bool(event.state)
            elif event.code == "BTN_WEST":
                self.button_X = bool(event.state)
            elif event.code == "BTN_NORTH":
                self.button_Y = bool(event.state)
            elif event.code == "BTN_TL":
                self.button_LB = bool(event.state)
            elif event.code == "BTN_TR":
                self.button_RB = bool(event.state)
            elif event.code == "BTN_THUMBL":
                self.button_left_stick = bool(event.state)
            elif event.code == "BTN_THUMBR":
                self.button_right_stick = bool(event.state)
            elif event.code == "BTN_START":
                self.button_select = bool(event.state)
            elif event.code == "BTN_SELECT":
                self.button_start = bool(event.state)

    def _read(self):

        # Keep reading the input
        while True:

            # Get the current event
            event = self._controller.read()[0]

            # Distribute the event to a corresponding field
            self._dispatch_event(event)

            # Delay the next read
            sleep(self._READ_DELAY)

    def init(self):

        # Start the thread (to not block the main execution)
        Thread(target=self._read).start()

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
