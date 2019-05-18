"""
High-level software
*******************

Description
===========

This module is used to run the surface control station.

Functionality
=============

Execution
---------

To start the code, you should execute the following command::

    python main.py

where `python` is the python's version.

Modifications
=============

You should modify this module as much as needed.

.. warning::

    Remember to initialise all components first, and start them later (so that you can have a loading screen).

Authorship
==========

Kacper Florianski
"""

import communication.data_manager as dm
from communication.connection import Connection
from communication.video_stream import VideoStream
from control.controller import Controller
from cv2 import imshow, waitKey

# Declare the number of cameras
CAMERAS_COUNT = 3


# TODO: Remove this test script when the GUI is implemented (all it does is show the video frames)
def blocking_test_video_stream(streams):
    while True:
        for stream in streams:
            frame = stream.frame
            try:
                imshow(str(stream), frame)
                waitKey(1)
            except:
                pass


if __name__ == "__main__":

    # Initialise the ip
    ip = 'localhost'  # local testing
    #ip = "169.254.246.235"  # ROV pi
    #ip = "169.254.231.182"  # Kacper's personal pi

    # Inform that the initialisation phase has started
    print("Loading...")

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

    # Inform that the execution phase has started
    print("Starting tasks...")

    # Start the connection and controller tasks
    controller.init()
    connection.connect()

    # Start the video streams
    for stream in streams:
        stream.stream()

    # Inform that the code has fully executed
    print("Tasks initialised and started successfully")

    # TODO: Remove this line
    blocking_test_video_stream(streams)
