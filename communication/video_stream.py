from communication.connection import Connection
from time import sleep
from dill import loads
from threading import Thread


class VideoStream(Connection):

    def __init__(self, ip="localhost", port=50001):

        # Super TCP data exchange functionality
        super().__init__(ip=ip, port=port)

        self._connection_process = Thread(target=self._connect)

        # Initialise the frame-end string
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
