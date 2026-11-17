import cv2

# OpenCV 4.14 and 5.0 moved the default to 0.49, which rejects a marker cell that is half white.
# A calibration board needs each corner, and the board layout and the marker ids filter false markers.
VALID_BIT_ID_THRESHOLD = 0.5


def create_aruco_detector_parameters() -> cv2.aruco.DetectorParameters:
    """The ArUco marker parameters of each calibration detector."""
    parameters = cv2.aruco.DetectorParameters()
    parameters.validBitIdThreshold = VALID_BIT_ID_THRESHOLD
    return parameters
