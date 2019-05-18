"""
Connection
**********

Description
===========

This module is used to handle the information exchange with middle-level of the system. It uses pathos multiprocessing
and a :class:`DataManager` to handle the data flow.

Functionality
=============

Connection
----------

The :class:`Connection` class provides a TCP-based data exchange with the Raspberry Pi.

Execution
---------

To start the communication, you should create an instance of :class:`Connection` and call :func:`connect`, for example::

    connection = Connection(port=50000)
    connection.connect()

Functions & classes
-------------------

.. note::

    Remember that the code is further described by in-line comments and docstrings.

The following list shortly summarises the functionality of each code component within the :class:`Connection` class:

    1. :class:`DataError` is a support class to handle custom exceptions
    2. :func:`__init__` builds the connection
    7. :func:`_handle_data` receives and sends the data to the Raspberry Pi
    8. :func:`_connect` runs an infinite loop to keep exchanging the data with the Pi
    9. :func:`run` starts the connection process

Modifications
=============

The only functions that could require modification is :func:`_handle_data`, as the module expands. You should also
consider modifying the `self._RECONNECT_DELAY` and `self._COMMUNICATION_DELAY` values within :func:`__init__`.

Authorship
==========

Kacper Florianski
"""

import socket
import communication.data_manager as dm
from json import loads, dumps, JSONDecodeError
from time import sleep
from pathos import helpers

# Fetch the Process class
Process = helpers.mp.Process


class Connection:

    # Custom exception to handle data errors
    class DataError(Exception):
        pass

    def __init__(self, *, ip="localhost", port=50000):
        """
        Constructor function used to initialise the communication with Raspberry Pi.

        You should modify:

            1. `self._RECONNECT_DELAY` constant to specify the delay value (seconds) on connection loss.
            2. `self._COMMUNICATION_DELAY` constant to specify the delay value (seconds) on communication.

        :param ip: Raspberry Pi's IP address
        :param port: Raspberry Pi's port
        """

        # Initialise the connection process
        self._connection_process = Process(target=self._connect)

        # Save the host and port information
        self._ip = ip
        self._port = port

        # Initialise the socket field
        self._socket = None

        # Initialise the delay constant to offload some computing power when reconnecting
        self._RECONNECT_DELAY = 1

        # Initialise the communication delay
        self._COMMUNICATION_DELAY = 0.01

    def _handle_data(self):
        """
        Function used to receive and send the processed data.

        Any data-related modifications should be introduced here, preferably encapsulated in another function.
        """

        # Once connected, keep receiving and sending the data, raise exception in case of errors
        try:
            # Send current state of the data manager
            self._socket.sendall(bytes(dumps(dm.get_data(transmit=True)), encoding="utf-8"))

            # Receive the data
            data = self._socket.recv(4096)

            # If 0-byte was received, raise exception
            if not data:
                sleep(self._RECONNECT_DELAY)
                raise self.DataError

        except (ConnectionResetError, ConnectionAbortedError):
            sleep(self._RECONNECT_DELAY)
            raise self.DataError

        # Convert bytes to string, remove white spaces, ignore invalid data
        try:
            data = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            data = None

        # Handle valid data
        if data:

            # Attempt to decode from JSON, inform about invalid data received
            try:
                dm.set_data(**loads(data))
            except JSONDecodeError:
                print("Received invalid data: {}".format(data))

    def _connect(self):
        """
        Function used to run a continuous connection with Raspberry Pi.

        Runs an infinite loop that performs re-connection to the given address as well as exchanges data with it, via
        blocking send and receive functions. The data exchanged is JSON-encoded.
        """

        # Never stop the connection once it was started
        while True:

            try:
                # Check if the socket is None to avoid running into errors when reconnecting
                if self._socket is None:

                    # Inform that client is attempting to connect to the server
                    print("Connecting to {}:{}...".format(self._ip, self._port))

                    # Set the socket for IPv4 addresses (hence AF_INET) and TCP (hence SOCK_STREAM)
                    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Connect to the server
                self._socket.connect((self._ip, self._port))
                print("Connected to {}:{}, starting data exchange".format(self._ip, self._port))

                # Keep exchanging data
                while True:

                    # Attempt to handle the data, break in case of errors
                    try:
                        self._handle_data()
                    except self.DataError:
                        break

                    # Delay the communication
                    sleep(self._COMMUNICATION_DELAY)

                # Cleanup
                self._socket.close()
                self._socket = None

                # Inform that the connection is closed
                print("Connection to {}:{} closed successfully".format(self._ip, self._port))

            except (ConnectionRefusedError, OSError):
                sleep(self._RECONNECT_DELAY)
                continue

    def connect(self):
        """
        Function used to start the connection process.
        """

        # Start the process (to not block the main execution)
        self._connection_process.start()
