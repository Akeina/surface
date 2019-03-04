import communication.data_manager as dm
from communication.connection import Connection
from control.controller import Controller
from time import sleep

if __name__ == "__main__":
    c = Connection(dm)#, ip="169.254.147.140", port=50001)
    Controller(dm).init()
    c.connect()
    while True:
        print("Data from main module: ", dm.get_data())
        pass