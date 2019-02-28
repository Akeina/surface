import communication.data_manager as dm
from communication.connection import Connection

if __name__ == "__main__":
    s = Connection(dm)
    #s = Connection(dm, ip="169.254.147.140", port=50001)
    s.connect()