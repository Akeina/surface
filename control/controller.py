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

On top of acquiring the information about the controller, thrusters PWM outputs are provided. Precisely:

    thruster_fp
    thruster_fs
    thruster_ap
    thruster_as
    thruster_tfp
    thruster_tfs
    thruster_tap
    thruster_tas

To change their behaviour, you should modify the '_register_thrusters' function, and all its sub-functions.

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
        self._axis_max = 1900
        self._axis_min = 1100

        # Initialise the axis hardware values
        self._TRIGGER_MAX = 255
        self._TRIGGER_MIN = 0

        # Initialise the axis goal values
        self._trigger_max = 1900
        self._trigger_min = 1500

        # Declare the sensitivity level (when to update the axis value), smaller value for higher sensitivity
        self._SENSITIVITY = 100

        # Initialise the axis information
        self._left_axis_x = 0
        self._left_axis_y = 0
        self._right_axis_x = 0
        self._right_axis_y = 0

        # Initialise the triggers information
        self._left_trigger = 0
        self._right_trigger = 0

        # Initialise the hat information
        self._hat_y = 0
        self._hat_x = 0

        # Initialise PWM idle output
        self.idle = normalise(0, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

        # Speed when button pressed
        self.button_speed = 400
        self.servo_speed = 20

        # Initialise servo extreme positions
        self._SERVO_MAX = 1900
        self._SERVO_MIN = 1100

        # Initialise servo and servo-like LED starting positions
        self._arm_servo = 1500      # 1500 - middle position
        self._lamp_brightness = 1100     # 1100 - off; 1900 - full brightness

        # Generate a region of self._lamp_brightness below self._SERVO_MIN and above self._SERVO_MAX.
        # This is to make easier to turn off the lamp and keep it at full brightness.
        self._lamp_extended_range = 200
        self._lamp_min = self._SERVO_MIN - self._lamp_extended_range
        self._lamp_max = self._SERVO_MAX + self._lamp_extended_range

        # Initialise controller stick deadzone
        self._deadzone = 0.15       # Deadzone in %
        self._deadzone_min = int(self.idle - (self._axis_max - self.idle) * self._deadzone)
        self._deadzone_max = int(self.idle + (self._axis_max - self.idle) * self._deadzone)

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
        }

        # Handle non-thruster joystick controls
        self._non_thruster_controls()

        # Register the thrusters
        self._register_thrusters()

        # Create a separate set of the data manager keys, for performance reasons
        self._data_manager_keys = set(self._data_manager_map.keys()).copy()

        # Update the initial values
        self._tick_update_data()

        # Initialise the inputs delay (to slow down with writing the data)
        self._UPDATE_DELAY = 0.05

    @property
    def left_axis_x(self):
        value = normalise(self._left_axis_x, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)
        return value if value < self._deadzone_min or value > self._deadzone_max else self.idle

    @left_axis_x.setter
    def left_axis_x(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._left_axis_x - value) >= self._SENSITIVITY:
            self._left_axis_x = value

    @property
    def left_axis_y(self):
        value = normalise(self._left_axis_y, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)
        return value if value < self._deadzone_min or value > self._deadzone_max else self.idle

    @left_axis_y.setter
    def left_axis_y(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._left_axis_y - value) >= self._SENSITIVITY:
            self._left_axis_y = value

    @property
    def right_axis_x(self):
        value = normalise(self._right_axis_x, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)
        return value if value < self._deadzone_min or value > self._deadzone_max else self.idle

    @right_axis_x.setter
    def right_axis_x(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._right_axis_x - value) >= self._SENSITIVITY:
            self._right_axis_x = value

    @property
    def right_axis_y(self):
        value = normalise(self._right_axis_y, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)
        return value if value < self._deadzone_min or value > self._deadzone_max else self.idle

    @right_axis_y.setter
    def right_axis_y(self, value):
        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._right_axis_y - value) >= self._SENSITIVITY:
            self._right_axis_y = value

    @property
    def left_trigger(self):
        return normalise(self._left_trigger, self._TRIGGER_MIN, self._TRIGGER_MAX, self._trigger_min, 2 * self._trigger_min - self._trigger_max)

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

    def _tick_update_data(self):

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

    def _non_thruster_controls(self):

        def _update_arm_servo(self):
            if self.hat_x == 1 and self._arm_servo < self._SERVO_MAX:
                self._arm_servo += self.servo_speed
            elif self.hat_x == -1 and self._arm_servo > self._SERVO_MIN:
                self._arm_servo -= self.servo_speed
            return self._arm_servo

        def _update_arm_gripper(self):
            return self.idle + self.hat_y * self.button_speed   # Hat can return values: -1, 0, 1

        def _update_lamp_brightness(self):
            if self.button_B:
                if self._lamp_brightness >= self._lamp_max:     # Resets the LED PWM output after reaching maximum
                    self._lamp_brightness = self._lamp_min
                self._lamp_brightness += self.servo_speed
            if self._lamp_brightness < self._SERVO_MIN:
                return self._SERVO_MIN
            elif self._lamp_brightness > self._SERVO_MAX:
                return self._SERVO_MAX
            return self._lamp_brightness

        self.__class__.arm_servo = property(_update_arm_servo)
        self.__class__.arm_gripper = property(_update_arm_gripper)
        self.__class__.lamp_brightness = property(_update_lamp_brightness)

        self._data_manager_map["Mot_R"] = "arm_servo"
        self._data_manager_map["Mot_G"] = "arm_gripper"
        self._data_manager_map["LED_M"] = "lamp_brightness"

    def _register_thrusters(self):

        # Create custom functions to update the thrusters
        def _update_thruster_fp(self):
            if self.right_trigger != self.idle:
                return self.right_trigger
            elif self.left_trigger != self.idle:
                return self.left_trigger
            elif self.right_axis_x != self.idle:
                return self.right_axis_x
            elif self.button_X:
                return self.idle - self.button_speed
            elif self.button_Y:
                return self.idle + self.button_speed
            else:
                return self.idle

        def _update_thruster_fs(self):
            if self.right_trigger != self.idle:
                return self.right_trigger
            elif self.left_trigger != self.idle:
                return self.left_trigger
            elif self.right_axis_x != self.idle:
                return 2 * self.idle - self.right_axis_x
            elif self.button_X:
                return self.idle + self.button_speed
            elif self.button_Y:
                return self.idle - self.button_speed
            else:
                return self.idle

        def _update_thruster_ap(self):

            if self.right_axis_x != self.idle:
                return self.right_axis_x
            elif self.right_trigger != self.idle:
                return self.right_trigger
            elif self.left_trigger != self.idle:
                return self.left_trigger
            elif self.button_X:
                return self.idle + self.button_speed
            elif self.button_Y:
                return self.idle - self.button_speed
            else:
                return self.idle

        def _update_thruster_as(self):
            if self.right_axis_x != self.idle:
                return 2 * self.idle - self.right_axis_x
            elif self.right_trigger != self.idle:
                return self.right_trigger
            elif self.left_trigger != self.idle:
                return self.left_trigger
            elif self.button_X:
                return self.idle - self.button_speed
            elif self.button_Y:
                return self.idle + self.button_speed
            else:
                return self.idle

        def _update_thruster_tfp(self):
            if self.button_RB:
                return self.idle + self.button_speed
            elif self.button_LB:
                return self.idle - self.button_speed
            elif self.left_axis_y != self.idle:
                return self.left_axis_y
            elif self.left_axis_x != self.idle:
                return self.left_axis_x
            else:
                return self.idle

        def _update_thruster_tfs(self):
            if self.button_RB:
                return self.idle + self.button_speed
            elif self.button_LB:
                return self.idle - self.button_speed
            elif self.left_axis_y != self.idle:
                return self.left_axis_y
            elif self.left_axis_x != self.idle:
                return 2 * self.idle - self.left_axis_x
            else:
                return self.idle

        def _update_thruster_tap(self):
            if self.button_RB:
                return self.idle + self.button_speed
            elif self.button_LB:
                return self.idle - self.button_speed
            elif self.left_axis_y != self.idle:
                return 2 * self.idle - self.left_axis_y
            elif self.left_axis_x != self.idle:
                return self.left_axis_x
            else:
                return self.idle

        def _update_thruster_tas(self):
            if self.button_RB:
                return self.idle + self.button_speed
            elif self.button_LB:
                return self.idle - self.button_speed
            elif self.left_axis_y != self.idle:
                return 2 * self.idle - self.left_axis_y
            elif self.left_axis_x != self.idle:
                return 2 * self.idle - self.left_axis_x
            else:
                return self.idle

        # Register the thrusters as the properties
        self.__class__.thruster_fp = property(_update_thruster_fp)
        self.__class__.thruster_fs = property(_update_thruster_fs)
        self.__class__.thruster_ap = property(_update_thruster_ap)
        self.__class__.thruster_as = property(_update_thruster_as)
        self.__class__.thruster_tfp = property(_update_thruster_tfp)
        self.__class__.thruster_tfs = property(_update_thruster_tfs)
        self.__class__.thruster_tap = property(_update_thruster_tap)
        self.__class__.thruster_tas = property(_update_thruster_tas)

        # Update the data manager with the new properties
        self._data_manager_map["Thr_FP"] = "thruster_fp"
        self._data_manager_map["Thr_FS"] = "thruster_fs"
        self._data_manager_map["Thr_AP"] = "thruster_ap"
        self._data_manager_map["Thr_AS"] = "thruster_as"
        self._data_manager_map["Thr_TFP"] = "thruster_tfp"
        self._data_manager_map["Thr_TFS"] = "thruster_tfs"
        self._data_manager_map["Thr_TAP"] = "thruster_tap"
        self._data_manager_map["Thr_TAS"] = "thruster_tas"

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
