# GPU JPEG decode on AMD (rocJPEG): research note

**Status:** research note, 2026-11-23. Not a decision. The decision entries that it cites hold the
measured facts.

This note helps a future worker to measure rocJPEG on an AMD Linux system. The open item is in
[open-work.md](../decisions/open-work.md) ("AMD JPEG decode with rocJPEG (Linux)").

Marks used in this note:

- **Measured:** this project measured it. The note names the decision entry.
- **Documented:** a vendor page says it. The note gives the URL.
- **Inferred:** the writer derived it from a documented fact. It is not a fact.
- **Not found:** the pages that the writer read do not say it. The note names the pages.

## 1. Status

- Nothing is measured. The project has no AMD hardware.
- The item was added to open work on 2026-11-23.
- Nothing is built. On an EP that is not `cuda` or `trt-rtx`, the JPEG decode runs on the CPU
  ([ADR-88ZB](../decisions/entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)).

What the project measured on NVIDIA
([ADR-58F5](../decisions/entries/58F5-native-jpeg-numbers-on-the-pinned-versions.md), RTX 3070):

| Batch | CPU pool | CPU pool plus upload | nvJPEG |
|---|---|---|---|
| 3 x 1280x720 | 3.64 ms | 5.38 ms | 2.44 ms |
| 6 x 1920x1080 | 7.98 ms | 14.16 ms | 3.11 ms |

The lesson of the Intel test
([ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md)): a GPU
decode pays only if (a) the decoded frame is in a format that the model path can use without an
expensive host conversion, and (b) the frame can stay in GPU memory and reach the EP of the model
with no copy to the host. Section 4 shows that (b) is the open question for rocJPEG.

## 2. What rocJPEG is

- **Documented.** "rocJPEG is a library for accessing the JPEG decoding hardware (media engines, or
  VCNs) on AMD GPUs. It provides APIs and samples, and it supports interoperability with other GPU
  compute engines through VA-API and HIP. It is delivered as part of TheRock, and its source code is
  in the ROCm/rocm-systems repository." Source: https://rocm.docs.amd.com/projects/rocJPEG/en/latest/
- **Documented.** The README calls it "a high performance JPEG decode SDK for AMD GPUs". It lists
  libva and VA-API drivers, libdrm (amdgpu) and the HIP runtime as required components. Source:
  https://github.com/ROCm/rocm-systems/tree/develop/projects/rocjpeg
- **Inferred.** rocJPEG decodes through the VA-API driver of the AMD GPU (Mesa `radeonsi` or
  similar) and then moves or converts the surface with HIP. This follows from the VA-API
  requirement and from "interoperability ... through VA-API and HIP". The writer did not read the
  source to confirm the path.
- **Documented.** Licence: MIT (README badge and LICENSE file). Same source as above.
- **Documented.** The documentation pages that the writer read: the home page, the install page,
  "Use rocJPEG", "Decode a JPEG stream with rocJPEG", the API reference, "rocJPEG subsampling and
  hardware capabilities", and the CHANGELOG.

## 3. Answers to the questions

### 3.1 Supported GPUs

**Documented** table (columns: GPU architecture, VCN generation, JPEG cores, maximum size in
pixels). Source:
https://rocm.docs.amd.com/projects/rocJPEG/en/latest/reference/rocjpeg-formats-and-architectures.html

| GPU architecture | VCN generation | JPEG cores | Maximum width, height |
|---|---|---|---|
| gfx908 (MI1xx) | VCN 2.5.0 | 2 | 4096, 4096 |
| gfx90a (MI2xx) | VCN 2.6.0 | 4 | 4096, 4096 |
| gfx942 (MI300A) | VCN 3.0 | 24 | 16384, 16384 |
| gfx942 (MI300X) | VCN 3.0 | 32 | 16384, 16384 |
| gfx1030, gfx1031, gfx1032 (Navi2x) | VCN 3.x | 1 | 16384, 16384 |
| gfx1100, gfx1101, gfx1102 (Navi3x) | VCN 4.0 | 1 | 16384, 16384 |

- **Documented.** The README requires a GPU of `gfx908` or newer ("AMD Radeon and AMD Instinct
  accelerators"). On partitioned GPUs, the number of cores is that of the selected compute
  partition. The page recommends `rocJpegGetDecoderCaps()` for a query at run time.
- **Documented, CHANGELOG.** Support for `gfx1150`, `gfx1152` and `gfx1153` came in rocJPEG 1.5.0
  (ROCm 7.13). `gfx1250` came in 1.6.0 (ROCm 7.14.1). Source:
  https://github.com/ROCm/rocm-systems/blob/develop/projects/rocjpeg/CHANGELOG.md
- **Consumer cards.** Radeon RX 6000 (Navi2x, gfx103x) and RX 7000 (Navi3x, gfx110x) are in the table
  (documented). The table says "1" JPEG core for both.
- **Ryzen AI APUs.** `gfx1150`, `gfx1152`, `gfx1153` are in the CHANGELOG. These ids appear in the
  list of Ryzen AI processors of the ONNX Runtime page of AMD (section 3.7). The JPEG core count
  of those APUs is **not found**. Older APUs: **not found**.
- **Radeon RX 9000 (gfx1200, gfx1201).** **Not found** in the hardware table, in the README or in
  the CHANGELOG entries that the writer read. The ONNX Runtime page of AMD lists `gfx1200` and
  `gfx1201` as supported Radeon GPUs for MIGraphX (documented), but that page is not about
  rocJPEG. **Guess:** the VCN of these GPUs probably has a JPEG engine, but this is not a fact. The
  worker must query `rocJpegGetDecoderCaps()` or ask AMD.
- The table is for the "latest" docs (version 1.13.0, per the install page). The CHANGELOG gives
  later versions (1.14.0).

### 3.2 Supported OS

- **Documented.** The install page says "Applies to Linux" and does not mention Windows. The README
  lists Linux only, tested on Ubuntu 22.04 and 24.04. The CHANGELOG has no Windows entry. Sources:
  https://rocm.docs.amd.com/projects/rocJPEG/en/latest/install/rocjpeg-install.html and the README
  of the source repository above.
- **Documented.** The install page does not list OS versions: it points to the ROCm Core SDK
  release notes.
- **Inferred.** Windows is not supported. The writer read no statement that says "not supported on
  Windows". The dependency on VA-API and libdrm (Linux interfaces) makes a Windows port unlikely.

### 3.3 Input limits

- **Documented.** "The VCN JPEG decoder supports only baseline JPEG." Source:
  https://rocm.docs.amd.com/projects/rocJPEG/en/latest/how-to/using-rocjpeg.html
- **Documented.** Chroma subsampling: 4:4:4, 4:4:0, 4:2:2, 4:2:0 and 4:0:0. The API enum also has
  `ROCJPEG_CSS_411` and `ROCJPEG_CSS_UNKNOWN`. "A chroma subsampling is reported as supported only
  if the VA-API driver supports its native surface format." Sources: the "subsampling and
  hardware capabilities" page, the "Use rocJPEG" page and
  https://rocm.docs.amd.com/projects/rocJPEG/en/latest/reference/rocJPEG-api-reference.html
- **Documented.** Maximum size: 4096 x 4096 on gfx908 and gfx90a, 16384 x 16384 on the others of
  the table. Dimensions of 0 or above 65500 are rejected (CHANGELOG, 1.7.0).
- **Documented.** The coding process enum has `BASELINE`, `EXTENDED`, `PROGRESSIVE` and `LOSSLESS`,
  but the page says that the hardware supports baseline only.
- **Inferred.** USB camera MJPEG frames are baseline 4:2:2 (a common case), so they fit. The
  worker must test real camera frames. Some cameras send MJPEG with no DHT (Huffman table) segment;
  [`nvidia.py`](../skellytracker/core/decode/nvidia.py) already refuses such a buffer for nvJPEG.
  How rocJPEG reacts is **not found**.

### 3.4 Output formats and where the colour conversion runs

**Documented** (page "Decode a JPEG stream with rocJPEG",
https://rocm.docs.amd.com/projects/rocJPEG/en/latest/how-to/rocjpeg-decoding-a-jpeg-stream.html):

| `RocJpegOutputFormat` | Meaning |
|---|---|
| `ROCJPEG_OUTPUT_NATIVE` | Unchanged YUV from the VCN decoder |
| `ROCJPEG_OUTPUT_YUV_PLANAR` | YUV planar |
| `ROCJPEG_OUTPUT_Y` | Y component only |
| `ROCJPEG_OUTPUT_RGB` | Interleaved RGB |
| `ROCJPEG_OUTPUT_RGB_PLANAR` | Planar RGB |

Layout of `ROCJPEG_OUTPUT_NATIVE` by chroma subsampling (documented, same page):

| Subsampling | Native layout |
|---|---|
| 4:4:4, 4:4:0 | Y, U, V in channels 0, 1, 2 |
| 4:2:2 | Packed YUYV in channel 0 (pitch is `width * 2`) |
| 4:2:0 | Y in channel 0, interleaved UV in channel 1 (NV12 style) |
| 4:0:0 | Y in channel 0 |

- **Inferred.** Native output for a 4:2:2 JPEG is packed YUYV with full vertical chroma. It does not
  have the 4:2:2 chroma loss that NV12 gave in
  [ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md). The
  RGB output also does not need the host. Both are guesses until a run compares the pixels against
  `cv2.imdecode`.
- **Documented.** `RocJpegSurfaceFormat` has `YUV444P`, `YUV440P`, `YUYV`, `NV12` and `Y8` (1.13.0
  CHANGELOG: the enum describes the native layout).
- **Documented.** RGB pitch is `width * 3`. The component order (RGB or BGR) is **not found**. The
  package needs BGR for `cv2` parity ([`cpu.py`](../skellytracker/core/decode/cpu.py) gives BGR).
  The worker must check the order and the colour matrix (BT.601 full range is what
  `cv2.imdecode` uses, per ADR-71YY).
- **Where the conversion runs.** Documented in the CHANGELOG: rocJPEG 1.13.0 "added HIP color
  conversion kernels to the batched path for better performance". So RGB conversion in the batched
  path runs on the GPU (documented). For the single-image path: **not found**. The "Use rocJPEG"
  page says nothing about a HIP kernel.
- **Documented.** The decode parameters hold `output_format`, a `crop_rectangle`, and a
  `target_dimension` that is "future use" (resize in the decoder is not available today). A
  crop is documented; a resize is not. Source: the "Decode a JPEG stream" page and the API
  reference page.
- **Documented, bug note.** 1.14.0 fixed a write past the end of the buffer for RGB, RGB planar,
  Y and YUV planar output when the width is not a multiple of 8 or the height is odd. Use rocJPEG
  1.14.0 or newer, or test 1280x720 and 1920x1080 only (both are multiples of 8).

### 3.5 Batch decode API

**Documented** (API reference page):

- `rocJpegDecode`, `rocJpegDecodeAsync`, `rocJpegDecodeSync` for one image.
- `rocJpegDecodeBatched(handle, jpeg_stream_handles, batch_size, decode_params, destinations)`,
  `rocJpegDecodeBatchedAsync` and `rocJpegDecodeBatchedSync(handle, destinations, batch_size)`.
  The async and sync batched functions came in 1.10.0 (CHANGELOG).
- The "Decode a JPEG stream" page says that batched decode is more efficient than repeated single
  calls on a GPU with several JPEG cores. It recommends a batch size that is a multiple of the core
  count.
- A consumer card has one JPEG core (3.1), so the batch gain on such a card is **inferred** to be
  small. A batch of 3 or 6 frames is not a multiple of 1 in a useful sense: the frames queue on
  one core.
- Backends: `ROCJPEG_BACKEND_HARDWARE` and `ROCJPEG_BACKEND_HYBRID` exist in the enum. The "Use
  rocJPEG" page documents only the hardware backend. What the hybrid backend does is **not found**.
- The caller creates one handle with `rocJpegCreate(backend, device_id, &handle)`, and a stream
  handle for each image with `rocJpegStreamCreate`, then `rocJpegStreamParse(data, length,
  stream_handle)`.

### 3.6 Does the output stay in GPU memory, and how does another library read it?

- **Documented.** "Memory needs to be allocated for each channel of the destination image." The
  caller allocates each channel of each `RocJpegImage` with `hipMalloc()` and frees it with
  `hipFree()`. `RocJpegImage` holds `uint8_t *channel[...]` and `uint32_t pitch[...]`. Source: the
  "Decode a JPEG stream" page.
- **Inferred.** The output is thus a HIP device pointer (plus a pitch in bytes) in the memory of the
  GPU. The frame never goes to the host unless the caller copies it. The page does not use the
  words "device pointer", but `hipMalloc` memory is device memory.
- **How another library reads it.** Any library that accepts a HIP device pointer, a pitch, a shape
  and a type can read it. Whether ONNX Runtime can is the question of section 4.
- A DLPack route (inferred): a Python object that exports `__dlpack__` with the device type
  `kDLROCM` could wrap the pointer. `OrtValue.from_dlpack` exists (section 4), but the writer found
  no statement that it accepts a ROCm device.

### 3.7 Python bindings

- **Documented.** rocPyDecode 0.8.0 contains `rocPyJpegDecode`, "Python bindings for the rocJPEG
  APIs". It installs with rocPyDecode when rocJPEG is already on the system. Sources:
  https://rocm.docs.amd.com/projects/rocPyDecode/en/latest/index.html and
  https://rocm.docs.amd.com/projects/rocPyDecode/en/latest/reference/rocPyJPEGDecode-api.html
- **Documented, API.** `initialize_hip()` (must come first, device 0 by default), `decoder()`,
  `decoder().set_output_image_format()` (`ROCJPEG_OUTPUT_RGB` or `ROCJPEG_OUTPUT_RGB_PLANAR`),
  `decoder().read` and `decoder().decode`. Input: a file path, a memory buffer or a NumPy array,
  one or a batch (a batch needs a batch size). The result: one image tensor, or a list of them. If
  one image of a batch fails, no image comes back.
- **Not found.** Whether the returned tensors live in device memory or host memory. The page does
  not say. DLPack, `__cuda_array_interface__` or another interop protocol: not mentioned. Ownership
  and lifetime of the memory: not described. Output formats other than RGB and RGB planar (so no
  native YUYV, no BGR): not offered by the Python binding, as the page reads.
- **Not found.** The install method of rocPyDecode (pip or apt). The page links to a prerequisites
  page, an install page, a CMake page and a "create a wheel" how-to. The writer did not read them.
  A wheel on PyPI or on the AMD index: not found.
- **Not found.** The licence of rocPyDecode (the page links to the ROCm licence page).
- **Documented.** The page says the documentation for 7.13.0 is a technology preview, and that
  production use should use the ROCm 7.2.4 documentation.
- **Inferred.** If the Python binding returns host tensors, it adds a device-to-host copy that
  defeats the purpose. The worker can call the C library with `ctypes` instead. The API is small
  (about 10 functions).

### 3.8 Installation

- **Documented.** On Linux, rocJPEG is in the ROCm Core SDK. Install the `amdrocm-core-sdk` meta
  package, or only rocJPEG: `amdrocm-jpeg` (runtime, includes the ROCm runtime and system
  dependencies) and `amdrocm-jpeg-dev` on Debian and Ubuntu (`-devel` on RHEL and SLES). Nightly
  builds come through TheRock (no command given). Source:
  https://rocm.docs.amd.com/projects/rocJPEG/en/latest/install/rocjpeg-install.html
- **Documented.** The install page does not mention pip. The README says rocJPEG is built and
  installed as part of TheRock, "tested with version 7.12 or later". The installed layout is
  `/opt/rocm/lib` and `/opt/rocm/include/rocjpeg`.
- **Not found.** A Python wheel of rocJPEG itself (the C library) on `repo.amd.com` or
  `stable.repo.amd.com`. The writer did not find a listing of these indexes.
- **Documented, for comparison.** The `migraphx` EP wheels of the project come from
  `https://stable.repo.amd.com/rocm/onnxruntime/whl-next/` as
  `onnxruntime-ep-migraphx==1.0.0+rocm10.0.0`, `+rocm10.1.0` and `+rocm10.2.0`. They depend on
  `migraphx-libs` from the MIGraphX pip repository. Python 3.12 (also 3.14 for ROCm 10.0.0).
  Source: https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/inference/onnxruntime.html
- **Inferred.** The system needs the ROCm packages of the same release as the `migraphx` wheel.
  The `amdrocm-jpeg` package version should match the ROCm release of the wheel (10.0, 10.1 or
  10.2). The install page links the rocJPEG docs to ROCm v10.1.0 and calls the docs version 1.13.0.
- **Documented.** The "Install" page says to complete the ROCm prerequisites first. They set up
  dependencies and GPU access permissions.

### 3.9 Licence

MIT for rocJPEG (documented, README). The licence of rocPyDecode: not found. The licence of the ROCm
packages that `amdrocm-jpeg` pulls in: not read (the home page links to
https://rocm.docs.amd.com/en/latest/about/license.html).

## 4. The hand-over question: HIP memory to the ONNX Runtime MIGraphX EP

**Question.** Can a rocJPEG output (HIP memory) feed the `migraphx` EP from the Python API with no
host copy?

**Documented.**

- `IOBinding.bind_input(name, device_type, device_id, element_type, shape, buffer_ptr)` takes a raw
  memory pointer. Its `device_type` examples are "cpu, cuda, cann". `OrtValue.ortvalue_from_numpy`
  and `ortvalue_from_shape_and_type` name "cpu, cuda, cann" too. `OrtValue.device_name()` lists
  "cpu, cuda, cann, webgpu". The signature also has `vendor_id` ("should be 'gpu' or 'npu'" when
  set) and, for `ortvalue_from_shape_and_type`, an optional `memory_info`. Source:
  https://onnxruntime.ai/docs/api/python/api_summary.html (the writer read the first 100000
  characters of 113626; the rest could hold more).
- `OrtValue.from_dlpack(data)` builds an OrtValue from an object with `__dlpack__` and
  `__dlpack_device__` and shares the memory with no copy. Same source.
- The device tensor page shows an example only for `dml` in Python and `cuda` in C++. It does not
  mention ROCm, MIGraphX or OpenVINO. Source: https://onnxruntime.ai/docs/performance/device-tensor.html
- The MIGraphX EP page does not mention I/O binding, device memory, an `OrtValue` from a device
  pointer, a device name or HIP memory. Its only memory option is `migraphx_mem_limit`. Source:
  https://onnxruntime.ai/docs/execution-providers/MIGraphX-ExecutionProvider.html
- The AMD ONNX Runtime install page says nothing about I/O binding or device memory. Source:
  https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/inference/onnxruntime.html

**Not found.**

- A device name for MIGraphX memory (for example `"migraphx"` or `"rocm"`) in the Python API.
- Any statement that a plugin EP (the `onnxruntime-ep-migraphx` wheel registers the EP with
  `register_execution_provider_library`) accepts a device `OrtValue` that it did not allocate.
- A statement of the MIGraphX Python API (the `migraphx` module of `migraphx-libs`) about
  zero-copy input from a HIP pointer. The writer did not read the MIGraphX Python API pages.

**Guess (inferred, not a fact).**

- The only route that the Python API documents for a raw device pointer is `bind_input` with a
  `device_type` string that ONNX Runtime knows. If the plugin EP registers a memory info with a
  device name, `ortvalue_from_shape_and_type(..., memory_info=...)` could create an `OrtValue` on
  that device, and a copy from the rocJPEG buffer (HIP device-to-device copy) could fill it. That is
  a GPU-side copy, not a host copy, and it is cheap. Whether it works is **unknown**.
- The package already faces this on DirectML. From
  [`AGENTS.md`](../skellytracker/AGENTS.md) of the package: on `directml`, a DML session does not
  always read a frame that `upload_frame` put in `dml` memory, so the frame stage gives host
  memory. The same limit can hold on `migraphx`.
- The package gives the `migraphx` EP the status `field-test` and its preprocess checks are
  `record-only`
  ([`ep_catalog.yaml`](../skellytracker/core/eps/ep_catalog.yaml), row `migraphx`). No project run
  has bound device memory on that EP.

**What the worker must find out first (a 1-hour test on an AMD system, no decode needed):**

1. List the memory infos that the registered `migraphx` plugin EP exposes
   (`session.get_provider_options()` and the EP device list of the ONNX Runtime plugin API in
   `registration.ort_device()` of the package).
2. Try `OrtValue.ortvalue_from_shape_and_type` with the device names `"migraphx"` and `"rocm"` and
   with `memory_info`. Record the error text of each.
3. Try `bind_input` with a `hipMalloc` pointer and each device name. Compare the output with a
   host numpy input. Record whether a copy happens (time the call against a host input).
4. If all fail: the hand-over is closed on this ONNX Runtime version. Then rocJPEG can at most
   save CPU time, and a copy to the host is in the path (apply the stop rule of section 6).

## 5. Other AMD routes

| Route | What the writer found | Why it is weaker |
|---|---|---|
| VA-API through FFmpeg | FFmpeg has a VA-API MJPEG hardware path: a source file `vaapi_mjpeg.c` defines an hwaccel named `mjpeg_vaapi` for the pixel format `AV_PIX_FMT_VAAPI` (FFmpeg doxygen, https://ffmpeg.org/doxygen/8.0/vaapi__mjpeg_8c.html). The FFmpeg VA-API wiki lists "MJPEG / JPEG mjpeg_vaapi" (https://trac.ffmpeg.org/wiki/Hardware/VAAPI). **Not confirmed:** whether `mjpeg_vaapi` is the decoder path, the encoder, or both. The writer read the wiki only as a search snippet. The usual FFmpeg way for decode is `-hwaccel vaapi`. | The surface is a VA-API surface. A frame that goes to the host is NV12 (inferred: the same pattern as `mjpeg_qsv` in ADR-71YY). A frame that stays on the GPU needs a VA-API to HIP or to ONNX Runtime bridge. That is what rocJPEG already does (section 2). |
| Windows with AMF | `VideoDecoderUVD.h` of the GPUOpen AMF repository defines `AMFVideoDecoderUVD_MJPEG` (found, with MPEG2, MPEG4, WMV3, VC1, H264_AVC, H264_MVC and H264_SVC). HEVC, VP9 and AV1 use the separate prefix `AMFVideoDecoderHW_`. The README of AMF says it runs on Windows 10 or 11 and on Linux (RHEL, Ubuntu 24.04 and SLES). It calls the Linux decoder "experimental". It does not mention MJPEG or UVD. Sources: https://raw.githubusercontent.com/GPUOpen-LibrariesAndSDKs/AMF/master/amf/public/include/components/VideoDecoderUVD.h and https://raw.githubusercontent.com/GPUOpen-LibrariesAndSDKs/AMF/master/README.md | The name exists in the header. **Not found:** a statement in the AMF documentation that a current driver implements it for current GPUs, the output surface formats, or a Python binding. A search result for the FFmpeg AMF decoder source (`amfdec.c`) shows H.264, HEVC and AV1 and no MJPEG case (a snippet, not a full read). The output is an AMF surface (DX11 or DX12), which ONNX Runtime Python does not read, as with D3D textures in ADR-71YY. The hardware of the older name "UVD" may not exist on current GPUs (inferred). |
| D3D11VA or D3D12VA | Not researched beyond this note. **Not found.** | Same hand-over limit as AMF (inferred). |
| `hybrid` backend of rocJPEG | In the enum only. **Not found:** what it does. | Unknown. |

## 6. Next-step plan for a worker with an AMD Linux system

### 6.1 Prerequisites

- An AMD GPU of the table in 3.1 (a Navi2x or Navi3x consumer card is the realistic case), with a
  ROCm release that matches the `migraphx` pack of the catalog (10.0, 10.1 or 10.2). Record the
  ROCm version, the rocJPEG version, the driver and the GPU id (`gfx...`) in the evidence entry,
  with no host name.
- Install `amdrocm-jpeg-dev`. Run the `jpegdecode` sample of the rocJPEG repository on one JPEG to
  prove that the decode works.
- Call `rocJpegGetDecoderCaps()` and `rocJpegGetImageInfo()` for a 4:2:2 JPEG. Record whether 4:2:2
  is supported, and the number of JPEG cores. If 4:2:2 is not supported on the GPU: stop.

### 6.2 Measurement, before any build

Use the method of
[ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md) and
[ADR-58F5](../decisions/entries/58F5-native-jpeg-numbers-on-the-pinned-versions.md).

- Batches: 3 x 1280x720 and 6 x 1920x1080. JPEG: 4:2:2, quality 90, baseline. Synthetic images
  (never a camera frame).
- Warm-up 10 batches. Timed: 200 batches for each cell.
- The baseline: the CPU thread pool of `min(frames, CPUs)` workers, with limits of 2, 4 and all
  logical CPUs (process affinity).
- Paths to time, end to end to the model input on `migraphx` (the model input tensor, not BGR on
  the host):
  1. CPU pool decode, then upload to the EP.
  2. rocJPEG batched decode (native YUYV and RGB output, each), then the conversion and the
     preprocess on the GPU if it exists, then the hand-over to the model session. Time the hand-over
     in each way that section 4 finds (device bind, or a host copy).
- Record for each cell: median, p95 and maximum of the wall time; the CPU time of the process; the
  start cost of the first decode of the handle and of each stream handle; the GPU memory use.
- Record pixel agreement against `cv2.imdecode`: largest step, mean, and the share of values above
  3 steps. Check the channel order (RGB against BGR) and the colour matrix.
- Put the script in `scripts/` of the decision log (the entry names it). Record the result as an
  evidence entry, win or lose.

### 6.3 Stop rule (a proposal; the user decides the numbers)

Do not build if any of these is true:

- the batch decode with its hand-over is not faster than the CPU pool in the median at 4 logical
  CPUs on both batches;
- the hand-over needs a copy to host memory and the decode plus the host copy is slower than the
  full CPU pool (reference from ADR-58F5: the CPU pool plus the upload costs more than the pool
  alone, so a copy through the host never pays);
- the p95 or the maximum is much worse than the CPU pool (for example the maximum more than twice
  the CPU maximum);
- the pixel result differs from `cv2.imdecode` by more than the CPU paths differ from each other
  (the 4:2:0 cells of ADR-71YY differ by at most 3 steps);
- the decode fails on real baseline 4:2:2 camera JPEG (for example a buffer with no DHT).

### 6.4 If the measurement passes: how it enters the package

Follow the shape of the NVIDIA decoder. This is the proposed design, not a decision.

1. **A component in the EP catalog** like `gpu-jpeg-cu13`
   ([`ep_catalog.yaml`](../skellytracker/core/eps/ep_catalog.yaml), key `components`). A first
   question: the catalog installs wheels from a Python index
   ([ADR-88ZB](../decisions/entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)).
   rocJPEG is a system package of ROCm, not a wheel (3.8). So the component can be a "system
   library" that the code probes, not an install. This needs a decision entry.
2. **A decoder class** beside `NvJpegDecoder`
   ([`nvidia.py`](../skellytracker/core/decode/nvidia.py)), for example `RocJpegDecoder` in
   `core/decode/amd.py`. Same shape: `open(execution_provider, ...)` gives the decoder or None; a
   self-test decode at the open with a time limit; a buffer that the hardware refuses gives None
   and the caller decodes it on the CPU ([`cpu.py`](../skellytracker/core/decode/cpu.py)); one
   decoder for each device, from one thread; no import of the library at import time. The
   `ctypes` route needs only the `libhip` and `librocjpeg` symbols (compare `CUDART_SYMBOLS`).
3. **The executor.** `JPEG_DECODER_EPS` of the executor (named in the package `AGENTS.md`) would
   add `migraphx`, with the warning `jpeg_decoded_on_cpu` on a refused buffer.
4. **Certify checks, record-only first.** The checks of the JPEG certification
   (`run_jpeg_certification`) already say `not-run` with `no_gpu_decode_on_ep` on an EP with no
   GPU decode. The `migraphx` EP has `record-only` checks today (package `AGENTS.md`). A rocJPEG
   check should also be `record-only` until a reviewed report from AMD hardware exists. The check
   name list is frozen: a new check adds names and does not rename.
5. Update the pages of the docs site that name the supported EPs (skill `update-docs-site`).

## 7. Risks

| Risk | Basis |
|---|---|
| One JPEG core on a consumer card | Documented: 1 core for Navi2x and Navi3x (3.1). The batch API gains little with one core (inferred). Instinct cards have 2 to 32 cores but are not the target. |
| Tail latency | Not measured. A single core shared with other media work (video decode or encode on the same VCN) can queue (guess). Record p95 and the maximum. |
| ROCm version coupling with the `migraphx` pack | Documented: the wheels are `+rocm10.0.0`, `+rocm10.1.0` and `+rocm10.2.0`, and the catalog says "ROCm 10.0, 10.1 or 10.2". rocJPEG comes from the same ROCm install. A mismatch of the HIP runtime between rocJPEG and the EP is inferred as a risk, as the project already had for `cudart` on NVIDIA (comment above `components` in the catalog). |
| No hand-over to the model session | Section 4: nothing documented. The main risk. The same limit already holds for `directml` in the package. |
| Consumer GPU list is incomplete | Radeon RX 9000 not found (3.1). A Ryzen AI APU is in the CHANGELOG with no core count. |
| Linux only | Documented (3.2). The package has `migraphx` on Windows through Windows ML. A rocJPEG decoder would not serve it. |
| Python binding returns unknown memory | Section 3.7: not found. Use `ctypes` on the C library, or test the binding first. |
| Documentation drift | The docs say "latest" with versions 1.13.0 (install page) and 1.14.0 (CHANGELOG), and ROCm 7.13, 7.14 and 10.x names appear. The worker must pin the version that the test used. |
| Buffer overflow bug for odd sizes | Fixed in 1.14.0 (CHANGELOG). Use 1.14.0 or newer. |
| Baseline only | Documented. A progressive JPEG must fall back to the CPU. Camera MJPEG is baseline in most cases (inferred). |

## Questions that this note could not answer

- Does a Radeon RX 9000 (gfx1200, gfx1201) have a JPEG core that rocJPEG uses, and how many?
- How many JPEG cores do the Ryzen AI APUs (gfx1150 to gfx1153) have, and are older APUs supported?
- Is the output of rocPyJpegDecode in device memory or in host memory, and does it export DLPack?
- Does the single-image path of rocJPEG convert colour on the GPU? (Only the batched path is
  documented.)
- Is the RGB output RGB or BGR order, and which colour matrix does it use?
- What does `ROCJPEG_BACKEND_HYBRID` do?
- Can the `onnxruntime-ep-migraphx` plugin EP read a device `OrtValue`, and with which device
  name? Can the MIGraphX Python API read a HIP pointer?
- Does AMF give a working MJPEG decoder on a current driver, with which output formats?
- Is there a wheel of rocJPEG or rocPyDecode on an AMD or PyPI index, and what is the licence of
  rocPyDecode?
- Does rocJPEG decode a camera MJPEG buffer that has no DHT segment?

## Sources

All URLs were read on 2026-11-23. A tool fetched each page, and a summary was returned. Thus a
text in quotation marks can differ from the page, and the worker must read each page again before a
decision.

Project entries (relative links above):
[ADR-71YY](../decisions/entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md),
[ADR-58F5](../decisions/entries/58F5-native-jpeg-numbers-on-the-pinned-versions.md),
[ADR-88ZB](../decisions/entries/88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md).

- https://rocm.docs.amd.com/projects/rocJPEG/en/latest/
- https://rocm.docs.amd.com/projects/rocJPEG/en/latest/install/rocjpeg-install.html
- https://rocm.docs.amd.com/projects/rocJPEG/en/latest/how-to/using-rocjpeg.html
- https://rocm.docs.amd.com/projects/rocJPEG/en/latest/how-to/rocjpeg-decoding-a-jpeg-stream.html
- https://rocm.docs.amd.com/projects/rocJPEG/en/latest/reference/rocjpeg-formats-and-architectures.html
- https://rocm.docs.amd.com/projects/rocJPEG/en/latest/reference/rocJPEG-api-reference.html
- https://github.com/ROCm/rocm-systems/tree/develop/projects/rocjpeg
- https://github.com/ROCm/rocm-systems/blob/develop/projects/rocjpeg/CHANGELOG.md
- https://rocm.docs.amd.com/en/latest/about/license.html (linked, not read)
- https://rocm.docs.amd.com/projects/rocPyDecode/en/latest/index.html
- https://rocm.docs.amd.com/projects/rocPyDecode/en/latest/reference/rocPyJPEGDecode-api.html
- https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/inference/onnxruntime.html
- https://onnxruntime.ai/docs/api/python/api_summary.html
- https://onnxruntime.ai/docs/performance/device-tensor.html
- https://onnxruntime.ai/docs/execution-providers/MIGraphX-ExecutionProvider.html
- https://ffmpeg.org/doxygen/8.0/vaapi__mjpeg_8c.html
- https://trac.ffmpeg.org/wiki/Hardware/VAAPI
- https://raw.githubusercontent.com/GPUOpen-LibrariesAndSDKs/AMF/master/amf/public/include/components/VideoDecoderUVD.h
- https://raw.githubusercontent.com/GPUOpen-LibrariesAndSDKs/AMF/master/README.md
