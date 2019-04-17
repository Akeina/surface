import communication.data_manager as dm
from communication.connection import Connection
from communication.video_stream import VideoStream
from control.controller import Controller
from time import sleep
from cv2 import imshow, waitKey


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
        sleep(0.5)


if __name__ == "__main__":

    # Initialise the ip
    ip = 'localhost'
    #ip = "169.254.231.182"

    # Clear the cache on start
    dm.clear()

    # Initialise the connection
    connection = Connection(ip=ip)

    # Initialise the video stream
    video_stream = VideoStream(ip=ip)
    vs = VideoStream(ip=ip, port=50002)

    # Initialise the controller
    controller = Controller()

    # Start the tasks
    connection.connect()
    video_stream.connect()
    vs.connect()
    controller.init()

    blocking_test_video_stream([video_stream, vs])
