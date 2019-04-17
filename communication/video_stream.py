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

from communication.connection import Connection
from time import sleep
from dill import loads
from threading import Thread


class VideoStream(Connection):

    def __init__(self, ip="localhost", port=50001):
        """

        Function used to initialise the stream.

        :param ip: Raspberry Pi's IP address
        :param port: Raspberry Pi's port

        """

        # Super the TCP data exchange functionality
        super().__init__(ip=ip, port=port)

        # Override the process as a thread to handle the frame correctly
        self._connection_process = Thread(target=self._connect)

        # Initialise the frame-end string to recognise when a full frame was received
        self._end_payload = bytes("Frame was successfully sent", encoding="ASCII")

        # Store the frame information
        self._frame = None

        # Initialise the frame video stream data
        self._frame_partial = b''

        # Override the communication delay
        self._COMMUNICATION_DELAY = 0

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

        except (ConnectionResetError, ConnectionAbortedError):
            sleep(self._RECONNECT_DELAY)
            raise self.DataError
