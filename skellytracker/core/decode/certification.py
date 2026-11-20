"""`run_jpeg_certification`: the JPEG decode and frame preprocess checks of one machine, for a certify suite.

A certify suite calls the function in a child process and reads its JSON-able result. Each check
name is stable: a later release adds names and never renames or removes one. A check that needs an
EP that is not present gives `not-run`, so each platform gets the full list. Each input is a
synthetic image that the function makes and encodes in memory. The function writes no file. No text
of the result holds an absolute path, a host name, a user name, a serial number or an environment
dump.

This module imports no `onnxruntime`, no `onnx`, no `cv2` and no GPU library at import time.
"""
from __future__ import annotations

import platform
import re
import statistics
from collections.abc import Callable
from typing import Any

SCHEMA = 1
RESULTS = ("pass", "fail", "not-run", "record-only")
REASONS = (
    "ok",  # the check passed
    "over_limit",  # a difference is more than the limit of the check
    "mismatch",  # a shape, a dtype or a bitwise comparison is not equal
    "refused",  # the decoder refused a buffer that it must decode
    "not_refused",  # the decoder decoded a buffer that it must refuse
    "warning_given",  # the run gave a warning that the check does not allow
    "decoder_not_opened",  # the GPU JPEG decoder is installed, but it did not open
    "ep_not_present",  # the EP of the check is not requested, not installed or not usable
    "no_gpu_decode_on_ep",  # a `gpu_decode` check on an EP with no GPU JPEG decode: only `cuda` and `trt-rtx` have one
    "component_not_installed",  # the GPU JPEG decoder component of the EP is not installed
    "sidecar_not_available",  # a package sidecar does not load
    "models_not_available",  # the ONNX files of the built-in pipeline are not on this machine
    "raised",  # the check raised an exception
    "recorded",  # a record-only check recorded its numbers
)
GPU_FRAME_EPS = ("cuda", "trt-rtx")  # the NVIDIA EPs: the only EPs with the GPU JPEG decode, and the EPs of the GPU preprocess
AMD_EPS = {"directml": "dml", "amdgpu": "gpu", "migraphx": "gpu"}  # the EPs of an AMD GPU, and the device type of their memory
SCORED_AMD_EPS = ("directml",)  # a check of the group `*_amd_ep` on each other EP of AMD_EPS gives `record-only`
AMD_HANDOVER_REPEATS = 300
UPLOAD_REPEATS = 50
FAR_SOURCE = (3840, 2160)  # the frame of the far-corner ROIs: large sampler positions stress the float precision
GPU_LIMIT = 3  # the max abs difference of a GPU decode against the CPU decode (measured on this branch: 3)
CPU_MEAN_LIMIT = 3.0  # the mean abs difference of a CPU decode of a quality 95 JPEG against its source image
QUALITY = 95
SIZES = ((320, 240), (640, 480), (1280, 720), (1920, 1080), (720, 1280))
ROTATIONS = (0, 90, 180, 270)
SIDECARS = {"yolox_person": "yolox-person@openmmlab-exporter", "rtmw_wholebody133": "rtmw-wholebody133@openmmlab-exporter"}
SIDECAR_SIZE = "m"  # the size of both models in the built-in pipeline
MIXED_SOURCES = ((1280, 720), (480, 640), (97, 61), (640, 480), (1920, 1080))
HANDOVER_REPEATS = 20
PIPELINE_KEY = "yolox-rtmw-wholebody@skellytracker"
PIPELINE_FRAMES = 8
PIPELINE_SPANS = ("frame.decode", "person.preprocess", "wholebody.preprocess")
PIPELINE_WARNINGS = ("preprocessed_on_cpu", "jpeg_decoded_on_cpu")
QUICK_CHECKS = {"gpu_decode.baseline_422": "jpeg-decode", "preprocess_graph_ep.yolox_person": "jpeg-preprocess"}  # the checks of `run_jpeg_quick_checks` and their names there
_PATH = re.compile(r"(?<![\w.])(?:[A-Za-z]:[\\/]|\\\\|~[\\/]|/(?=\w))[^\s'\",;)]*")


class _Stop(Exception):
    """Stop one check with a fixed result: `not-run`, or `fail` with a reason that is not `raised`."""

    def __init__(self, reason: str, detail: str = "", result: str = "not-run") -> None:
        super().__init__(reason)
        self.result, self.reason, self.detail = result, reason, detail


def run_jpeg_certification(ep_key: str | None = None, *, device_key: str | None = None,
                           progress: Callable[[str], None] | None = None) -> dict:
    """Run each check on this machine and return `{"schema", "ep_key", "facts", "checks"}`: JSON-able data only.

    `device_key` selects the GPU of each session and pipeline run on `ep_key`, as in `build_session()`.
    With None, the run uses the default GPU of the EP. A GPU that the EP cannot use gives `not-run`
    with the reason `ep_not_present` for each check that needs a session on the EP. `facts["device"]` gives the
    `device_key` and the `device_name` of the GPU of the run, or None when no check opened a session
    on a GPU.

    `ep_key` is the EP of the GPU checks and of the pipeline checks. Only the NVIDIA EPs `cuda` and
    `trt-rtx` have a GPU JPEG decode. The checks `gpu_decode.*`, `preprocess_graph_ep.*` and
    `pipeline.gpu_auto_vs_cpu` run on these two EPs. The checks `preprocess_graph_amd_ep.*` and
    `pipeline_amd_ep.*` run on the EPs of an AMD GPU: `directml`, `amdgpu` and `migraphx`. On `amdgpu`
    and `migraphx`, such a check gives `record-only` in place of `pass` or `fail`, and an exception is
    a `record-only` result with the reason `raised`. Each GPU check of an other EP, and of None,
    gives `not-run`. The reason is `no_gpu_decode_on_ep` for a `gpu_decode` check on an other EP, and
    `ep_not_present` for each other case. `progress(name)` is called before each check.

    Each item of `checks` has `name`, `result` (a value of `RESULTS`), `reason` (a value of
    `REASONS`), `numbers` (str to int or float), `warnings` (`{code, reason}` of each warning of the
    run) and `detail` (short text; for `raised`, the exception type and its message with no path).
    A check that fails or raises does not stop the next check. A timing number is always
    `record-only`.
    """
    from skellytracker.core.eps import gate

    with gate.certification_run():  # the certification runs an EP before the EP has a result (ADR-ER5X)
        return _certify(ep_key, device_key, progress)


def run_jpeg_quick_checks(ep_key: str, *, device_key: str | None = None, progress: Callable[[str], None] | None = None) -> list[dict]:
    """Run the two quick checks of the GPU frame path on `ep_key` and return them: `jpeg-decode`, then `jpeg-preprocess`.

    Each item has the form of an item of `run_jpeg_certification()["checks"]`. `jpeg-decode` is the
    check `gpu_decode.baseline_422`, and `jpeg-preprocess` is the check
    `preprocess_graph_ep.yolox_person`. They need no ONNX model file. On an EP other than `cuda` and
    `trt-rtx`, both give `not-run`: `jpeg-decode` with `no_gpu_decode_on_ep`, and `jpeg-preprocess`
    with `ep_not_present`. A check that raises gives `fail` with `raised`. A failed check
    stops only the GPU frame path, not the EP.
    """
    from skellytracker.core.eps import gate

    with gate.certification_run():
        return _certify(ep_key, device_key, progress, quick=True)["checks"]


def _certify(ep_key: str | None, device_key: str | None, progress: Callable[[str], None] | None, quick: bool = False) -> dict:
    """The checks of both entry points. With `quick`, only the checks of `QUICK_CHECKS`, with their new names, and no facts."""
    import cv2
    import numpy as np

    from skellytracker.core.decode import cpu

    state: dict[str, Any] = {}  # the shared sessions and the GPU decoder of the run
    gpu_ep = ep_key if ep_key in GPU_FRAME_EPS else None
    amd_ep = ep_key if ep_key in AMD_EPS else None

    def device_of(execution_provider: str) -> str | None:
        """The chosen GPU for a session or a run on `ep_key`; the checks on the CPU EP take none."""
        return device_key if execution_provider == ep_key else None

    def picture(width: int, height: int, seed: int = 0) -> np.ndarray:
        """Gradients, noise and shapes, blurred: a JPEG of it is not trivial, and each pixel position differs."""
        y, x = np.mgrid[0:height, 0:width]
        image = np.dstack([x * 255 // max(width - 1, 1), y * 255 // max(height - 1, 1), (x + 3 * y) % 256]).astype(np.uint8)
        image = image + np.random.default_rng(seed).integers(0, 30, image.shape, dtype=np.uint8)
        cv2.rectangle(image, (width // 8, height // 6), (width // 3, height // 2), (30, 200, 90), -1)
        cv2.circle(image, (2 * width // 3, height // 2), max(min(width, height) // 6, 1), (220, 40, 160), -1)
        return cv2.GaussianBlur(image, (5, 5), 0)

    def jpeg(image: np.ndarray, sampling: str = "420", progressive: bool = False) -> bytes:
        factors = {"420": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_420, "422": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_422,
                   "444": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_444}
        params = [cv2.IMWRITE_JPEG_QUALITY, QUALITY, cv2.IMWRITE_JPEG_PROGRESSIVE, int(progressive)]
        if image.ndim == 3:
            params += [cv2.IMWRITE_JPEG_SAMPLING_FACTOR, factors[sampling]]
        ok, encoded = cv2.imencode(".jpg", image, params)
        if not ok or (progressive and b"\xff\xc2" not in encoded.tobytes()):  # SOF2: the progressive frame header
            raise RuntimeError("OpenCV did not encode the JPEG image of the check")
        return encoded.tobytes()

    def without_dht(data: bytes) -> bytes:
        """The JPEG with each DHT segment before the scan removed, as many MJPEG cameras send it."""
        out, i = bytearray(data[:2]), 2
        while i + 4 <= len(data) and data[i] == 0xFF and data[i + 1] != 0xDA:
            end = i + 2 + int.from_bytes(data[i + 2:i + 4], "big")
            if data[i + 1] != 0xC4:
                out += data[i:end]
            i = end
        return bytes(out + data[i:])

    def diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.abs(a.astype(np.int16) - b.astype(np.int16))

    def source(name: str) -> tuple[np.ndarray, bytes]:
        """The source image (BGR, or 3 equal channels for grayscale) and its JPEG for each named input."""
        if name == "grayscale":
            gray = cv2.cvtColor(picture(640, 480, 3), cv2.COLOR_BGR2GRAY)
            return np.dstack([gray] * 3), jpeg(gray)
        if name.startswith("size_"):
            width, height = (int(v) for v in name[5:].split("x"))
            image = picture(width, height, width + height)
            return image, jpeg(image)
        image = picture(640, 480, 1)
        sampling = name.rsplit("_", 1)[1] if name.startswith(("baseline", "truncated")) else "420"
        return image, jpeg(image, sampling, progressive=name == "progressive")

    # --- CPU decode ---

    def cpu_close(name: str) -> dict:
        image, data = source(name)
        found = cpu.decode_jpeg(data)
        if found.dtype != np.uint8 or found.shape != image.shape:
            return {"result": "fail", "reason": "mismatch", "detail": f"shape {found.shape} {found.dtype}, expected {image.shape} uint8"}
        d = diff(found, image)
        numbers = {"mean_abs_diff": round(float(d.mean()), 4), "max_abs_diff": int(d.max()), "limit_mean": CPU_MEAN_LIMIT}
        return _passed(numbers["mean_abs_diff"] <= CPU_MEAN_LIMIT, numbers)

    def cpu_no_dht() -> dict:
        image, data = source("baseline_420")
        stripped = without_dht(data)
        if b"\xff\xc4" in stripped[:stripped.find(b"\xff\xda")]:
            raise RuntimeError("the DHT segment is still in the test buffer")
        d = diff(cpu.decode_jpeg(stripped), image)
        numbers = {"mean_abs_diff": round(float(d.mean()), 4), "max_abs_diff": int(d.max()), "limit_mean": CPU_MEAN_LIMIT}
        return _passed(numbers["mean_abs_diff"] <= CPU_MEAN_LIMIT, numbers)

    def cpu_rotation(rotation: int) -> dict:
        _, data = source("baseline_420")
        expected = np.rot90(cpu.decode_jpeg(data), k=-rotation // 90)  # clockwise
        found = cpu.decode_jpeg(data, rotation)
        same = found.shape == expected.shape and np.array_equal(found, expected)
        return _passed(same, {"height": int(found.shape[0]), "width": int(found.shape[1])}, "mismatch")

    def cpu_no_soi() -> dict:
        _, data = source("baseline_420")
        try:
            cpu.decode_jpeg(data[2:])
        except ValueError:
            return _passed(True, {})
        return {"result": "fail", "reason": "not_refused", "detail": "a buffer with no SOI marker decoded"}

    def cpu_truncated() -> dict:
        _, data = source("baseline_420")
        full = cpu.decode_jpeg(data)
        try:
            found = cpu.decode_jpeg(data[:len(data) // 2])
        except ValueError:
            return {"result": "record-only", "reason": "recorded", "numbers": {"decoded": 0, "kept_ratio": 0.5}, "detail": "refused: ValueError"}
        numbers = {"decoded": 1, "kept_ratio": 0.5, "max_abs_diff_to_full": int(diff(found, full).max())}
        return {"result": "record-only", "reason": "recorded", "numbers": numbers, "detail": "decoded with no error"}

    # --- GPU decode ---

    def probe_report(execution_provider: str | None, group: str) -> Any:
        """The `SessionReport` of a probe session on the EP of a check group, or raise `_Stop`."""
        if execution_provider is None:
            raise _Stop("ep_not_present", f"the EP {ep_key!r} has no {group}" if ep_key else "no EP is requested")
        key = f"report:{execution_provider}"
        if key not in state:
            from skellytracker.core.eps._probe_model import model_bytes
            from skellytracker.core.eps.session import build_session
            from skellytracker.core.errors import EpRequestError, EpUnavailableError

            try:
                state[key] = build_session(model_bytes(), execution_provider=execution_provider, device_key=device_key)[1]
            except (EpRequestError, EpUnavailableError):  # also a key that is not in the EP catalog, for example `amdgpu`
                state[key] = None
        if state[key] is None:
            raise _Stop("ep_not_present", f"the EP {execution_provider!r} is not installed or not usable")
        return state[key]

    def gpu_report() -> Any:
        return probe_report(gpu_ep, "GPU frame path")

    def amd_report() -> Any:
        return probe_report(amd_ep, "check of an AMD GPU")

    def decoder() -> Any:
        if ep_key is not None and ep_key not in GPU_FRAME_EPS:
            raise _Stop("no_gpu_decode_on_ep", f"the EP {ep_key!r} has no GPU JPEG decode: only the NVIDIA EPs 'cuda' and 'trt-rtx' have one")
        report = gpu_report()
        if "decoder" not in state:
            from skellytracker.core.decode.nvidia import NvJpegDecoder

            state["decoder"] = None  # an open that raises stays failed for each check
            state["decoder"] = NvJpegDecoder.open(gpu_ep, report.device_key, report.ep_device_id)
        if state["decoder"] is None:
            from skellytracker.core.eps import store
            from skellytracker.core.eps.catalog import load_catalog

            component = store.component_state(load_catalog(), gpu_ep)
            if component != "installed":
                raise _Stop("component_not_installed", f"the GPU JPEG decoder component is {component or 'not in the catalog'}")
            raise _Stop("decoder_not_opened", "the GPU JPEG decoder is installed, but it did not open", "fail")
        return state["decoder"]

    def gpu_compare(buffers: list[bytes], rotations: list[int]) -> dict:
        frames = decoder().decode(buffers, rotations)
        refused = sum(frame is None for frame in frames)
        worst = 0
        for data, rotation, frame in zip(buffers, rotations, frames, strict=True):
            if frame is None:
                continue
            expected = cpu.decode_jpeg(data, rotation)
            if frame.host.shape != expected.shape:
                return {"result": "fail", "reason": "mismatch", "detail": f"shape {frame.host.shape}, expected {expected.shape}"}
            worst = max(worst, int(diff(frame.host, expected).max()))
        numbers = {"max_abs_diff": worst, "limit": GPU_LIMIT, "refused": refused, "buffers": len(buffers)}
        if refused:
            return {"result": "fail", "reason": "refused", "numbers": numbers}
        return _passed(worst <= GPU_LIMIT, numbers)

    def gpu_batch(count: int) -> dict:
        sizes = [(640, 480), (641, 359), (64, 48), (1280, 720), (33, 17), (320, 240)]
        buffers = []
        for i, (width, height) in enumerate(sizes[:count]):
            image = picture(width, height, i)
            buffers.append(jpeg(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)) if i == 2 else jpeg(image, ("420", "422")[i % 2]))
        return gpu_compare(buffers, [0] * count)

    def gpu_must_refuse(data: bytes) -> dict:
        (frame,) = decoder().decode([data], [0])
        if frame is None:
            return _passed(True, {})
        return {"result": "fail", "reason": "not_refused", "detail": "the GPU decoder gave a frame; the run does not fall back to the CPU"}

    def gpu_truncated(sampling: str) -> dict:
        _, data = source(f"truncated_{sampling}")
        (frame,) = decoder().decode([data[:len(data) // 2]], [0])
        if frame is None:
            return {"result": "record-only", "reason": "recorded", "numbers": {"decoded": 0, "kept_ratio": 0.5}, "detail": "refused"}
        numbers = {"decoded": 1, "kept_ratio": 0.5, "max_abs_diff_to_full": int(diff(frame.host, cpu.decode_jpeg(data)).max())}
        return {"result": "record-only", "reason": "recorded", "numbers": numbers, "detail": "decoded with no error"}

    # --- preprocess graph ---

    def sidecar(name: str) -> Any:
        from skellytracker.core.detectors.catalog import DetectorUnavailableError, load_detector_sidecar

        try:
            return load_detector_sidecar(SIDECARS[name])
        except (DetectorUnavailableError, KeyError):
            raise _Stop("sidecar_not_available", f"the package sidecar {SIDECARS[name]} does not load") from None

    def case(model: Any, mixed: bool, far: bool = False) -> tuple[list[tuple[int, int]], list[int], list[Any]]:
        """The sources, the index and the ROIs of one graph: one 1280x720 slot, the slots of `MIXED_SOURCES`, or ROIs at the far corner of `FAR_SOURCE`."""
        if far:
            width, height = FAR_SOURCE
            rois = [(0.97 * width, 0.96 * height, 0.05 * width, 0.08 * height, 0.0), (width - 40.0, height - 60.0, 60.0, 90.0, 0.0),
                    (0.95 * width, 0.93 * height, 0.08 * width, 0.1 * height, 0.3)]
            return [FAR_SOURCE], [0, 0, 0], rois
        sources = list(MIXED_SOURCES) if mixed else [(1280, 720)]
        if model.input.resize.method != "affine_crop":
            return sources, [4, 0, 3, 1, 0] if mixed else [0], [None] * (5 if mixed else 1)
        items = [(4, 0.95, 0.92, 0.0), (1, 0.5, 0.5, 0.0), (0, 0.05, 0.08, 0.0), (3, 0.85, 0.8, 0.7)] if mixed else \
                [(0, 0.5, 0.5, 0.0), (0, 0.9, 0.1, 0.0), (0, 0.3, 0.6, 0.4)]
        rois = [(cx * sources[s][0], cy * sources[s][1], 0.4 * sources[s][0], 0.5 * sources[s][1], r) for s, cx, cy, r in items]
        return sources, [s for s, *_ in items], rois

    def graph_session(model: Any, sources: list, batch: int, execution_provider: str) -> tuple[Any, Any]:
        from skellytracker.core.detectors.processing.pre.graph import build_preprocess_graph
        from skellytracker.core.eps.session import build_session

        graph = build_preprocess_graph(model, SIDECAR_SIZE, "fp32", sources, batch)
        return build_session(graph.SerializeToString(), execution_provider=execution_provider, device_key=device_of(execution_provider))

    def feeds_of(model: Any, sources: list, index: list[int], rois: list[Any]) -> tuple[list[np.ndarray], dict]:
        from skellytracker.core.detectors.processing.pre.graph import affine_crop_theta

        images = [picture(w, h, 10 + i) for i, (w, h) in enumerate(sources)]
        feeds = {f"frame_{i}": image for i, image in enumerate(images)} | {"index": np.array(index, np.int64)}
        if model.input.resize.method == "affine_crop":
            feeds["theta"] = affine_crop_theta(model, SIDECAR_SIZE, sources, rois)
        return images, feeds

    def graph_check(name: str, mixed: bool, execution_provider: str | None, far: bool = False) -> dict:
        from skellytracker.core.detectors.processing.pre.preprocess import preprocess_image, resize_image
        from skellytracker.core.detectors.processing.pre.resize_interpolation import within_resize_limit

        model = sidecar(name)
        if execution_provider is None:
            execution_provider = gpu_report().requested_ep
        spec = model.input
        sources, index, rois = case(model, mixed, far)
        session, report = graph_session(model, sources, len(index), execution_provider)
        images, feeds = feeds_of(model, sources, index, rois)
        tensor, pixels = session.run(["tensor", "pixels"], feeds)
        compute, worst, ok = str(spec.resize.compute_dtype or "uint8"), 0.0, True
        for k, (slot, roi) in enumerate(zip(index, rois, strict=True)):
            reference, _ = resize_image(images[slot], spec.resize, model.size(SIDECAR_SIZE).target_size, spec.color_format, roi)
            reference = (reference[..., ::-1] if spec.color_format == "rgb" else reference).transpose(2, 0, 1)
            difference, within = within_resize_limit(reference, pixels[k], compute)
            expected, _ = preprocess_image(images[slot], model, SIDECAR_SIZE, "fp32", roi)
            if tensor[k].shape != expected.shape or tensor[k].dtype != expected.dtype:
                return {"result": "fail", "reason": "mismatch", "detail": f"tensor {tensor[k].shape} {tensor[k].dtype}, expected {expected.shape} {expected.dtype}"}
            ok &= within
            worst = max(worst, difference) if np.isfinite(difference) else worst  # a NaN fails `within` and is no JSON number
        return _passed(ok, {"max_difference": worst, "items": len(index), "cpu_nodes": int(report.cpu_nodes)})

    def node_placement(report_of: Callable[[], Any]) -> dict:
        execution_provider = report_of().requested_ep
        numbers, cpu_ops = {}, set()
        for name in SIDECARS:
            model = sidecar(name)
            sources, index, _ = case(model, mixed=True)
            _, report = graph_session(model, sources, len(index), execution_provider)
            numbers |= {f"{name}.nodes.{ep}": count for ep, count in report.nodes_by_ep}
            numbers[f"{name}.cpu_nodes"] = int(report.cpu_nodes)
            cpu_ops |= set(report.cpu_op_types)
        return {"result": "record-only", "reason": "recorded", "numbers": numbers,
                "detail": f"op types on the CPU: {', '.join(sorted(cpu_ops)) or 'none'}"}

    def second_session(execution_provider: str) -> Any:
        """The second session of a hand-over: y = x * 0.5 + 1, two exact element-wise ops with fixed weights."""
        from onnx import TensorProto, numpy_helper
        from onnx import helper as oh

        from skellytracker.core.eps.session import build_session

        nodes = [oh.make_node("Mul", ["x", "scale"], ["half"]), oh.make_node("Add", ["half", "one"], ["y"])]
        inits = [numpy_helper.from_array(np.array(0.5, np.float32), "scale"), numpy_helper.from_array(np.array(1.0, np.float32), "one")]
        tiny = oh.make_model(oh.make_graph(nodes, "handover", [oh.make_tensor_value_info("x", TensorProto.FLOAT, ["b", 3, "h", "w"])],
                                           [oh.make_tensor_value_info("y", TensorProto.FLOAT, None)], inits),
                             opset_imports=[oh.make_opsetid("", 17)])
        tiny.ir_version = 9
        return build_session(tiny.SerializeToString(), execution_provider=execution_provider, device_key=device_of(execution_provider))[0]

    def handover() -> dict:
        from skellytracker.core.eps.session import run_bound, run_preprocess, upload_frame

        report = gpu_report()
        model = sidecar("yolox_person")
        sources, index, _ = case(model, mixed=False)
        session, graph_report = graph_session(model, sources, 1, gpu_ep)
        second = second_session(gpu_ep)
        device_id = int(graph_report.ep_device_id or report.ep_device_id or 0)
        images = [picture(1280, 720, 30), cv2.flip(picture(1280, 720, 31), -1)]  # two contents of one size
        expected = []
        for image in images:
            (host_tensor,) = session.run(["tensor"], {"frame_0": image, "index": np.array(index, np.int64)})
            expected.append(second.run(["y"], {"x": host_tensor})[0])
        wrong = 0
        for i in range(HANDOVER_REPEATS):
            tensor = run_preprocess(session, [upload_frame(images[i % 2], device_id)], np.array(index, np.int64), None, "cuda", device_id)
            (found,) = run_bound(second, "x", ["y"], tensor)
            wrong += found.tobytes() != expected[i % 2].tobytes()
        return _passed(wrong == 0, {"repeats": HANDOVER_REPEATS, "unequal": wrong}, "mismatch")

    # --- preprocess graph on an EP of an AMD GPU ---

    def amd_scored(check: Callable[[], dict]) -> Callable[[], dict]:
        """On an EP of `AMD_EPS` that is not in `SCORED_AMD_EPS`, the result is `record-only`, also for an exception."""
        def run() -> dict:
            if amd_ep in SCORED_AMD_EPS:
                return check()
            try:
                found = check()
            except _Stop:
                raise
            except Exception as error:  # noqa: BLE001 - an EP that is not scored records each exception
                return {"result": "record-only", "reason": "raised", "detail": _error_text(error)}
            return {**found, "result": "record-only"} if found["result"] in ("pass", "fail") else found
        return run

    def amd_graph(model: Any, sources: list, index: list[int]) -> tuple[Any, str, int]:
        """A graph session on the AMD EP, the device type of its memory and the device id of its bindings."""
        report = amd_report()
        session, graph_report = graph_session(model, sources, len(index), amd_ep)
        device_type = AMD_EPS[amd_ep]
        # a DML session keeps its device memory under the device id 0 on each adapter: the session selects the adapter
        return session, device_type, 0 if device_type == "dml" else int(graph_report.ep_device_id or report.ep_device_id or 0)

    def bound_tensor(session: Any, image: np.ndarray, index: np.ndarray, device_type: str, device_id: int, preallocated: bool = False) -> Any:
        """Run the graph on a host frame with its output `tensor` in device memory: `bind_output`, or a pre-allocated `bind_ortvalue_output`."""
        import onnxruntime

        from skellytracker.core.eps.session import run_preprocess, upload_frame

        frame = upload_frame(image, None, "cpu")
        if not preallocated:
            return run_preprocess(session, [frame], index, None, device_type, device_id)
        shape = [len(index), *session.get_outputs()[0].shape[1:]]
        vendor = {} if device_type == "dml" else {"vendor_id": onnxruntime.OrtDeviceVendorId.AMD}
        out = onnxruntime.OrtValue.ortvalue_from_shape_and_type(shape, np.float32, device_type, device_id, **vendor)
        bound = session.io_binding()
        bound.bind_ortvalue_input("frame_0", frame)
        bound.bind_cpu_input("index", index)
        bound.bind_ortvalue_output("tensor", out)
        session.run_with_iobinding(bound)
        bound.synchronize_outputs()
        return out

    def amd_one_slot() -> tuple[Any, str, int, np.ndarray, Any, np.ndarray, np.ndarray]:
        """The yolox graph of one 1280x720 slot on the AMD EP, the second session, a frame and the host route of it."""
        model = sidecar("yolox_person")
        sources, index, _ = case(model, mixed=False)
        session, device_type, device_id = amd_graph(model, sources, index)
        second = second_session(amd_ep)
        image, slots = picture(1280, 720, 30), np.array(index, np.int64)
        (host_tensor,) = session.run(["tensor"], {"frame_0": image, "index": slots})
        return session, device_type, device_id, slots, second, image, second.run(["y"], {"x": host_tensor})[0]

    def amd_upload() -> dict:
        import time

        from skellytracker.core.eps.session import run_preprocess, upload_frame

        session, device_type, device_id, slots, _, image, _ = amd_one_slot()
        times, unequal = [], 0
        for i in range(UPLOAD_REPEATS):
            changed = np.roll(image, 7 * i, axis=1)  # new content in each repeat
            (expected,) = session.run(["tensor"], {"frame_0": changed, "index": slots})
            try:
                start = time.perf_counter_ns()
                value = upload_frame(changed, device_id, device_type)
                times.append(time.perf_counter_ns() - start)
            except Exception as error:  # noqa: BLE001 - a refused upload is a recorded fact
                return {"result": "record-only", "reason": "recorded", "numbers": {"uploaded": 0}, "detail": _error_text(error)}
            try:
                found = run_preprocess(session, [value], slots, None, "cpu", 0).numpy()  # the graph output in host memory
            except Exception as error:  # noqa: BLE001 - a graph that cannot read the uploaded frame is a recorded fact (Intel UHD 770: device removed)
                return {"result": "record-only", "reason": "recorded", "numbers": {"uploaded": 1, "repeats": i, "unequal": unequal, "read_raised": 1},
                        "detail": _error_text(error)}
            unequal += found.shape != expected.shape or not np.array_equal(found, expected)
        numbers = {"uploaded": 1, "repeats": UPLOAD_REPEATS, "unequal": unequal, "median_upload_ms": round(statistics.median(times) / 1e6, 3)}
        return {"result": "record-only", "reason": "recorded", "numbers": numbers,
                "detail": f"device {value.device_name()}; the graph reads the uploaded frame in {UPLOAD_REPEATS - unequal} of {UPLOAD_REPEATS} repeats (rough time)"}

    def amd_handover() -> dict:
        from skellytracker.core.eps.session import run_bound

        session, device_type, device_id, slots, second, image, _ = amd_one_slot()
        wrong, first = 0, -1
        for i in range(AMD_HANDOVER_REPEATS):
            changed = np.roll(image, 7 * i, axis=1)  # new content in each repeat
            (host_tensor,) = session.run(["tensor"], {"frame_0": changed, "index": slots})
            (expected,) = second.run(["y"], {"x": host_tensor})
            (found,) = run_bound(second, "x", ["y"], bound_tensor(session, changed, slots, device_type, device_id))
            if found.tobytes() != expected.tobytes():
                wrong, first = wrong + 1, i if first < 0 else first
        return _passed(wrong == 0, {"repeats": AMD_HANDOVER_REPEATS, "unequal": wrong, "first_unequal": first}, "mismatch")

    def amd_binding_forms() -> dict:
        from skellytracker.core.eps.session import run_bound

        session, device_type, device_id, slots, second, image, expected = amd_one_slot()
        numbers, failures = {}, []
        for form, preallocated in (("bind_output", False), ("bind_ortvalue_output", True)):
            try:
                (found,) = run_bound(second, "x", ["y"], bound_tensor(session, image, slots, device_type, device_id, preallocated))
                numbers |= {f"{form}.works": 1, f"{form}.equal_host": int(found.tobytes() == expected.tobytes())}
            except Exception as error:  # noqa: BLE001 - a form that does not work is a recorded fact
                numbers |= {f"{form}.works": 0, f"{form}.equal_host": 0}
                failures.append(f"{form}: {_error_text(error)[:120]}")
        return {"result": "record-only", "reason": "recorded", "numbers": numbers, "detail": f"device type {device_type}; " + "; ".join(failures)}

    def amd_device_mapping() -> dict:
        from skellytracker.core.eps.session import run_bound

        session, device_type, device_id, slots, second, image, expected = amd_one_slot()
        (found,) = run_bound(second, "x", ["y"], bound_tensor(session, image, slots, device_type, device_id))
        equal = found.tobytes() == expected.tobytes()
        others = [other for other in (0, 1, 2) if other != device_id]
        raised = 0
        for other in others:  # a binding to an other device id must raise, never read an other adapter
            try:
                run_bound(second, "x", ["y"], bound_tensor(session, image, slots, device_type, other))
            except Exception:  # noqa: BLE001 - the expected refusal
                raised += 1
        numbers = {"bound_device_id": device_id, "bound_equal_host": int(equal), "other_ids": len(others), "other_ids_raise": raised,
                   "same_adapter": int(equal and raised == len(others))}
        return {"result": "record-only", "reason": "recorded", "numbers": numbers,
                "detail": f"adapter {amd_report().device_name}; the session selects the adapter by its ONNX Runtime EP device"}

    # --- pipeline ---

    def pipeline_run(execution_provider: str, preprocess: str, number: int = 0) -> dict:
        """One run of the built-in pipeline on `PIPELINE_FRAMES` JPEG frames: its outputs, warnings and span times. Cached."""
        key = (execution_provider, preprocess, number)
        if key in state:
            return state[key]
        from skellytracker.core.errors import EpRequestError, EpUnavailableError
        from skellytracker.core.eps.state import check_start
        from skellytracker.core.pipelines import Frame, get_pipeline, load_pipeline, start_pipeline

        if not get_pipeline(PIPELINE_KEY).available:
            raise _Stop("models_not_available", f"the ONNX files of {PIPELINE_KEY} are not on this system")
        try:
            check_start(execution_provider, device=device_of(execution_provider))
        except (EpRequestError, EpUnavailableError):
            raise _Stop("ep_not_present", f"the EP {execution_provider!r} is not installed or not usable") from None
        config = load_pipeline(PIPELINE_KEY)
        config = config.model_copy(update={"instrumentation": config.instrumentation.model_copy(update={"timing_spans": list(PIPELINE_SPANS)})})
        events: list[dict] = []
        outputs, arrays = [], []
        with start_pipeline(config, camera_ids=[0], running_mode="video", execution_provider=execution_provider,
                            device=device_of(execution_provider), preprocess=preprocess, timing_sink=events.append) as run:
            for i in range(PIPELINE_FRAMES):
                result = run.process(Frame(jpeg(picture(1280, 720, 40 + i), "422"), frame_index=i))
                boxes, points = result["boxes"], result["wholebody"]
                arrays.append(tuple(np.array(a, np.float64) for a in (boxes.xyxy, boxes.score, points.xy, points.score)))
                outputs.append(b"".join(np.ascontiguousarray(a).tobytes() for a in (boxes.xyxy, boxes.score, points.xy, points.score)))
            warnings = [{"code": w.code, "reason": str(w.details.get("reason")) if w.details.get("reason") is not None else None}
                        for w in run.warnings]
        spans: dict[str, list[float]] = {}
        for event in events:
            if "span" in event:
                spans.setdefault(f"{event['node_id']}.{event['span']}", []).append((event["end_ns"] - event["start_ns"]) / 1e6)
        providers = [item["stage_providers"]["preprocess"] for item in events[0]["nodes"] if item.get("stage_providers")]  # the header
        state[key] = {"outputs": outputs, "arrays": arrays, "warnings": warnings, "preprocess_providers": providers,
                      "medians_ms": {k: round(statistics.median(v), 3) for k, v in spans.items()}}
        return state[key]

    def no_frame_warning(execution_provider: str, preprocess: str) -> dict:
        found = pipeline_run(execution_provider, preprocess)
        bad = [w for w in found["warnings"] if w["code"] in PIPELINE_WARNINGS]
        return {**_passed(not bad, {"frames": PIPELINE_FRAMES}, "warning_given"), "warnings": found["warnings"]}

    def gpu_auto_vs_cpu() -> dict:
        gpu_report()
        auto, host = pipeline_run(gpu_ep, "auto"), pipeline_run(gpu_ep, "cpu")
        numbers = {f"auto.{k}_ms": v for k, v in auto["medians_ms"].items()} | {f"cpu.{k}_ms": v for k, v in host["medians_ms"].items()}
        return {"result": "record-only", "reason": "recorded", "numbers": numbers, "warnings": auto["warnings"] + host["warnings"]}

    def amd_preprocess_place(preprocess: str) -> dict:
        """`gpu` runs the graph of each node on the EP, `auto` the CPU preprocess (header `stage_providers`); neither gives a frame warning."""
        ep_name = amd_report().ep_name
        found = pipeline_run(amd_ep, preprocess)
        bad = [w for w in found["warnings"] if w["code"] in PIPELINE_WARNINGS]
        providers = found["preprocess_providers"]
        on_graph = sum(provider == ep_name for provider in providers)
        placed = on_graph == len(providers) if preprocess == "gpu" else all(provider is None for provider in providers)
        numbers = {"frames": PIPELINE_FRAMES, "nodes": len(providers), "nodes_on_graph": on_graph}
        return {**_passed(not bad and placed, numbers, "warning_given" if bad else "mismatch"), "warnings": found["warnings"]}

    def amd_gpu_vs_cpu() -> dict:
        amd_report()
        gpu, host = pipeline_run(amd_ep, "gpu"), pipeline_run(amd_ep, "cpu")
        names = ("box_px", "box_score", "point_px", "point_score")
        worst, presence = dict.fromkeys(names, 0.0), 0
        for found, expected in zip(gpu["arrays"], host["arrays"], strict=True):
            for name, a, b in zip(names, found, expected, strict=True):
                presence += int(np.count_nonzero(np.isnan(a) != np.isnan(b)))
                both = ~(np.isnan(a) | np.isnan(b))
                worst[name] = max(worst[name], float(np.abs(a - b)[both].max(initial=0.0)))
        present = [sum(int(np.count_nonzero(~np.isnan(arrays[k]))) for arrays in gpu["arrays"]) for k in (1, 3)]
        numbers = {f"max_{name}_diff": round(value, 6) for name, value in worst.items()} | {
            "presence_changes": presence, "frames": PIPELINE_FRAMES, "box_scores_present": present[0], "point_scores_present": present[1]}
        return {"result": "record-only", "reason": "recorded", "numbers": numbers, "warnings": gpu["warnings"] + host["warnings"]}

    def amd_repeat_equal() -> dict:
        amd_report()
        first, second = pipeline_run(amd_ep, "gpu"), pipeline_run(amd_ep, "gpu", 1)
        unequal = sum(a != b for a, b in zip(first["outputs"], second["outputs"], strict=True))
        return {**_passed(unequal == 0, {"frames": PIPELINE_FRAMES, "unequal": unequal}, "mismatch"), "warnings": second["warnings"]}

    def repeat_equal() -> dict:
        execution_provider = ep_key or "cpu"
        first, second = pipeline_run(execution_provider, "auto"), pipeline_run(execution_provider, "auto", 1)
        unequal = sum(a != b for a, b in zip(first["outputs"], second["outputs"], strict=True))
        return {**_passed(unequal == 0, {"frames": PIPELINE_FRAMES, "unequal": unequal}, "mismatch"), "warnings": second["warnings"]}

    checks: list[tuple[str, Callable[[], dict]]] = [
        *[(f"cpu_decode.{n}", lambda n=n: cpu_close(n)) for n in ("baseline_420", "baseline_422", "baseline_444", "progressive", "grayscale")],
        ("cpu_decode.no_dht", cpu_no_dht),
        *[(f"cpu_decode.rotation_{r}", lambda r=r: cpu_rotation(r)) for r in ROTATIONS],
        *[(f"cpu_decode.size_{w}x{h}", lambda n=f"size_{w}x{h}": cpu_close(n)) for w, h in SIZES],
        ("cpu_decode.no_soi_refused", cpu_no_soi),
        ("cpu_decode.truncated", cpu_truncated),
        *[(f"gpu_decode.{n}", lambda n=n: gpu_compare([source(n)[1]], [0]))
          for n in ("baseline_420", "baseline_422", "baseline_444", "progressive", "grayscale")],
        *[(f"gpu_decode.rotation_{r}", lambda r=r: gpu_compare([source("baseline_422")[1]], [r])) for r in ROTATIONS],
        *[(f"gpu_decode.size_{w}x{h}", lambda n=f"size_{w}x{h}": gpu_compare([source(n)[1]], [0])) for w, h in SIZES],
        *[(f"gpu_decode.batch_{c}", lambda c=c: gpu_batch(c)) for c in (1, 3, 6)],
        ("gpu_decode.no_dht_refused", lambda: gpu_must_refuse(without_dht(source("baseline_420")[1]))),
        ("gpu_decode.no_soi_refused", lambda: gpu_must_refuse(source("baseline_420")[1][2:])),
        ("gpu_decode.truncated_420", lambda: gpu_truncated("420")),
        ("gpu_decode.truncated_422", lambda: gpu_truncated("422")),
        *[(f"preprocess_graph.{n}{m}", lambda n=n, m=m: graph_check(n, bool(m), "cpu")) for n in SIDECARS for m in ("", "_mixed_sizes")],
        *[(f"preprocess_graph_ep.{n}{m}", lambda n=n, m=m: graph_check(n, bool(m), None)) for n in SIDECARS for m in ("", "_mixed_sizes")],
        ("preprocess_graph_ep.node_placement", lambda: node_placement(gpu_report)),
        ("preprocess_graph_ep.device_handover", handover),
        ("pipeline.cpu_preprocess_no_frame_warning", lambda: no_frame_warning(ep_key or "cpu", "cpu")),
        ("pipeline.cpu_ep_auto_no_frame_warning", lambda: no_frame_warning("cpu", "auto")),
        ("pipeline.gpu_auto_vs_cpu", gpu_auto_vs_cpu),
        ("pipeline.repeat_equal", repeat_equal),
        *[(f"preprocess_graph_amd_ep.{n}{m}", amd_scored(lambda n=n, m=m: graph_check(n, bool(m), amd_report().requested_ep)))
          for n in SIDECARS for m in ("", "_mixed_sizes")],
        ("preprocess_graph_amd_ep.rtmw_wholebody133_far_corner_roi",
         amd_scored(lambda: graph_check("rtmw_wholebody133", False, amd_report().requested_ep, far=True))),
        ("preprocess_graph_amd_ep.node_placement", amd_scored(lambda: node_placement(amd_report))),
        ("preprocess_graph_amd_ep.frame_upload", amd_scored(amd_upload)),
        ("preprocess_graph_amd_ep.device_handover", amd_scored(amd_handover)),
        ("preprocess_graph_amd_ep.output_binding_forms", amd_scored(amd_binding_forms)),
        ("preprocess_graph_amd_ep.device_mapping", amd_scored(amd_device_mapping)),
        ("pipeline_amd_ep.gpu_preprocess_no_frame_warning", amd_scored(lambda: amd_preprocess_place("gpu"))),
        ("pipeline_amd_ep.gpu_vs_cpu_preprocess", amd_scored(amd_gpu_vs_cpu)),
        ("pipeline_amd_ep.auto_cpu_preprocess_no_warning", amd_scored(lambda: amd_preprocess_place("auto"))),
        ("pipeline_amd_ep.repeat_equal", amd_scored(amd_repeat_equal)),
    ]
    if quick:
        checks = [(QUICK_CHECKS[name], check) for name, check in checks if name in QUICK_CHECKS]
    try:
        facts = None if quick else _facts(ep_key)
        results = [_run_check(name, check, progress) for name, check in checks]
    finally:
        if state.get("decoder") is not None:
            state["decoder"].close()
    if facts is not None:
        report = state.get(f"report:{gpu_ep or amd_ep}")
        facts["device"] = None if report is None else {"device_key": report.device_key, "device_name": report.device_name}
    return {"schema": SCHEMA, "ep_key": ep_key, "facts": facts, "checks": results}


def _passed(ok: bool, numbers: dict, fail_reason: str = "over_limit") -> dict:
    return {"result": "pass" if ok else "fail", "reason": "ok" if ok else fail_reason, "numbers": numbers}


def _error_text(error: BaseException) -> str:
    """The exception type and its first 300 characters of message, with each absolute path and the home folder removed."""
    from skellytracker.core._hardware.sanitize import sanitize_text

    return _PATH.sub("<path>", sanitize_text(f"{type(error).__name__}: {error}"))[:300]


def _run_check(name: str, check: Callable[[], dict], progress: Callable[[str], None] | None) -> dict:
    if progress is not None:
        progress(name)
    try:
        found = check()
    except _Stop as stop:
        found = {"result": stop.result, "reason": stop.reason, "detail": stop.detail}
    except Exception as error:  # noqa: BLE001 - one check that raises must not stop the others
        found = {"result": "fail", "reason": "raised", "detail": _error_text(error)}
    return {"name": name, "result": found["result"], "reason": found["reason"], "numbers": found.get("numbers", {}),
            "warnings": found.get("warnings", []), "detail": found.get("detail", "")}


def _facts(ep_key: str | None) -> dict:
    """The machine facts of the run, with no path, host name, user name or serial number. A fact that raises is None."""
    import importlib.metadata

    def get(read: Callable[[], Any]) -> Any:
        try:
            return read()
        except Exception:  # noqa: BLE001 - a missing fact must not stop the run
            return None

    def host() -> dict:
        from skellytracker.core.system.host import probe_host

        info = probe_host()
        return {"os_name": info.os_name, "os_release": info.os_release, "os_version": info.os_version, "os_build": info.os_build,
                "arch": info.arch, "cpu_name": info.cpu_name, "cpu_logical_cores": info.cpu_logical_cores,
                "cpu_physical_cores": info.cpu_physical_cores,
                "gpus": [{"vendor": g.vendor, "name": g.name, "vram_total_bytes": g.vram_total_bytes, "driver_version": g.driver_version}
                         for g in info.gpus]}

    def ep() -> dict | None:
        from skellytracker.core.eps.catalog import load_catalog
        from skellytracker.core.eps.state import status

        row = next((row for row in status().eps if row.key == ep_key), None)
        if row is None:
            return None
        component = load_catalog().component(ep_key)
        versions = None
        if component is not None and row.jpeg_decoder == "installed":  # an installed component has the versions of the catalog
            versions = {component["package"]: component["version"]} | {w["package"]: w["version"] for w in component.get("dependency_wheels", ())}
        return {"key": row.key, "state": row.state, "pack_id": row.pack_id, "pack_version": row.pack_version,
                "jpeg_decoder": row.jpeg_decoder, "jpeg_decoder_versions": versions}

    def cv2_version() -> str:
        import cv2

        return cv2.__version__

    def numpy_version() -> str:
        import numpy

        return numpy.__version__

    def ort_version() -> str:
        from skellytracker.core.eps.installer import installed_ort  # `onnxruntime` or `onnxruntime-windowsml`

        return installed_ort()[1]

    return {
        "host": get(host),
        "ep": get(ep) if ep_key else None,
        "versions": {
            "python": platform.python_version(),
            "skellytracker": get(lambda: importlib.metadata.version("skellytracker")),
            "onnxruntime": get(ort_version),
            "onnx": get(lambda: importlib.metadata.version("onnx")),
            "opencv": get(cv2_version),
            "numpy": get(numpy_version),
        },
    }
