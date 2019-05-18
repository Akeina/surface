"""
Video Stream
************

Description
===========

This module is used to handle the visual data exchange with the Raspberry Pi in a separate thread.

Functionality
=============

VideoStream
-----------

The :class:`VideoStream` class provides a TCP-based streaming of a single camera.

Execution
---------

To start the stream, you should create an instance of :class:`VideoStream` and call :func:`stream`::

    stream = VideoStream(ip=ip, port=port)
    stream.stream()

where `ip` and `port` are the connection-related values.

Functions & classes
-------------------

.. note::

    Remember that the code is further described by in-line comments and docstrings.

The following list shortly summarises the functionality of each code component within the :class:`VideoStream` class:

    1. :class:`DataError` is a support class to handle custom exceptions
    2. :func:`__init__` builds the stream object
    3. :func:`frame` is a getter for the camera frame
    4. :func:`_handle_data` receives and sends the data
    5. :func:`_connect` runs an infinite loop to keep exchanging the data (frames)
    6. :func:`stream` starts the streaming thread

Modifications
=============

The only functions that could require modification are :func:`_on_surface_disconnected` and :func:`_handle_data`, as
the module expands. You should also consider modifying the `self._TIMEOUT` value within :func:`__init__`.

Authorship
==========

Kacper Florianski
"""

import socket
from time import sleep
from dill import loads
from threading import Thread
from _pickle import UnpicklingError


class VideoStream:

    # Custom exception to handle data errors
    class DataError(Exception):
        pass

    def __init__(self, ip="localhost", port=50001):
        """
        Constructor function used to initialise the stream.

        It is recommended that you change the `self._RECONNECT_DELAY` to adjust the delay on reconnection with the Pi.

        :param ip: Raspberry Pi's IP address
        :param port: Raspberry Pi's port
        """

        # Save the host and port information
        self._ip = ip
        self._port = port

        # Initialise the socket field
        self._socket = None

        # Initialise the delay constant to offload some computing power when reconnecting
        self._RECONNECT_DELAY = 1

        # Build and store the thread instance
        self._thread = Thread(target=self._connect)

        # Initialise the frame-end string to recognise when a full frame was received
        self._end_payload = bytes("Frame was successfully sent", encoding="ASCII")

        # Store the frame information
        self._frame = None

        # Initialise the frame video stream data
        self._frame_partial = b''

    @property
    def frame(self):
        """
        Getter for the camera frame

        :return: OpenCV-formatted frame (numpy array)
        """

        return self._frame

    def _handle_data(self):
        """
        Function used to process the frames and send them to surface.

        Any frame-related modifications should be introduced here, preferably encapsulated in another function.
        """

        # Once connected, keep receiving and sending the data, raise exception in case of errors
        try:
            # Receive the data
            self._frame_partial += self._socket.recv(4096)

            # If 0-byte was received, raise exception
            if not self._frame_partial:
                sleep(self._RECONNECT_DELAY)
                raise self.DataError

            # Check if a full frame was sent
            if self._frame_partial[-len(self._end_payload):] == self._end_payload:

                # Un-pickle the frame or set it to None if it's empty
                self._frame = loads(self._frame_partial[:-len(self._end_payload)]) if self._frame_partial else None

                # Reset the video stream data
                self._frame_partial = b''

                # Send the acknowledgement
                self._socket.sendall(bytes("ACK", encoding="ASCII"))

        except (ConnectionResetError, ConnectionAbortedError, UnpicklingError):
            sleep(self._RECONNECT_DELAY)
            raise self.DataError

    def _connect(self):
        """
        Function used to run a continuous connection with Raspberry Pi.

        Runs an infinite loop that performs re-connection to the given address as well as exchanges data with it, via
        blocking send and receive functions. The data exchanged is pickled using :mod:`dill`.
        """

        # Never stop the connection once it was started
        while True:

            try:
                # Check if the socket is None to avoid running into errors when reconnecting
                if self._socket is None:

                    # Inform that client is attempting to connect to the server
                    print("Connecting to video stream at {}:{}...".format(self._ip, self._port))

                    # Set the socket for IPv4 addresses (hence AF_INET) and TCP (hence SOCK_STREAM)
                    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Connect to the server
                self._socket.connect((self._ip, self._port))
                print("Connected to video stream at {}:{}, starting data exchange".format(self._ip, self._port))

                # Keep exchanging data
                while True:

                    # Attempt to handle the data, break in case of errors
                    try:
                        self._handle_data()
                    except self.DataError:
                        break

                # Cleanup
                self._socket.close()
                self._socket = None

                # Inform that the connection is closed
                print("Video stream at {}:{} closed successfully".format(self._ip, self._port))

            except (ConnectionRefusedError, OSError):
                sleep(self._RECONNECT_DELAY)
                continue

    def stream(self):
        """
        Function used to start the streaming thread.
        """

        # Start receiving the video stream
        self._thread.start()
