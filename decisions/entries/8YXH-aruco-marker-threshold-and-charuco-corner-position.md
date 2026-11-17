# 8YXH — ArUco marker threshold 0.5 and the ChArUco corner position of OpenCV 5

**Status:** accepted, 2026-11-16 (user, question X4 of 2026-11-16).

## Decision

1. Each calibration detector of skellytracker sets the ArUco marker parameter
   `validBitIdThreshold` to 0.5 explicitly. This applies to the charuco detector, the aruco detector
   and the board selector `CharucoBoardSelector`. One helper builds the `DetectorParameters`:
   `create_aruco_detector_parameters()` in
   `skellytracker/core/detectors/calibration_detectors/aruco_parameters.py`, with the constant
   `VALID_BIT_ID_THRESHOLD`.
2. No config field and no option sets the threshold.
3. skellytracker adds no offset to a ChArUco corner or to an ArUco marker corner. The corner
   positions are those of OpenCV 5.0. The centre of pixel (0, 0) is (0.0, 0.0).
4. A regression test pins the corner position. It renders a synthetic ChArUco board with OpenCV,
   moves it with a known sub-pixel affine map, and detects it with the package detector. The mean
   error of the corners must be less than 0.05 px in x and in y. The RMS error must be less than
   0.2 px. The test uses 30 px and 40 px for each square
   (`test_charuco_corners_have_no_position_bias` in `skellytracker/tests/test_charuco_detector.py`).

## Reason

- OpenCV 4.14 and 5.0 added `DetectorParameters.validBitIdThreshold` with the default 0.49
  (upstream PR 28289). A marker cell that is exactly half white is then a bit error.
  `DICT_4X4_250` allows 0 error bits, so OpenCV rejects the marker. Blur and distance make such
  cells. A calibration board needs each corner. The board layout and the marker ids filter false
  markers.
- OpenCV 4.14 and 5.0 also removed a bias of +0.5 px from the ChArUco corners (upstream PR 28380,
  issue 25539). The corner positions of OpenCV 5.0 are correct. An offset would put the error back.
- `pyproject.toml` pins `opencv-contrib-python==5.0.0.93`.

## Consequences

- A calibration made with OpenCV 4.13 or earlier used corners with a bias of about +0.5 px. When
  that calibration optimises the principal point, its `cx` and `cy` are about 0.5 px too large.
  freemocap holds the principal point fixed. There the difference goes into the extrinsics, the
  focal length and the distortion. Do not mix a calibration of OpenCV 4.13 or earlier with corners of
  OpenCV 5.0.
- The regression test fails with about +0.5 px on OpenCV 4.13 or earlier. A change of the OpenCV pin
  that changes the corner convention fails the test.

## Evidence

- ChArUco corner count on the freemocap test recording, three cameras, a one-off measurement of
  2026-11-16: OpenCV 4.12 found 666, 619 and 1088 corners. OpenCV 5.0.0
  (`opencv-contrib-python` 5.0.0.93) with the default parameters found 580, 462 and 978. OpenCV 5.0.0
  with `validBitIdThreshold` 0.5 found 664, 617 and 1089. Plain ArUco detection loses markers in
  the same way.
- Synthetic boards, a one-off measurement of 2026-11-16: the corner bias of OpenCV 5.0.0 is less
  than 0.01 px. The bias of OpenCV 4.12 is +0.47 px to +0.50 px. On a board of 5 by 3 squares,
  rendered at 600 by 360 px with a margin of 30 px, the first corner is at (149.5, 129.5). OpenCV
  5.0.0 gives (149.490, 129.490). OpenCV 4.12 gives (149.995, 129.995).
- The regression test through the package detector, `opencv-contrib-python` 5.0.0.93: each of the
  24 corners found. Mean error from -0.0041 px to +0.0035 px, RMS from 0.064 px to 0.091 px, over
  the four cases. The same image with plain `cv2.aruco.CharucoDetector` on
  `opencv-contrib-python-headless` 4.12.0.88: mean error (+0.486, +0.496) px, RMS 0.70 px.
- `test_a_blurred_small_board_keeps_each_corner` in `skellytracker/tests/test_charuco_detector.py`:
  a board of 7 by 5 squares at 16 px for each square with a Gaussian blur of 0.8 px. With 0.5, the
  detector finds 17 of 17 markers and 24 of 24 corners. With 0.49, it finds 14 markers and
  16 corners.

## Alternatives rejected

- **0.49, the OpenCV default.** Fewer corners on a blurred or a distant board.
- **An offset of +0.5 px on each corner.** It would copy the bias of OpenCV 4.13 and earlier. That
  bias is a defect that OpenCV fixed.
- **A config field for the threshold.** Nobody asked for it.
