import communication.data_manager as dm
from communication.connection import Connection
from control.controller import Controller


if __name__ == "__main__":

    # Clear the cache on start
    dm.clear()

    # Initialise the connection
    connection = Connection()#, ip="169.254.147.140", port=50001)

    # Initialise the controller
    controller = Controller()

    # Start the tasks
    connection.connect()
    controller.init()
