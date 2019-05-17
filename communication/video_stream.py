"""

Video Stream is used to handle the visual data exchange with surface.

** Functionality **

By importing the module you gain access to the class 'VideoStream'.

You should create an instance of 'VideoStream' and use the 'run' function to start the communication. The constructor of
takes 2 optional parameters - 'ip' and 'port', which can be specified to identify the address of the Raspberry Pi (host)
to connect with the surface. Ip passed should be a string, whereas the port an integer.

Once connected, the class should handle everything, including formatting, encoding and re-connecting in case of
data loss. Additionally, the class allows you to access the frame through the 'frame' field.

You should modify any `_handle_data` functions to change how the data is processed.

** Constants and other values **

All constants and other important values are mentioned and explained within the corresponding functions.

** Example **

Let ip be 169.254.147.140 and port 50001. To host a stream with the given address, call:

    video_stream = VideoStream(ip=169.254.147.140)

The port is 50001 by default, so it's not necessary to explicitly specify it. To run, call:

    video_stream.connect()

Let frame be a cv2 numpy array. To send it, call

    video_stream.frame = frame

** Author **

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

        Function used to initialise the stream.

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

        # Override the process as a thread to handle the frame correctly
        self._thread = Thread(target=self._connect)

        # Initialise the frame-end string to recognise when a full frame was received
        self._end_payload = bytes("Frame was successfully sent", encoding="ASCII")

        # Store the frame information
        self._frame = None

        # Initialise the frame video stream data
        self._frame_partial = b''

    @property
    def frame(self):
        return self._frame

    def _handle_data(self):
        """

        Function used to exchange and process the frames.

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
        blocking send and receive functions. The data exchanged is JSON-encoded.

        ** Modifications **

            1. Modify the bottom try, except block to change non-data-specific error-handling.

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

        # Start receiving the video stream
        self._thread.start()