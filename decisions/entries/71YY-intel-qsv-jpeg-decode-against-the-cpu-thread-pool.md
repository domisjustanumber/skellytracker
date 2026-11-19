# 71YY — Intel QSV JPEG decode against the CPU thread pool

**Status:** evidence, 2026-11-19 (measurement of 2026-11-19; PR: pending).

## Decision

The question: can the JPEG decode of Intel Quick Sync Video (QSV) replace the CPU decode on a host
with no NVIDIA decoder? The user asked for it on 2026-11-19, with a measurement before the build.
The result: no. Nothing is built, and the JPEG decode on an EP that is not `cuda` or `trt-rtx`
stays on the CPU ([ADR-88ZB](88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)).

1. **The route.** PyAV 19.0.2 from PyPI holds FFmpeg 9.0.2 with the decoder `mjpeg_qsv`. With the
   option `async_depth=1`, one packet with one JPEG gives one frame. The GPU runtime comes with the
   Intel driver. The decode runs on the GPU through D3D11.
2. **The output is NV12.** The decoder gives NV12 (4:2:0) for a 4:2:0 JPEG and for a 4:2:2 JPEG.
   The host must convert it to BGR. The conversion that agrees with `cv2.imdecode` is a linear
   upsample of the chroma planes, then `cv2.COLOR_YCrCb2BGR` (BT.601, full range). The range tag of
   the frame says limited range, and it is wrong.
3. **Time, end to end to BGR in host memory.** Median wall time of one batch in ms, and the CPU time
   of the process for one batch in ms in parentheses. 4:2:2 JPEG, quality 90, 200 batches. "QSV
   decode" is the decode and the copy of NV12 to host memory, with no conversion.

   | Logical CPUs | Batch | CPU thread pool | QSV to BGR | QSV decode |
   |---|---|---|---|---|
   | 2 | 3 x 1280x720 | 6.2 (9) | 11.5 (19) | 4.8 |
   | 2 | 6 x 1920x1080 | 19.7 (36) | 29.9 (52) | 6.7 |
   | 4 | 3 x 1280x720 | 3.5 (10) | 8.6 (22) | 5.3 |
   | 4 | 6 x 1920x1080 | 13.3 (38) | 20.7 (62) | 6.8 |
   | 28 | 3 x 1280x720 | 3.5 (10) | 8.5 (43) | 4.8 |
   | 28 | 6 x 1920x1080 | 8.7 (42) | 20.0 (207) | 6.6 |

   QSV to BGR is slower and uses more CPU time in each cell. The 4:2:0 cells agree within 14 %.
   With one OpenCV thread (`cv2.setNumThreads(1)`), QSV to BGR at 28 CPUs is 16.7 to 17.5 ms and 60
   to 62 ms of CPU time for 6 frames of 1920x1080. It is still slower.
4. **The decode alone is cheap.** It uses 7 to 10 ms of CPU time for one batch in each cell. The
   conversion to BGR at the full frame size costs more CPU time than the full CPU decode.
5. **Pixels against `cv2.imdecode`, one 1280x720 image.** 4:2:0 JPEG: at most 3 `uint8` steps, mean
   0.087. 4:2:2 JPEG: at most 139 steps, mean 0.53, and 1.25 % of the values differ by more than 3.
   The cause is item 2: half of the vertical chroma resolution of a 4:2:2 JPEG is lost. USB cameras
   send 4:2:2 JPEG.
6. **Start cost.** The first decode of a decoder context takes 360 to 630 ms, and sometimes about
   870 ms. A batch of 6 frames needs 6 contexts.
7. **No hand-over in GPU memory.** The Python API of ONNX Runtime 1.30.0 wraps no D3D texture and
   no VA surface. The EP catalog gives an Intel GPU the EP `cpu`.

## Evidence

- Conditions: Windows 11, one Intel i7-14700K (8 P-cores with 2 threads each, 12 E-cores), Intel UHD
  770 with the driver 32.0.101.7088, Python 3.13, PyAV 19.0.2, `opencv-python-headless` 5.1.0, numpy
  2.5.5, in a temporary environment, not the environment of the package. The limit of 2 and 4
  logical CPUs is a process affinity on one thread each of 2 and 4 P-cores.
- The images are synthetic: a gradient with noise and coloured shapes, 175 KiB at 1280x720 and 275 to
  279 KiB at 1920x1080. No camera frame was used.
- Each cell has 10 warm-up batches and 200 timed batches. The CPU path uses a thread pool of
  `min(frames, CPUs)` workers. The QSV path uses one decoder context for each frame, each on its
  thread, and converts in the same pool.
- The script and the raw results are in
  [`71yy_qsv_jpeg_decode/`](../scripts/71yy_qsv_jpeg_decode/): `qsv_cores.py`, `result_<limit>.json`
  and `result_<limit>_cv1.json` (one OpenCV thread).
- Limits: one host; the clock rate and the other load of the host were not fixed (5 to 11 % load);
  the CPU time does not count the work of the GPU.
- Not measured: Linux; real camera frames; the Intel VPL library called directly, which can ask for
  YUY2 or RGB output (read from the Intel manual, not tested); a conversion on the GPU; a
  conversion after a resize to the model input size, which would be much smaller.
- Read, not measured: the PyAV wheel for Linux has libvpl and no VA-API, so `mjpeg_qsv` can fail
  there.

## Open work

See [open-work.md](../open-work.md).
