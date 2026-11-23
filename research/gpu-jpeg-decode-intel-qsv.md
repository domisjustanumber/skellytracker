# GPU JPEG decode on Intel (Quick Sync Video): research note

**Status:** research note, 2026-11-23. Not a decision. The decision entries that it cites hold the
measured facts.

This note helps a future worker to continue the work of
[ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md). The
open item is in [open-work.md](../decisions/open-work.md) ("Intel QSV JPEG decode").

Marks used in this note:

- **Measured:** this project measured it. The note names the decision entry.
- **Documented:** a vendor page says it. The note gives the URL.
- **Inferred:** the writer derived it from a documented fact. It is not a fact.
- **Not found:** the pages that the writer read do not say it. The note names the pages.

## 1. Status

- The measurement was made on 2026-11-19. QSV JPEG decode gave no gain against the CPU thread pool
  on any cell that was measured.
- Nothing is built. The JPEG decode on an EP that is not `cuda` or `trt-rtx` stays on the CPU
  ([ADR-88ZB](../decisions/entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)).
- Two cases could reopen the work. No run has tested them (section 4).

## 2. What was measured, and how

Source: [ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md).
All numbers in this section are **measured**.

**Route.** PyAV 19.0.2 from PyPI holds FFmpeg 9.0.2 with the decoder `mjpeg_qsv`. The option
`async_depth=1` gives one frame for one packet. The decode runs on the GPU through D3D11. The run
used one decoder context for each frame, each on its own thread.

**Conditions.** Windows 11, Core i7-14700K, Intel UHD 770 (driver 32.0.101.7088), Python 3.13,
`opencv-python-headless` 5.1.0, in a temporary environment. The limit of 2 and 4 logical CPUs is a
process affinity. The images are synthetic (a gradient with noise and coloured shapes), 4:2:2 JPEG,
quality 90. Each cell has 10 warm-up batches and 200 timed batches. No camera frame was used.

**Script folder:** [`71yy_qsv_jpeg_decode/`](../decisions/scripts/71yy_qsv_jpeg_decode/). It holds
`qsv_cores.py` and the raw `result_*.json` files (`_cv1` files: one OpenCV thread).

**Time, end to end to BGR in host memory.** Median wall time of one batch in ms. The CPU time of
the process for one batch is in parentheses. "QSV decode" is the decode and the copy of NV12 to
host memory, with no conversion.

| Logical CPUs | Batch | CPU thread pool | QSV to BGR | QSV decode |
|---|---|---|---|---|
| 2 | 3 x 1280x720 | 6.2 (9) | 11.5 (19) | 4.8 |
| 2 | 6 x 1920x1080 | 19.7 (36) | 29.9 (52) | 6.7 |
| 4 | 3 x 1280x720 | 3.5 (10) | 8.6 (22) | 5.3 |
| 4 | 6 x 1920x1080 | 13.3 (38) | 20.7 (62) | 6.8 |
| 28 | 3 x 1280x720 | 3.5 (10) | 8.5 (43) | 4.8 |
| 28 | 6 x 1920x1080 | 8.7 (42) | 20.0 (207) | 6.6 |

Other measured facts of
[ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md):

- With one OpenCV thread at 28 CPUs, QSV to BGR takes 16.7 to 17.5 ms and 60 to 62 ms of CPU time
  for 6 frames of 1920x1080. It is still slower than the CPU pool.
- The decode alone uses 7 to 10 ms of CPU time for one batch. The conversion to BGR at the full
  frame size costs more CPU time than the full CPU decode.
- Pixels against `cv2.imdecode` (one 1280x720 image): a 4:2:0 JPEG differs by at most 3 `uint8`
  steps (mean 0.087). A 4:2:2 JPEG differs by at most 139 steps (mean 0.53). 1.25 % of the values
  differ by more than 3.
- The first decode of a decoder context takes 360 to 630 ms, and sometimes about 870 ms.
- Not measured: Linux, real camera frames, the Intel VPL library called directly, a conversion on
  the GPU, a conversion after a resize to the model input size.

For comparison, the NVIDIA numbers of
[ADR-58F5](../decisions/entries/58F5-native-jpeg-numbers-on-the-pinned-versions.md) (RTX 3070,
measured):

| Batch | CPU pool | CPU pool plus upload | nvJPEG |
|---|---|---|---|
| 3 x 1280x720 | 3.64 ms | 5.38 ms | 2.44 ms |
| 6 x 1920x1080 | 7.98 ms | 14.16 ms | 3.11 ms |

The NVIDIA decoder is the shape that a new decoder would copy:
[`nvidia.py`](../skellytracker/core/decode/nvidia.py) and
[`cpu.py`](../skellytracker/core/decode/cpu.py).

## 3. Why it lost

All four causes are from
[ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md)
(measured), except where the text says "inferred".

1. **NV12 output and the host conversion.** `mjpeg_qsv` gives NV12 (4:2:0) for a 4:2:0 JPEG and
   for a 4:2:2 JPEG. The host must convert NV12 to BGR at the full frame size. That step costs
   more CPU time than the whole CPU decode.
2. **No hand-over in GPU memory.** The Python API of ONNX Runtime 1.30.0 wraps no D3D texture and
   no VA surface. The frame must come back to host memory. The EP catalog gives an Intel GPU the
   EP `cpu`, so no GPU model session waits for the frame.
3. **Start cost.** A decoder context needs 360 to 630 ms for its first decode. A batch of 6 frames
   needs 6 contexts.
4. **4:2:2 chroma loss.** NV12 has half of the vertical chroma resolution. A 4:2:2 JPEG loses it.
   USB cameras send 4:2:2 JPEG. The result differs from `cv2.imdecode` by up to 139 steps.

The lesson in short: a GPU decode pays only if the decoded frame is in a format that the model path
can use without an expensive host conversion, and if the frame can stay in GPU memory and reach the
model EP with no copy to the host.

## 4. The two cases that could reopen it

The open item says: no run tested an NV12 preprocess that converts after the resize to the model
input size, and no run tested 4:2:2 output from the Intel VPL library.

### 4.1 Case A: an NV12 preprocess that converts after the resize

**Idea (inferred).** Keep the NV12 output. Resize the Y plane and the UV plane to the model input
size first. Convert to the model colour layout after that. The model input is much smaller than
the camera frame, so the conversion costs less. Example: 1920x1080 is 2.07 million pixels. A model
input of 640x640 is 0.41 million pixels. The resize on NV12 is the cost to measure.

**What is needed.**

- A resize that works on two planes. Options: OpenCV on the two planes on the CPU (inferred:
  the chroma plane has two interleaved channels, so it resizes as a two-channel image); or an
  ONNX preprocess graph that takes NV12.
- The preprocess graph of the package takes a BGR `uint8` frame (the turn graph in
  [`nvidia.py`](../skellytracker/core/decode/nvidia.py) has the input `(H, W, 3)`). An NV12
  version is a new graph. No fact about the cost of such a graph on `openvino` or `directml`
  was found.
- The frame must still leave the GPU as NV12 (12 bits per pixel, so half of the bytes of BGR).
  This project measured the copy of NV12 to host memory as part of "QSV decode" (4.8 to 6.8 ms in
  the table above). The copy is included in that number.
- The accuracy limit stays: chroma upsampling before the colour conversion decides the pixel
  difference. A resize first changes the pixel result against `cv2.imdecode`. The worker must
  decide, with the model owner, what difference the model accepts. Not measured.
- The QSV decode time alone (4.8 to 6.8 ms) is already longer than the full CPU pool at 4 CPUs for
  the small batch (3.5 ms), and equal to about half of it for the large batch (13.3 ms). Inferred:
  Case A can win only on the large batch, and only if the NV12 resize is cheap.

**Sources:** [ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md)
for the numbers. No vendor page is needed for this case: it needs only a measurement.

### 4.2 Case B: 4:2:2 or RGB output from the Intel VPL library

**Question 1. Does Intel VPL JPEG decode give YUY2 (4:2:2) or RGB4 output, and on which hardware
generations?**

- **Documented (with a caveat).** The oneVPL developer reference for Intel hardware, page
  "Features and Formats", has MJPEG decode rows. As read by the writer (through a web fetch tool,
  so the worker must read the page again):
  - Discrete Intel GPUs (Iris Xe MAX, Arc A-Series): rows "4:2:0, 8-bit to IMC3",
    "4:2:2, 8-bit to 4:2:2H", "4:4:4, 8-bit to RGBP / BGRP",
    "4:2:0 / 4:2:2H (inter) to YUY2 / UYVY", "4:2:0 / 4:2:2H / 4:2:2V (inter) to NV12" and
    "400 / 4:2:0 / 4:2:2H / 4:4:4 / RGB / BGR (inter) to A8R8G8B8". All are marked as supported up
    to 16k.
  - 6th to 10th Gen Core: the same rows, with the A8R8G8B8 row.
  - 11th to 13th Gen Core: the rows for YUY2 and NV12, and no A8R8G8B8 row.
  - Intel Atom x5 and x7: the A8R8G8B8 row is blank.
  - Source: https://www.intel.com/content/www/us/en/docs/onevpl/developer-reference-media-intel-hardware/1-1/features-and-formats.html
- **Not found.** The meaning of "(inter)" in these rows. The writer did not confirm it.
- **Not found.** A row for the 14th Gen Core or for the UHD 770 of the test system. The version of the
  page that the writer read is 1.1, and it can be older than that hardware. The worker must query
  the driver (see the plan in section 5, step 1).
- **Documented, old.** The Media SDK JPEG manual says the decoder supports three output colour
  formats: NV12, YUY2 and RGB32. The output format comes from the FourCC and ChromaFormat fields of
  `mfxFrameInfo`. Source: https://github.com/sharpshooter777/MediaSDK/blob/master/doc/mediasdkjpeg-man.md
  (a copy of the manual in a fork; the writer did not find the manual on an Intel page).
- **Mixed reports.** One Intel forum reply says that `MFX_FOURCC_RGB4` with
  `MFX_CHROMAFORMAT_YUV444` gives RGB32 output. Another thread says a decode with RGB4 still gave
  NV12, and that VPP is needed to convert. One old report says YUY2 and RGB4 failed on an old GPU.
  Sources: https://community.intel.com/t5/Media-Intel-oneAPI-Video/Media-SDK-decode-MJPEG-to-RGB4/td-p/1041290
  and https://community.intel.com/t5/Media-Intel-oneAPI-Video/Problems-understanding-Decode-VPP-workflow-for-JPEG-gt-RGB4/m-p/1071050
  and https://community.intel.com/t5/Media-Intel-Video-Processing/mjpeg-decoding-to-system-memory/m-p/1071079/highlight/true
  These are forum posts, not vendor statements.
- **Not found.** A statement in the libvpl API reference about the JPEG fields (`JPEGChromaFormat`,
  `JPEGColorFormat`). The writer read these pages and the fields were not on them:
  https://intel.github.io/libvpl/latest/API_ref/VPL_structs_decode_vpp.html and
  https://intel.github.io/libvpl/latest/API_ref/VPL_structs_decode.html. The structure
  `mfxInfoMFX` is probably on the "Cross-component Structures" page (inferred, not read).
- **Inferred.** A 4:2:2 YUY2 frame keeps the full vertical chroma. If the driver gives YUY2 for a
  4:2:2 JPEG, the chroma loss of section 3 goes away. The host (or GPU) conversion from YUY2 to BGR
  still costs time. YUY2 is 16 bits per pixel, so the copy to the host is 33 % larger than NV12.

**Question 2. Does a Python binding of Intel VPL exist?**

- **Not found** on PyPI or in an Intel repository. A Fedora packaging file says the Python
  bindings were removed upstream in 2023.0.0. Source (secondary):
  https://packages.fedoraproject.org/pkgs/oneVPL/python3-oneVPL and
  https://src.fedoraproject.org/rpms/oneVPL/blob/8edd0ae70705d47b427ebca9cb6b3a49d54b8d34/f/oneVPL.spec
- The repository https://github.com/intel/libvpl says its tools moved to
  https://github.com/intel/libvpl-tools. The writer did not read that repository.
- **Inferred.** The routes are: PyAV (FFmpeg `mjpeg_qsv`, no control of the output format that
  the writer could confirm); `ctypes` or `cffi` on the C API of libvpl (the worker writes the
  binding); or a small C extension. The `ctypes` route is the only one that can ask for YUY2.

**Question 3. Can the OpenVINO GPU plugin take a VA surface or a D3D11 texture as a remote tensor?
Is it reachable from Python?**

- **Documented, C++.** The OpenVINO GPU remote tensor API has `ov::intel_gpu::ocl::VAContext`
  (header `va.hpp`, Linux) and `ov::intel_gpu::ocl::D3DContext` (header `dx.hpp`, Windows), with
  helpers for NV12 surfaces. Sources:
  https://docs.openvino.ai/2022.2/namespaceInferenceEngine_1_1gpu.html and the class pages
  https://docs.openvino.ai/2026/api/c_cpp_api/classov_1_1intel__gpu_1_1ocl_1_1_v_a_context.html
  (read through search results; the writer could not read the page bodies).
- **Documented, Python, Linux.** The OpenVINO Python API reference lists `openvino.RemoteContext`,
  `openvino.RemoteTensor`, `openvino.VAContext` and `openvino.VASurfaceTensor`.
  `VAContext.create_tensor_nv12` takes a height, a width and an NV12 `VASurfaceID` and returns two
  `VASurfaceTensor` objects, one for each plane. The context needs a valid `VADisplay`. Source:
  https://docs.openvino.ai/2026/api/ie_python_api/_autosummary/openvino.VAContext.html (the page
  body could not be fetched by the writer; the text is from search results. The worker must read
  it again.)
- **Not found.** A Python class for a D3D11 context or an NV12 D3D11 texture. The writer found only
  the C++ `D3DContext`. The test system of
  [ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md) is
  Windows, and `mjpeg_qsv` there decodes through D3D11. So the Python remote tensor route
  that the writer found is for Linux (VA-API) only.
- **Not found.** The "Remote Tensor API of GPU Plugin" page body for the current release. The
  writer fetched
  https://docs.openvino.ai/2025/openvino-workflow/running-inference/inference-devices-and-modes/gpu-device/remote-tensor-api-gpu-plugin.html
  but the body was beyond the part that the tool returned. The worker must read this page.
- **Project fact.** The EP catalog marks `openvino` as `reserved`: "OpenVINO is deferred: discrete
  Intel GPUs only", with a CI-only test pack
  ([`ep_catalog.yaml`](../skellytracker/core/eps/ep_catalog.yaml)). A model session on an Intel
  iGPU is thus not offered today. A QSV route needs a decision about that first.

**Question 4. Can the OpenVINO EP or the DirectML EP of ONNX Runtime take such a surface from the
Python API?**

- **OpenVINO EP: not found for Python.** The OpenVINO EP page shows a `context` option only in the
  C and C++ examples (`options[context] = "0x123456ff"`). The Python provider options in the
  table are `device_type`, `load_config` and others, and `context` is not among them. Source:
  https://onnxruntime.ai/docs/execution-providers/OpenVINO-ExecutionProvider.html
  (read by a fetch tool, which gave no I/O buffer section). A forum answer says OpenVINO remote
  tensors do not pass into ONNX Runtime: https://community.intel.com/t5/Intel-Distribution-of-OpenVINO/Is-it-possible-to-use-onnxruntime-in-openvino-pipeline-with/m-p/1532403
  (informal, may be old).
- **DirectML EP: documented for numpy upload only.** The device tensor page shows
  `ort.OrtValue.ortvalue_from_numpy(array, "dml")`, `bind_ortvalue_input`, `bind_output(name,
  "dml")` and `run_with_iobinding`. It shows no way to wrap an existing D3D resource from Python.
  Source: https://onnxruntime.ai/docs/performance/device-tensor.html
- **Documented.** `IOBinding.bind_input(name, device_type, device_id, element_type, shape,
  buffer_ptr)` takes a raw device pointer. The `device_type` examples are "cpu, cuda, cann". Source:
  https://onnxruntime.ai/docs/api/python/api_summary.html
- **Measured.** [ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md)
  item 7: the Python API of ONNX Runtime 1.30.0 wraps no D3D texture and no VA surface.
- **Inferred.** A D3D11 texture is not a `buffer_ptr` that a DML session can read. A D3D12 resource
  that DirectML owns is a different object. No documented bridge was found.

**Summary of case B.** Only the first link (YUY2 or RGB output from VPL) is plausible from the
documents. No Python binding exists. The hand-over to a model session in GPU memory is not
reachable from Python on Windows, from what the writer found. On Linux, the OpenVINO Python API
has VA surface remote tensors, but it is a separate OpenVINO runtime, not the ONNX Runtime EP that
the package uses.

## 5. Next-step plan

Do a measurement before any build. Use the method of
[ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md).

1. **Ask the driver (no timing).** With `ctypes` on libvpl, call `MFXVideoDECODE_Query` for the
   MJPEG decoder with the FourCC `YUY2` and with `RGB4`, on the target system. Record the answer.
   If neither works, stop: case B is closed for that hardware. Also record whether the driver
   accepts a 4:2:2 JPEG at all.
2. **Check the idle-gap effect (section 6).** Before any model session on the iGPU, run the check
   in section 6.
3. **Build a measurement script** in `scripts/` of a new decision entry (not in `tools/`). Use the
   same inputs as ADR-71YY: batches of 3 x 1280x720 and 6 x 1920x1080, 4:2:2 JPEG, quality 90,
   200 timed batches after 10 warm-up batches, the CPU thread pool of `min(frames, CPUs)` workers,
   limits of 2, 4 and all logical CPUs. Use synthetic images (never a camera frame).
4. **Measure end to end to the model input.** The end is the model input tensor (for example
   `float32` NCHW at the model size), not BGR at full size. Time both paths:
   - the CPU pool: decode, resize, normalise;
   - the VPL route: decode (YUY2 or NV12), copy to the host, resize, convert, normalise.
   Record the median, the p95 and the maximum of the wall time, the CPU time of the process, and
   the pixel agreement of the model input against the CPU path (largest step, mean, share above 3).
5. **Record the start cost** of the first decode of a context, and test one context for a batch
   (VPL can decode on one session in sequence) against one context for each frame.
6. **Apply the stop rule.**

**Stop rule (a proposal; the user decides the numbers).** Do not build if any of these is true:

- the VPL route is not faster than the CPU pool in the median at 4 logical CPUs on both batches;
- the VPL route uses more CPU time of the process than the CPU pool;
- the pixel difference of the 4:2:2 JPEG against the CPU path is larger than that of the NV12 route
  of ADR-71YY (up to 139 steps) with no better result;
- the start cost of a context is above 100 ms with no way to hide it;
- the frame cannot reach the model session without a host copy, and the host copy alone (decode plus
  copy, with no conversion) is already slower than the full CPU pool. For reference, ADR-71YY gives
  4.8 to 6.8 ms for this value, against 3.5 ms (3 x 1280x720) and 13.3 ms (6 x 1920x1080) for the
  CPU pool at 4 CPUs.

Record the result as an evidence entry, win or lose. A negative result closes the open item.

## 6. A related fact measured on 2026-11-23 (OpenVINO EP on the iGPU)

**Measured**
([ADR-4JFP](../decisions/entries/4JFP-preprocess-paths-timing.md) item 8). On a
Core i7-14700K with a UHD 770, the OpenVINO EP on that iGPU ran a preprocess graph in 5.5 ms when
the calls came back to back. After an idle gap of 250 ms, the call took about 460 ms (28 of 30
calls). The cause is unknown.

Any QSV route that feeds a model session on an iGPU must check for this effect, for these reasons
(inferred):

- A camera delivers frames at intervals. A gap of 250 ms or more is normal in a live run with a low
  frame rate or a pause.
- A fast decode with a 460 ms model call after each pause is worse than the CPU decode.

How to check: run the real call pattern. Time each call after a gap of 0, 50, 100, 250 and 500 ms,
at least 30 calls for each gap. Record the median and the maximum. Do this on the decode session and
on the model session. A result such as 28 of 30 slow calls means "do not build".

## Sources

All URLs were read on 2026-11-23, except where the text says that the page body was not read. A tool
fetched each page, and a summary was returned. Thus a text in quotation marks can differ from the
page, and the worker must read each page again before a decision.

Project entries (relative links above):
[ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md),
[ADR-58F5](../decisions/entries/58F5-native-jpeg-numbers-on-the-pinned-versions.md),
[ADR-88ZB](../decisions/entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md).

- https://www.intel.com/content/www/us/en/docs/onevpl/developer-reference-media-intel-hardware/1-1/features-and-formats.html
- https://intel.github.io/libvpl/latest/API_ref/VPL_structs_decode_vpp.html (no JPEG fields found)
- https://intel.github.io/libvpl/latest/API_ref/VPL_structs_decode.html (no JPEG fields found)
- https://github.com/sharpshooter777/MediaSDK/blob/master/doc/mediasdkjpeg-man.md
- https://community.intel.com/t5/Media-Intel-oneAPI-Video/Media-SDK-decode-MJPEG-to-RGB4/td-p/1041290
- https://community.intel.com/t5/Media-Intel-oneAPI-Video/Problems-understanding-Decode-VPP-workflow-for-JPEG-gt-RGB4/m-p/1071050
- https://community.intel.com/t5/Media-Intel-Video-Processing/mjpeg-decoding-to-system-memory/m-p/1071079/highlight/true
- https://packages.fedoraproject.org/pkgs/oneVPL/python3-oneVPL
- https://src.fedoraproject.org/rpms/oneVPL/blob/8edd0ae70705d47b427ebca9cb6b3a49d54b8d34/f/oneVPL.spec
- https://github.com/intel/libvpl
- https://docs.openvino.ai/2025/openvino-workflow/running-inference/inference-devices-and-modes/gpu-device/remote-tensor-api-gpu-plugin.html (body not read)
- https://docs.openvino.ai/2022.2/namespaceInferenceEngine_1_1gpu.html
- https://docs.openvino.ai/2026/api/c_cpp_api/classov_1_1intel__gpu_1_1ocl_1_1_v_a_context.html
- https://docs.openvino.ai/2026/api/ie_python_api/_autosummary/openvino.VAContext.html (body not read)
- https://onnxruntime.ai/docs/execution-providers/OpenVINO-ExecutionProvider.html
- https://community.intel.com/t5/Intel-Distribution-of-OpenVINO/Is-it-possible-to-use-onnxruntime-in-openvino-pipeline-with/m-p/1532403
- https://onnxruntime.ai/docs/performance/device-tensor.html
- https://onnxruntime.ai/docs/api/python/api_summary.html
