"""
Controller
**********

Description
===========

Controller is used to read and process the game pad input.

Functionality
=============

Controller
----------

The :class:`Controller` class provides complex input reading and processing, connected with the :class:`DataManager`.

Execution
---------

To start the controller, you should create an instance of :class:`Controller` and call :func:`init`, for example::

    controller = Controller()
    controller.init()

.. note::

    You will be notified if the controller isn't detected.

Functions & classes
-------------------

.. note::

    Remember that the code is further described by in-line comments and docstrings.

The following list shortly summarises the functionality of each code component within the :class:`Server` class:

    1. :func:`__init__` builds the controller, returns at the beginning if no controller is detected
    2. :func:`_dispatch_event` dispatches controller readings into class fields
    3. :func:`_tick_update_data` updates the :class:`DataManager` with the current values
    4. :func:`_update_data` runs an infinite loop to keep updating the :class:`DataManager`
    5. :func:`_read` runs an infinite loop to keep reading the controller input
    6. :func:`_register_thrusters` initialises thruster-related controls
    7. :func:`_register_motors` initialises motor-related controls
    8. :func:`_register_light` initialises light-related controls
    9. :func:`init` starts all threads

Additionally, the :func:`normalise` provides the scaling of values to meet the expected range.

Fields
------

The :class:`Controller` provides a number of fields that are accessible via the corresponding getters.

Axis (ints)
+++++++++++

    - left_axis_x
    - left_axis_y
    - right_axis_x
    - right_axis_y

Triggers (ints)
+++++++++++++++

    - left_trigger
    - right_trigger

* Hat (ints) *

    - hat_y
    - hat_x

Buttons (booleans)
++++++++++++++++++

    - button_A
    - button_B
    - button_X
    - button_Y
    - button_LB
    - button_RB
    - button_left_stick
    - button_right_stick
    - button_select
    - button_start

On top of acquiring the information about the controller, PWM outputs are provided. Precisely:

Thrusters (ints)
++++++++++++++++

    - thruster_fp
    - thruster_fs
    - thruster_ap
    - thruster_as
    - thruster_tfp
    - thruster_tfs
    - thruster_tap
    - thruster_tas

Motors (ints)
+++++++++++++

    - motor_arm
    - motor_gripper
    - motor_box

Modifications
=============

This module may require an extensive number of modifications to introduce any changes to it. To modify the behaviour of
the controller itself, you should look into :func:`__init__` and adjust the constants inside. To change the control
system, you should adjust the code within functions starting with `_register`, or add more.

.. warning::

    You must follow the style present in the current registering functions if you were to add a new one.

Authorship
==========

Kacper Florianski

Modified by
-----------

Pawel Czaplewski
"""

import communication.data_manager as dm
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

    def __init__(self):
        """
        Constructor function used to initialise the controller. Returns early if no controller is detected.

        You should modify:

            1. `self._axis_max' and '_axis_min' constants to specify the expected axis values.
            2. `self._trigger_max' and '_trigger_min' constants to specify the expected trigger values.
            3. `self._SENSITIVITY' constant to specify how sensitive should the values setting be.
            4. Hardcoded value in '_button_sensitivity' to specify the quickly should the buttons change the values.
            5. `self._data_manager_map' dictionary to synchronise the controller with the data manager.
            6. `self._UPDATE_DELAY' constant to specify the read delay from the controller.
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

        # Create a separate set of the data manager keys, for performance reasons
        self._data_manager_keys = set(self._data_manager_map.keys()).copy()

        # Create a separate dict to remember the last state of the values and avoid updating the cache unnecessarily
        self._data_manager_last_saved = dict()

        # Update the initial values
        self._tick_update_data()

        # Initialise the cache delay (to slow down with writing the data)
        self._UPDATE_DELAY = 0.025

    @property
    def left_axis_x(self):
        """
        Getter for the left stick x-axis.

        :return: Normalised controller reading
        """

        return normalise(self._left_axis_x, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @left_axis_x.setter
    def left_axis_x(self, value):
        """
        Setter for the left stick x-axis. Updates the value if the sensitivity threshold was passed.
        """

        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._left_axis_x - value) >= self._SENSITIVITY:
            self._left_axis_x = value

    @property
    def left_axis_y(self):
        """
        Getter for the left stick y-axis.

        :return: Normalised controller reading
        """

        return normalise(self._left_axis_y, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @left_axis_y.setter
    def left_axis_y(self, value):
        """
        Setter for the left stick y-axis. Updates the value if the sensitivity threshold was passed.
        """

        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._left_axis_y - value) >= self._SENSITIVITY:
            self._left_axis_y = value

    @property
    def right_axis_x(self):
        """
        Getter for the right stick x-axis.

        :return: Normalised controller reading
        """

        return normalise(self._right_axis_x, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @right_axis_x.setter
    def right_axis_x(self, value):
        """
        Setter for the right stick x-axis. Updates the value if the sensitivity threshold was passed.
        """

        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._right_axis_x - value) >= self._SENSITIVITY:
            self._right_axis_x = value

    @property
    def right_axis_y(self):
        """
        Getter for the right stick y-axis.

        :return: Normalised controller reading
        """

        return normalise(self._right_axis_y, self._AXIS_MIN, self._AXIS_MAX, self._axis_min, self._axis_max)

    @right_axis_y.setter
    def right_axis_y(self, value):
        """
        Setter for the right stick y-axis. Updates the value if the sensitivity threshold was passed.
        """

        if value == self._AXIS_MAX or value == self._AXIS_MIN or abs(self._right_axis_y - value) >= self._SENSITIVITY:
            self._right_axis_y = value

    @property
    def left_trigger(self):
        """
        Getter for the left trigger.

        :return: Normalised controller reading
        """

        return normalise(self._left_trigger, self._TRIGGER_MIN, self._TRIGGER_MAX,
                         self._trigger_min, 2 * self._trigger_min - self._trigger_max)

    @left_trigger.setter
    def left_trigger(self, value):
        """
        Setter for the left trigger.
        """

        self._left_trigger = value

    @property
    def right_trigger(self):
        """
        Getter for the right trigger.

        :return: Normalised controller reading
        """

        return normalise(self._right_trigger, self._TRIGGER_MIN, self._TRIGGER_MAX, self._trigger_min,
                         self._trigger_max)

    @right_trigger.setter
    def right_trigger(self, value):
        """
        Setter for the right trigger.
        """

        self._right_trigger = value

    @property
    def hat_x(self):
        """
        Getter for the hat x-axis.

        :return: Normalised controller reading
        """

        return self._hat_x

    @hat_x.setter
    def hat_x(self, value):
        """
        Setter for the hat x-axis.
        """

        self._hat_x = value

    @property
    def hat_y(self):
        """
        Getter for the hat y-axis.

        :return: Normalised controller reading
        """

        return self._hat_y

    @hat_y.setter
    def hat_y(self, value):
        """
        Setter for the hat y-axis.
        """

        self._hat_y = value * (-1)

    def _dispatch_event(self, event):
        """
        Function used to dispatch each controller event into its corresponding value.

        :param event: Controller (:mod:`inputs`) event
        """

        # Check if a registered event was passed
        if event.code in self._dispatch_map:

            # Update the corresponding value
            self.__setattr__(self._dispatch_map[event.code], event.state)

    def _tick_update_data(self):
        """
        Function used to update the data manager with the current controller values.
        """

        # Iterate over all keys that should be updated (use copy of the set to avoid runtime concurrency errors)
        for key in self._data_manager_keys:

            # Fetch the current attribute's value
            value = self.__getattribute__(self._data_manager_map[key])

            # Check if the last saved value and the current reading mismatch
            if key not in self._data_manager_last_saved or self._data_manager_last_saved[key] != value:

                # Update the corresponding values
                dm.set_data(**{key: value})
                self._data_manager_last_saved[key] = value

    def _update_data(self):
        """
        Function used to keep updating the manager with controller values.
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

        You should modify each sub-function to change the thrusters' controls.
        """

        # Create custom functions to update the thrusters
        def _update_thruster_fp(self):

            # If surge and yaw
            if self.left_axis_y != self._idle and self.right_axis_x != self._idle:

                # If backwards
                if self.left_axis_y < self._idle:
                    return 2 * self._idle - self.left_axis_y

                # Else forwards
                else:
                    return 2 * self._idle - self.right_axis_x

            # If surge only
            elif self.left_axis_y != self._idle:
                return 2 * self._idle - self.left_axis_y

            # If sway only
            elif self.right_axis_x != self._idle:
                return 2 * self._idle - self.right_axis_x

            # If yaw starboard
            elif self.right_trigger != self._idle:
                return 2 * self._idle - self.right_trigger

            # If yaw pot
            elif self.left_trigger != self._idle:
                return 2 * self._idle - self.left_trigger

            # Else idle
            else:
                return self._idle

        def _update_thruster_fs(self):

            # If surge and yaw
            if self.left_axis_y != self._idle and self.right_axis_x != self._idle:

                # If backwards
                if self.left_axis_y < self._idle:
                    return 2 * self._idle - self.left_axis_y

                # Else forwards
                else:
                    return self.right_axis_x

            # If surge only
            elif self.left_axis_y != self._idle:
                return 2 * self._idle - self.left_axis_y

            # If sway only
            elif self.right_axis_x != self._idle:
                return self.right_axis_x

            # If yaw starboard
            elif self.right_trigger != self._idle:
                return self.right_trigger

            # If yaw pot
            elif self.left_trigger != self._idle:
                return self.left_trigger

            # Else idle
            else:
                return self._idle

        def _update_thruster_ap(self):

            # If surge and yaw
            if self.left_axis_y != self._idle and self.right_axis_x != self._idle:

                # If forwards
                if self.left_axis_y > self._idle:
                    return self.left_axis_y

                # Else backwards
                else:
                    return 2 * self._idle - self.right_axis_x

            # If surge only
            elif self.left_axis_y != self._idle:
                return self.left_axis_y

            # If sway only
            elif self.right_axis_x != self._idle:
                return 2 * self._idle - self.right_axis_x

            # If yaw starboard
            elif self.right_trigger != self._idle:
                return self.right_trigger

            # If yaw pot
            elif self.left_trigger != self._idle:
                return self.left_trigger

            # Else idle
            else:
                return self._idle

        def _update_thruster_as(self):

            # If surge and yaw
            if self.left_axis_y != self._idle and self.right_axis_x != self._idle:

                # If forwards
                if self.left_axis_y > self._idle:
                    return self.left_axis_y

                # Else backwards
                else:
                    return self.right_axis_x

            # If surge only
            elif self.left_axis_y != self._idle:
                return self.left_axis_y

            # If sway only
            elif self.right_axis_x != self._idle:
                return self.right_axis_x

            # If yaw starboard
            elif self.right_trigger != self._idle:
                return 2 * self._idle - self.right_trigger

            # If yaw pot
            elif self.left_trigger != self._idle:
                return 2 * self._idle - self.left_trigger

            # Else idle
            else:
                return self._idle

        def _update_thruster_tfp(self):

            # If full upwards
            if self.button_RB:
                return self._idle + self._button_sensitivity

            # If full downwards
            elif self.button_LB:
                return self._idle - self._button_sensitivity

            # If pitch
            elif self.hat_y:
                return self._idle - self.hat_y * self._button_sensitivity

            # If roll
            elif self.hat_x:
                return self._idle + self.hat_x * self._button_sensitivity

            # Else idle
            else:
                return self._idle

        def _update_thruster_tfs(self):

            # If full upwards
            if self.button_RB:
                return self._idle + self._button_sensitivity

            # If full downwards
            elif self.button_LB:
                return self._idle - self._button_sensitivity

            # If pitch
            elif self.hat_y:
                return self._idle - self.hat_y * self._button_sensitivity

            # If roll
            elif self.hat_x:
                return self._idle - self.hat_x * self._button_sensitivity

            # Else idle
            else:
                return self._idle

        def _update_thruster_tap(self):

            # If full upwards
            if self.button_RB:
                return self._idle + self._button_sensitivity

            # If full downwards
            elif self.button_LB:
                return self._idle - self._button_sensitivity

            # If pitch
            elif self.hat_y:
                return self._idle + self.hat_y * self._button_sensitivity

            # If roll
            elif self.hat_x:
                return self._idle + self.hat_x * self._button_sensitivity

            # Else idle
            else:
                return self._idle

        def _update_thruster_tas(self):

            # If full upwards
            if self.button_RB:
                return self._idle + self._button_sensitivity

            # If full downwards
            elif self.button_LB:
                return self._idle - self._button_sensitivity

            # If pitch
            elif self.hat_y:
                return self._idle + self.hat_y * self._button_sensitivity

            # If roll
            elif self.hat_x:
                return self._idle - self.hat_x * self._button_sensitivity

            # Else idle
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

        You should modify each sub-function to change the motors' controls.
        """

        # Initialise the arm rotation sensitivity
        arm_rotation_speed = min(100, self._axis_max - self._idle)

        # Initialise the box opening sensitivity
        box_movement_speed = min(100, self._axis_max - self._idle)

        # Create custom functions to update the motors
        def _update_arm(self):

            # If starboard
            if self.button_B:
                return self._idle - arm_rotation_speed

            # If pot
            elif self.button_X:
                return self._idle + arm_rotation_speed

            # Else idle
            else:
                return self._idle

        def _update_gripper(self):

            # If upwards
            if self.button_Y:
                return self._idle + self._button_sensitivity

            # If downwards
            elif self.button_A:
                return self._idle - self._button_sensitivity

            # Else idle
            else:
                return self._idle

        def _update_box(self):

            # If left box
            if self.button_left_stick:
                return self._idle - box_movement_speed

            # If right box
            elif self.button_right_stick:
                return self._idle + box_movement_speed

            # Else idle
            else:
                return self._idle

        # Register the thrusters as the properties
        self.__class__.motor_arm = property(_update_arm)
        self.__class__.motor_gripper = property(_update_gripper)
        self.__class__.motor_box = property(_update_box)

        # Update the data manager with the new properties
        self._data_manager_map["Mot_R"] = "motor_arm"
        self._data_manager_map["Mot_G"] = "motor_gripper"
        self._data_manager_map["Mot_F"] = "motor_box"

    def init(self):
        """
        Function used to start the controller reading threads. Only executes if the controller is correctly detected.
        """

        # Check if the controller was correctly created
        if not hasattr(self, "_controller"):
            print("Controller initialisation error detected.")

        # Start the threads (to not block the main execution) with event dispatching and data updating
        else:
            self._data_thread.start()
            self._controller_thread.start()
            print("Controller initialised.")
