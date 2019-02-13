import socket
from json import loads, dumps, JSONDecodeError

import communication.data_manager as dm


# TODO:
'''
Attempt to make it a non-blocking client, just in case (although deadlock should not happen). If happens and isn't fixed
by OS (and therefore Python's exception) - possibly add resetting the server/client after a certain amount of time
'''


class Connection:

    def __init__(self, *, ip="localhost", port=50000):

        # Save the host and port information
        self._ip = ip
        self._port = port

        # Initialise the socket field
        self._socket = None

    def connect(self):

        # Never stop the connection once it was started
        while True:

            if self._socket is None:
                # Inform that client is attempting to connect to the server
                print("Connecting to {}:{}...".format(self._ip, self._port))

            try:
                # Initialise the socket for IPv4 addresses (hence AF_INET) and TCP (hence SOCK_STREAM)
                if self._socket is None:
                    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Connect to the server
                self._socket.connect((self._ip, self._port))
                print("Connected, starting data exchange")

                # Keep exchanging data
                while True:

                    # Send current state of the data manager
                    self._socket.sendall(bytes(dumps(dm.data.get()), encoding="utf-8"))

                    try:
                        # Once connected, keep receiving and sending the data, break in case of errors
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
                            dm.data.set(**loads(data))
                        except JSONDecodeError:
                            print("Received invalid data: {}".format(data))

                # Cleanup
                self._socket.close()
                self._socket = None

                # Inform that the connection is closed
                print("Connection to {}:{} closed successfully".format(self._ip, self._port))

            except ConnectionRefusedError:
                continue


if __name__ == "__main__":
    s = Connection()
    s.connect()
