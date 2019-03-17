# TODO: Remove unused imports
import communication.data_manager as dm
from communication.connection import Connection
from communication.video_stream import VideoStream
from control.controller import Controller
from cv2 import imshow, waitKey


# TODO: Remove this test script
def sample_video_stream():
    while True:
        frame = video_stream.frame
        try:
            imshow("frame", frame)
            waitKey(1)
        except:
            pass


# TODO: Remove this test script
def sample_text_debug():
    while True:
        print(dm.get_data())


if __name__ == "__main__":

    # Initialise the ip
    ip = 'localhost' #ip = "169.254.147.140"

    # Clear the cache on start
    dm.clear()

    # Initialise the connection
    connection = Connection(ip=ip)

    # Initialise the video stream
    video_stream = VideoStream(ip=ip)

    # Initialise the controller
    controller = Controller()

    # Start the tasks
    connection.connect()
    video_stream.connect()
    controller.init()

    # TODO: Remove this test script
    sample_video_stream()
