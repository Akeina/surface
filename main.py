import communication.data_manager as dm
from communication.connection import Connection
from control.controller import Controller

if __name__ == "__main__":
    Controller(dm).init()
    s = Connection(dm)#, ip="169.254.147.140", port=50001)
    s.connect()
