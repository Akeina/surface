import communication.data_manager as dm
from communication.connection import Connection
from communication.video_stream import VideoStream
from control.controller import Controller
from time import sleep
from cv2 import imshow, waitKey

# Declare the number of cameras
CAMERAS_COUNT = 3


# TODO: Remove this test script
def blocking_test_video_stream(streams):
    while True:
        for stream in streams:
            frame = stream.frame
            try:
                imshow(str(stream), frame)
                waitKey(1)
            except:
                pass


# TODO: Remove this test script
def blocking_test_text_debug():
    while True:
        print(dm.get_data(transmit=True))
        #sleep(1)


if __name__ == "__main__":

    # Initialise the ip
    ip = 'localhost'  # local testing
    #ip = "169.254.246.235"  # ROV pi
    ip = "169.254.231.182"  # Home pi

    # Clear the cache on start
    dm.clear()

    # Build the controller's instance
    controller = Controller()

    # Initialise the server connection
    connection = Connection(ip=ip, port=50000)

    # Initialise the port iterator
    port = 50010

    # Initialise the video streams
    streams = [VideoStream(ip=ip, port=p) for p in range(port, port + CAMERAS_COUNT)]

    # Start the tasks
    controller.init()
    connection.connect()

    # Start the video streams
    for stream in streams:
        stream.stream()

    blocking_test_video_stream(streams)

