"""

Connection is used to handle the information exchange with the Raspberry Pi.

** Usage **

By importing the module you gain access to the class 'Connection'.

You should create an instance of it and use the 'connect' function to start the communication. The constructor of the
'Connection' class takes 2 optional parameters - 'ip' and 'port', which can be specified to identify address of the
Raspberry Pi. Ip passed should be a string, whereas the port an integer. Both arguments are of the keyword-only type.

Once connected, the 'Connection' class should handle everything, including formatting, encoding and re-connecting in
case of data loss.

** Example **

The data manager will be referred to as 'dm'.

Let ip be 169.254.147.140 and port 50000. To connect with the Raspberry Pi at the given address, call:

    connection = Connection(dm, ip=169.254.147.140)

The port is 50000 by default, so it's not necessary to explicitly specify it. To connect, call:

    connection.connect()

** Author **

Kacper Florianski

"""

import socket
from json import loads, dumps, JSONDecodeError
from time import sleep


class Connection:

    def __init__(self, dm: "Data Manager", *, ip="localhost", port=50000):

        # Store the data manager information
        self._dm = dm

        # Save the host and port information
        self._ip = ip
        self._port = port

        # Initialise the socket field
        self._socket = None

        # Initialise the delay constant to offload some computing power when reconnecting
        self._RECONNECT_DELAY = 1

    def connect(self):
        """

        Method used to run a continuous connection with Raspberry Pi.

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
                print("Connected, starting data exchange")

                # Keep exchanging data
                while True:

                    # Once connected, keep receiving and sending the data, break in case of errors
                    try:
                        # Send current state of the data manager
                        self._socket.sendall(bytes(dumps(self._dm.get_data(transmit=True)), encoding="utf-8"))

                        # Receive the data
                        data = self._socket.recv(4096)

                        # If 0-byte was received, close the connection
                        if not data:
                            break

                    except ConnectionResetError:
                        break
                    except ConnectionAbortedError:
                        break

                    # Convert bytes to string, remove white spaces, ignore invalid data
                    try:
                        data = data.decode("utf-8").strip()
                    except UnicodeDecodeError:
                        data = None

                    # Handle valid data
                    if data:

                        # Attempt to decode from JSON, inform about invalid data received
                        try:
                            self._dm.set_data(**loads(data))
                        except JSONDecodeError:
                            print("Received invalid data: {}".format(data))

                # Cleanup
                self._socket.close()
                self._socket = None

                # Inform that the connection is closed
                print("Connection to {}:{} closed successfully".format(self._ip, self._port))

            except ConnectionRefusedError:
                continue
            except OSError:
                # Reconnect in case of host socket loss (e.g. Ethernet unplugged)
                sleep(self._RECONNECT_DELAY)
                continue
