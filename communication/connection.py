"""

Connection is used to handle the information exchange with the Raspberry Pi.

** Functionality **

By importing the module you gain access to the class 'Connection'.

You should create an instance of it and use the 'connect' function to start the communication. The constructor of the
'Connection' class takes 2 optional parameters - 'ip' and 'port', which can be specified to identify address of the
Raspberry Pi. Ip passed should be a string, whereas the port an integer. Both arguments are of the keyword-only type.

Once connected, the 'Connection' class should handle everything, including formatting, encoding and re-connecting in
case of data loss.

You should modify the '__init__' function to perform any additional initialisations of the communication.

You should modify the '_connect' function to change the existing ways of exchanging information with Raspberry Pi
as well as modify behaviour when the connection between surface and the Pi is lost.

You should modify any `_handle_data` functions to change how the data is processed.

** Constants and other values **

All constants and other important values are mentioned and explained within the corresponding functions.

** Example **

Let ip be 169.254.147.140 and port 50000. To connect with the Raspberry Pi at the given address, call:

    connection = Connection(ip=169.254.147.140)

The port is 50000 by default, so it's not necessary to explicitly specify it. To connect, call:

    connection.connect()

** Author **

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

        Function used to initialise the communication.

         ** Modifications **

            1. Modify the '_RECONNECT_DELAY' constant to specify the delay value (seconds) on connection loss.

            2. Modify the '_COMMUNICATION_DELAY' constant to specify the delay value (seconds) on communication.

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
        self._COMMUNICATION_DELAY = 0.05

    def connect(self):
        """

        Function used to connect with the Pi.

        """

        # Start the process (to not block the main execution)
        self._connection_process.start()

    def _handle_data(self):
        """

        Function used to exchange and process the data.

        ** Modifications **

            1. Modify any try, except blocks to change the error-handling (keep in mind to use the DataError exception).

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

        ** Modifications **

            1. Modify the bottom try, except block to change non-data-specific error-handling.

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
