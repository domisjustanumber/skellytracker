# Cost of the detector preprocess, 2026-11-17

This file holds a measurement that [open-work.md](../open-work.md) held until
[ADR-8ACK](../entries/8ACK-hardware-runs-checklist.md). No entry holds these numbers. The later
timing of the yolox preprocess is in
[ADR-B5Z0](../entries/B5Z0-yolox-preprocess-timing-on-an-intel-igpu-system.md).

Measured on 2026-11-17 (`time.perf_counter_ns`, one desktop CPU, OpenCV 5.0.0.93, no other load):
`preprocess_image` of `core/detectors/processing/pre/preprocess.py` needs about 5.2 ms for one
1280x720 frame with the `yolox-person` sidecar at size `m` (640x640), almost the same at 1920x1080
and 3840x2160. It needs about 1.2 ms with `rtmw-wholebody133` at size `m` (256x192). The known
causes:

- `letterbox` of `pre/resize_letterbox.py` needs about 1.8 ms, and its `cv2.resize` call 0.2 to
  0.4 ms. The canvas fill from a `float64` array uses most of the difference.
- `normalize` of `pre/normalize.py` makes a cast and two or three float passes over each pixel of
  the model input.
- A detector prepares the images of a frame one after the other in one `preprocess` span, so the
  span grows with the number of cameras. freemocap showed more than 22 ms for `person.preprocess`
  with four cameras at 1280x720.

The built-in pipeline runs the detector one time in 150 frames. The mean cost is small, but the
frame with a detection has this delay. On 2026-11-17, no fix was decided. A change of this code
must keep each output tensor equal.
