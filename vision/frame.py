import cv2


class Frame:

    def __init__(self):

        # Create a new VideoCapture object
        self.cap = cv2.VideoCapture(0)

    def __call__(self):

        # Catch the frame
        flag, frame = self.cap.read()

        # Return the frame or None on failure
        return frame if flag else None


def test():

    # Create a new Frame object
    f = Frame()

    # Keep streaming the view
    while True:

        # Catch the next frame
        frame = f()

        # Display a valid frame
        if frame is not None:
            cv2.imshow("Testing", frame)
            cv2.waitKey(1)
