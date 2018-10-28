import socket


class Connection:

    def __init__(self, *, ip="localhost", port=50000):
        # TODO: Come up with different statuses (probably just a list of constants)
        # TODO: Finish the __init__ method with all other, necessary init information

        # Save the host and port information
        self.ip = ip
        self.port = port

        # Initialise the status information
        self.status = 0

        # Initialise the socket for IPv4 addresses (hence AF_INET) and TCP (hence SOCK_STREAM)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __call__(self):
        # TODO: Write functionality that would be called to run the connection, e.g. connect to the server, receive data
        pass

    def receive(self):
        # TODO: Write a method that receives formatted data
        pass

    def send(self, data):
        # TODO: Write a method that sends formatted data
        pass
