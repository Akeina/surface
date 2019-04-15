"""

Controller is used to read and process game pad input.

** Functionality **

By importing the module you gain access to the class 'Controller', and some additional functions.

You should create an instance of it and use the 'init' function to start reading the input. The class will automatically
read all controller events and dispatch them to corresponding fields as well as update the data manager if needed.

You should modify the `__init__` function to change any functionality of the class.

** Constants and other values **

The class lets you access the controller's state through multiple fields. A complete list is as follows:

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

On top of acquiring the information about the controller, PWM outputs are provided. Precisely:

* Thrusters *

    thruster_fp
    thruster_fs
    thruster_ap
    thruster_as
    thruster_tfp
    thruster_tfs
    thruster_tap
    thruster_tas

* Motors *

    motor_arm
    motor_gripper

* Light *

    light_brightness

To change their behaviour, you should modify functions like '_register_thrusters', and all its sub-functions.

** Example **

To create a controller object, call:

    controller = Controller()

To start reading input, call:

    controller.init()

** Author **

Kacper Florianski

** Extended by **

Pawel Czaplewski

"""

import communication.data_manager as dm
from threading import Thread
from inputs import devices
from time import time
from numba import jit


@jit
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
        """

        Function used to initialise the controller.

        ** Modifications **

            1. Modify the '_axis_max' and '_axis_min' constants to specify the expected axis values.

            2. Modify the '_trigger_max' and '_trigger_min' constants to specify the expected trigger values.

            3. Modify the '_SENSITIVITY' constant to specify how sensitive should the values setting be.

            4. Modify the value in '_button_sensitivity' to specify the quickly should the buttons change the values.

            5. Modify the '_data_manager_map' dictionary to synchronise the controller with the data manager.

            6. Modify the '_UPDATE_DELAY' constant to specify the read delay from the controller.

        """

        # Fetch the hardware reference via inputs
        try:
            self._controller = devices.gamepads[0]
        except IndexError:
            print("No game controllers detected.")
            return

        # Initialise the threads
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

        # Initialise the idle value (default PWM output)
        self._idle = normalise(0, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

        # Initialise the button sensitivity (higher value for bigger PWM values' changes)
        self._button_sensitivity = min(400, self._axis_max - self._idle)

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

        # Register thrusters, motors and the light
        self._register_thrusters()
        self._register_motors()
        self._register_light()

        # Create a separate set of the data manager keys, for performance reasons
        self._data_manager_keys = set(self._data_manager_map.keys()).copy()

        # Update the initial values
        self._tick_update_data()

        # Initialise the inputs delay (to slow down with writing the data)
        self._UPDATE_DELAY = 0.03

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
        return normalise(self._left_trigger, self._TRIGGER_MIN, self._TRIGGER_MAX,
                         self._trigger_min, 2 * self._trigger_min - self._trigger_max)

    @left_trigger.setter
    def left_trigger(self, value):
        self._left_trigger = value

    @property
    def right_trigger(self):
        return normalise(self._right_trigger, self._TRIGGER_MIN, self._TRIGGER_MAX, self._trigger_min,
                         self._trigger_max)

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
        self._hat_y = value * (-1)

    def _dispatch_event(self, event):
        """

        Function used to dispatch each controller event into its corresponding value.

        :param event: Controller event

        """

        # Check if a registered event was passed
        if event.code in self._dispatch_map:

            # Update the corresponding value
            self.__setattr__(self._dispatch_map[event.code], event.state)

    def _tick_update_data(self):
        """

        Function used to update the data manager.

        """

        # Iterate over all keys that should be updated (use copy of the set to avoid runtime concurrency errors)
        for key in self._data_manager_keys:

            # Update the corresponding value
            dm.set_data(**{key: self.__getattribute__(self._data_manager_map[key])})

    def _update_data(self):
        """

        Function used to periodically update the data manager.

        """

        # Initialise the time counter
        timer = time()

        # Keep updating the data
        while True:

            # Update the data if enough time passed
            if time() - timer > self._UPDATE_DELAY:
                self._tick_update_data()
                timer = time()

    def _read(self):
        """

        Function used to read an event from the controller and dispatch it accordingly.

        """

        # Keep reading the input
        while True:

            # Get the current event
            event = self._controller.read()[0]

            # Distribute the event to a corresponding field
            self._dispatch_event(event)

    def _register_thrusters(self):
        """

        Function used to associate thruster values with the controller.

        You should modify each sub-function to change how the values are calculated.

        """

        # Create custom functions to update the thrusters
        def _update_thruster_fp(self):
            if self.right_trigger != self._idle:
                return self.right_trigger
            elif self.left_trigger != self._idle:
                return self.left_trigger
            elif self.right_axis_x != self._idle:
                return self.right_axis_x
            elif self.button_X:
                return self._idle - self._button_sensitivity
            elif self.button_Y:
                return self._idle + self._button_sensitivity
            else:
                return self._idle

        def _update_thruster_fs(self):
            if self.right_trigger != self._idle:
                return self.right_trigger
            elif self.left_trigger != self._idle:
                return self.left_trigger
            elif self.right_axis_x != self._idle:
                return 2 * self._idle - self.right_axis_x
            elif self.button_X:
                return self._idle + self._button_sensitivity
            elif self.button_Y:
                return self._idle - self._button_sensitivity
            else:
                return self._idle

        def _update_thruster_ap(self):

            if self.right_axis_x != self._idle:
                return self.right_axis_x
            elif self.right_trigger != self._idle:
                return self.right_trigger
            elif self.left_trigger != self._idle:
                return self.left_trigger
            elif self.button_X:
                return self._idle + self._button_sensitivity
            elif self.button_Y:
                return self._idle - self._button_sensitivity
            else:
                return self._idle

        def _update_thruster_as(self):
            if self.right_axis_x != self._idle:
                return 2 * self._idle - self.right_axis_x
            elif self.right_trigger != self._idle:
                return self.right_trigger
            elif self.left_trigger != self._idle:
                return self.left_trigger
            elif self.button_X:
                return self._idle - self._button_sensitivity
            elif self.button_Y:
                return self._idle + self._button_sensitivity
            else:
                return self._idle

        def _update_thruster_tfp(self):
            if self.button_RB:
                return self._idle + self._button_sensitivity
            elif self.button_LB:
                return self._idle - self._button_sensitivity
            elif self.left_axis_y != self._idle:
                return self.left_axis_y
            elif self.left_axis_x != self._idle:
                return self.left_axis_x
            else:
                return self._idle

        def _update_thruster_tfs(self):
            if self.button_RB:
                return self._idle + self._button_sensitivity
            elif self.button_LB:
                return self._idle - self._button_sensitivity
            elif self.left_axis_y != self._idle:
                return self.left_axis_y
            elif self.left_axis_x != self._idle:
                return 2 * self._idle - self.left_axis_x
            else:
                return self._idle

        def _update_thruster_tap(self):
            if self.button_RB:
                return self._idle + self._button_sensitivity
            elif self.button_LB:
                return self._idle - self._button_sensitivity
            elif self.left_axis_y != self._idle:
                return 2 * self._idle - self.left_axis_y
            elif self.left_axis_x != self._idle:
                return self.left_axis_x
            else:
                return self._idle

        def _update_thruster_tas(self):
            if self.button_RB:
                return self._idle + self._button_sensitivity
            elif self.button_LB:
                return self._idle - self._button_sensitivity
            elif self.left_axis_y != self._idle:
                return 2 * self._idle - self.left_axis_y
            elif self.left_axis_x != self._idle:
                return 2 * self._idle - self.left_axis_x
            else:
                return self._idle

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

    def _register_motors(self):
        """

        Function used to associate motor values with the controller.

        You should modify each sub-function to change how the values are calculated.

        """

        # Initialise the servo motor position tracking and its rotation speed
        self._arm_servo = 1500
        self._arm_servo_speed = 20

        # Create custom functions to update the thrusters
        def _update_arm(self):
            if self.hat_x == 1 and self._arm_servo + self._arm_servo_speed <= self._axis_max:
                self._arm_servo += self._arm_servo_speed
            elif self.hat_x == -1 and self._arm_servo - self._arm_servo_speed >= self._axis_min:
                self._arm_servo -= self._arm_servo_speed
            return self._arm_servo

        def _update_gripper(self):
            return self._idle + self.hat_y * self._button_sensitivity

        def _update_box(self):
            return self._idle

        # Register the thrusters as the properties
        self.__class__.motor_arm = property(_update_arm)
        self.__class__.motor_gripper = property(_update_gripper)
        self.__class__.motor_box = property(_update_box)

        # Update the data manager with the new properties
        self._data_manager_map["Mot_R"] = "motor_arm"
        self._data_manager_map["Mot_G"] = "motor_gripper"
        self._data_manager_map["Mot_F"] = "motor_box"

    def _register_light(self):
        """

        Function used to associate light values with the controller.

        You should modify each sub-function to change how the values are calculated.

        """

        # Initialise the LED brightness tracking and its illumination change speed
        self._lamp_brightness = 1100
        self._lamp_speed = 50

        # Create custom functions to update the thrusters
        def _update_brightness(self):
            if self.button_B and self._lamp_brightness + self._lamp_speed <= self._axis_max:
                self._lamp_brightness += self._lamp_speed
            elif self.button_A and self._lamp_brightness - self._lamp_speed >= self._axis_min:
                self._lamp_brightness -= self._lamp_speed
            return self._lamp_brightness

        # Register the thrusters as the properties
        self.__class__.light_brightness = property(_update_brightness)

        # Update the data manager with the new properties
        self._data_manager_map["LED_M"] = "light_brightness"

    def init(self):
        """

        Function used to initialise the controller (start reading)

        """

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
