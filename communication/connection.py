import socket
from json import loads, dumps, JSONDecodeError
from time import sleep

import communication.data_manager as dm


class Connection:

    def __init__(self, *, ip="localhost", port=50000):

        # Save the host and port information
        self._ip = ip
        self._port = port

        # Initialise the socket field
        self._socket = None

        # Initialise the delay constant to offload some computing power when reconnecting
        self._RECONNECT_DELAY = 1

    def connect(self):

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
                        self._socket.sendall(bytes(dumps(dm.get_data()), encoding="utf-8"))

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
                            dm.set_data(**loads(data))
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


if __name__ == "__main__":
    s = Connection()
    #s = Connection(ip="169.254.147.140", port=50001)
    s.connect()
