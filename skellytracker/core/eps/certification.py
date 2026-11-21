"""The children and the helpers of the session checks of `skellytracker.certify()` (`skellytracker/certification.py`).

Each check runs in its own `spawn` child process, so an EP that ends or hangs its process gives a result. The
test frames are a file of the package (`frames_record()`). This module downloads nothing. A failure is a fixed
reason code, because an error text can hold a path.
"""

import hashlib
import importlib.resources
import io
import os
import statistics
import time
import zipfile
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

from skellytracker.core.eps import gate, store, verification
from skellytracker.core.eps.gate import local_result, pair_key  # noqa: F401 - their old home; callers read them here

PARTIAL_PLACEMENT = "ep_partial_placement"  # the warning code of the pipeline runtime; `_runtime` is private
SCORE_MARGIN = 0.1  # not calibrated: fp16 noise near `score_min` must not fail a good EP
SIMILAR_SPEED = 0.2  # `similar`: the warm call on the EP is within 20 % of the warm call on the CPU EP
WARMUP_CALLS, TIMED_CALLS = 10, 100  # the calls of `time_run()`: the warm-up calls, and then the timed calls
TIMING_TIMEOUT_SECONDS = 900.0  # not calibrated: the start of the child, a pipeline start with an engine build on each camera, 110 calls
WIDE_TIMEOUT_SECONDS = 600.0  # not calibrated: the start of the child, two pipeline starts with a TensorRT RTX engine build, two calls
FRAMES = 30  # the test frames of one run of `session_frames()`: `count` of `frames_record()`; a test checks it
MEDIAPIPE_PIPELINE = "mediapipe-holistic-tasks@skellytracker"  # the pipeline of the check `mediapipe:smoke` (ADR-X7WD item 11)


class FramesUnavailableError(RuntimeError):
    """The test frames file is absent, or its sha256 or its count is wrong."""


def reports_dir() -> Path:
    return store.store_root() / "reports"


def speed_against_cpu(ep_ms: float, cpu_ms: float) -> str:
    """`faster`, `slower` or `similar` (within `SIMILAR_SPEED` of the CPU time). It is a record only: it never fails an EP."""
    if abs(ep_ms - cpu_ms) <= SIMILAR_SPEED * cpu_ms:
        return "similar"
    return "faster" if ep_ms < cpu_ms else "slower"


def compare_results(cpu: dict, ep: dict, thresholds: dict, *, keypoints: bool = True) -> dict:
    """Compare the pipeline result of the EP with the result of the CPU EP on one image.

    With `keypoints` false, only the people, the finite outputs and the box IoU can fail: the lighter rule of a
    later frame of `<label>:video` (ADR-R0EB item 3). The keypoint values then stay in the result as a record.

    The rule: the same count of present rows, at least one; each box IoU at least `box_iou_min`;
    no NaN in the EP result where the CPU result is finite; each point with a CPU score of
    `score_min` or more has an EP score of `score_min - SCORE_MARGIN` or more; each point with a
    score of `score_min` or more in the two results within `keypoint_box_fraction_max` of the diagonal
    of the CPU box of its row. The limit is a part of the box size, because the decode step of a
    keypoint model has a pixel size that grows with the person. The result holds the worst values
    and a reason code.
    """
    import numpy as np

    found = {"people_cpu": int(cpu["boxes"].present.sum()), "people_ep": int(ep["boxes"].present.sum()),
             "box_iou_min": None, "keypoint_px_max": None, "keypoint_box_fraction_max": None,
             "keypoint_box_fraction_median": None, "keypoint_box_fraction_p99": None, "points_compared": 0,
             "ok": False, "reason_code": None}
    present = cpu["boxes"].present
    if found["people_cpu"] == 0:
        return {**found, "reason_code": "no-person-on-cpu"}
    if not np.array_equal(present, ep["boxes"].present) or not np.array_equal(cpu["wholebody"].present, ep["wholebody"].present):
        return {**found, "reason_code": "people-differ"}
    a, b = cpu["boxes"].xyxy[present], ep["boxes"].xyxy[present]
    overlap = np.clip(np.minimum(a[:, 2:], b[:, 2:]) - np.maximum(a[:, :2], b[:, :2]), 0, None).prod(axis=1)
    union = (a[:, 2:] - a[:, :2]).prod(axis=1) + (b[:, 2:] - b[:, :2]).prod(axis=1) - overlap
    found["box_iou_min"] = float((overlap / union).min())
    rows = cpu["wholebody"].present
    cpu_score, ep_score = cpu["wholebody"].score[rows], ep["wholebody"].score[rows]
    cpu_xy, ep_xy = cpu["wholebody"].xy[rows], ep["wholebody"].xy[rows]
    lost = (np.isfinite(cpu_score) & ~np.isfinite(ep_score)).any() or (np.isfinite(cpu_xy) & ~np.isfinite(ep_xy)).any()
    both = (cpu_score >= thresholds["score_min"]) & (ep_score >= thresholds["score_min"])
    distance = np.linalg.norm(cpu_xy - ep_xy, axis=-1)
    fraction = (distance / np.hypot(*(cpu["boxes"].xyxy[rows, 2:] - cpu["boxes"].xyxy[rows, :2]).T)[:, None])[both]
    distance = distance[both]
    found["points_compared"] = int(both.sum())
    found["keypoint_px_max"] = float(distance.max()) if distance.size else None
    found["keypoint_box_fraction_max"] = float(fraction.max()) if distance.size else None
    found["keypoint_box_fraction_median"] = float(np.median(fraction)) if distance.size else None
    found["keypoint_box_fraction_p99"] = float(np.percentile(fraction, 99)) if distance.size else None
    if lost or not np.isfinite(found["box_iou_min"]) or (distance.size and not np.isfinite(distance).all()):
        return {**found, "reason_code": "not-finite"}
    if found["box_iou_min"] < thresholds["box_iou_min"]:
        return {**found, "reason_code": "box-differs"}
    if not keypoints:
        return {**found, "ok": True}
    if ((cpu_score >= thresholds["score_min"]) & (ep_score < thresholds["score_min"] - SCORE_MARGIN)).any():
        return {**found, "reason_code": "scores-differ"}
    if not distance.size:
        return {**found, "reason_code": "no-point-to-compare"}
    if not found["keypoint_box_fraction_max"] <= thresholds["keypoint_box_fraction_max"]:
        return {**found, "reason_code": "keypoints-differ"}
    return {**found, "ok": True}


def frames_record(test_media_dir: str | os.PathLike | None = None) -> dict:
    """The record of the test frames file: `path`, `sha256`, `bytes` and `count` (`model_zoo/test_media/quick_frames.yaml`).

    `dir` is `test_media_dir` as a string, or None for the file of the package.
    """
    import yaml

    record = yaml.safe_load((importlib.resources.files("skellytracker.core") / "model_zoo" / "test_media" / "quick_frames.yaml").read_text(encoding="utf-8"))
    return {**record, "dir": None if test_media_dir is None else os.fspath(test_media_dir)}


def frames_file(settings: dict) -> bytes:
    """The bytes of the test frames file of `settings["frames"]` (`frames_record()`). It downloads nothing.

    With no `dir`, the file is a file of the package, and `path` is relative to `skellytracker/core/model_zoo/`. With
    `dir`, the file is `<sha256>.zip` in that folder: the name rule of the test media folder of the format of
    `skellycertify` (section 2.8). It raises `FramesUnavailableError` when the file is absent or its sha256 is not the
    sha256 of the record.
    """
    item = settings["frames"]
    folder = item.get("dir")
    try:
        data = ((importlib.resources.files("skellytracker.core") / "model_zoo" / item["path"]) if folder is None
                else Path(folder) / f"{item['sha256']}{Path(item['path']).suffix}").read_bytes()
    except OSError as error:
        raise FramesUnavailableError("the test frames file is absent") from error
    if hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise FramesUnavailableError("the test frames file has a wrong sha256")
    return data


def frame_jpegs(settings: dict) -> list[bytes]:
    """The JPEG bytes of each test frame of `frames_record()`, in the order of their names. It checks the file first (`frames_file()`)."""
    with zipfile.ZipFile(io.BytesIO(frames_file(settings))) as archive:
        frames = [archive.read(name) for name in sorted(archive.namelist())]
    if len(frames) != settings["frames"]["count"]:
        raise FramesUnavailableError("the test frames file does not hold the frames of the record")
    return frames


def quick_frames(settings: dict) -> list:
    """The decoded test frames of `frame_jpegs()`."""
    import cv2
    import numpy as np

    frames = [cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR) for data in frame_jpegs(settings)]
    if any(frame is None for frame in frames):
        raise FramesUnavailableError("the test frames file does not hold the frames of the record")
    return frames


def _process_vram(sampler, pid: int) -> int | None:
    """The VRAM bytes of this process: Windows PDH, or NVML per process on Linux; None when no reader gives it."""
    sample = sampler.sample([pid])
    values = [p.vram_used_bytes for p in sample.processes if p.pid == pid]
    values += [row.vram_used_bytes for gpu in sample.gpus for row in (gpu.processes or ()) if row.pid == pid]
    values = [value for value in values if value is not None]
    return max(values) if values else None


def time_run(pipeline, execution_provider: str, cameras: int, image, device: str | None = None) -> dict:
    """Start the pipeline on `cameras` cameras in the running mode `video`, and time `TIMED_CALLS` calls after `WARMUP_CALLS` calls.

    `pipeline` is a key of the pipeline catalog or the mapping of a config. The times are of the span
    `pipeline.run`. `start_seconds` holds the start of the sessions, with an engine build. The VRAM values are
    of this process, in MiB, from a sample after each call. They are None when no reader gives the value.
    """
    from skellytracker.core import pipelines
    from skellytracker.core.metrics import LiveSampler
    from skellytracker.core.pipelines.timing import duration_ms

    def mib(value: int | None) -> int | None:
        return None if value is None else round(value / 2**20)

    config = pipelines.load_pipeline(pipeline)
    config.instrumentation.timing_spans = ["pipeline.run"]
    events, sampler, pid, ids = [], LiveSampler(), os.getpid(), list(range(cameras))
    before = _process_vram(sampler, pid)
    peak = before
    started = time.perf_counter()
    with pipelines.start_pipeline(config, camera_ids=ids, running_mode="video", execution_provider=execution_provider,
                                  timing_sink=events.append, device=device) as run:
        start_seconds = time.perf_counter() - started
        for index in range(WARMUP_CALLS + TIMED_CALLS):
            run.process_batch({camera: pipelines.Frame(image, frame_index=index) for camera in ids})
            # shortcut: a sample after each call, not during it; the ONNX Runtime arenas keep their peak, so it is close
            now = _process_vram(sampler, pid)
            peak = now if peak is None else max(peak, now or 0)
    calls = [duration_ms(event) for event in events if event.get("node_id") == "pipeline"]
    timed = sorted(calls[WARMUP_CALLS:])
    return {"cameras": cameras, "start_seconds": round(start_seconds, 2), "first_call_ms": round(calls[0], 1),
            "calls": len(timed), "median_ms": round(statistics.median(timed), 2),
            "p95_ms": round(timed[min(len(timed) - 1, round(0.95 * (len(timed) - 1)))], 2),
            "vram_before_mib": mib(before), "peak_vram_mib": mib(peak)}


def _timing_child(key: str, settings: dict, cameras: int, device_key: str | None, connection) -> None:
    """The child of `timing_run()`: it sends the result of `time_run()`, or `{"error": <exception class name>}`."""
    try:
        with gate.certification_run():  # the level `full` times an EP that can have no result yet
            result = time_run(settings["pipeline"], key, cameras, quick_frames(settings)[0], device_key)
    except Exception as error:  # noqa: BLE001 - a fixed code: an error text can hold a path
        result = {"error": type(error).__name__}
    connection.send(result)
    connection.close()


def timing_run(key: str, settings: dict, cameras: int, device_key: str | None = None, *,
               cancel=None, timeout: float = TIMING_TIMEOUT_SECONDS) -> tuple:
    """Run `time_run()` on the EP `key` in a `spawn` child, and give `(result, problem, exit_code)` of `spawn_child()`."""
    return verification.spawn_child(_timing_child, (key, settings, cameras, device_key), timeout=timeout, cancel=cancel)


def session_frames(pipeline, execution_provider: str, images: list, running_mode: str, device: str | None = None) -> dict:
    """Start the pipeline on one camera in the running mode `video` or `live`, and run each image of `images` in order.

    `images` are the decoded test frames (`quick_frames()`). A frame of `live` has a rising `timestamp_ms`. `frames` holds, for each frame, the outputs that `compare_results()`
    reads, as plain arrays, so that a child can send them. `ms` is the fastest call after the first: a rough figure,
    a record only.
    """
    import numpy as np

    from skellytracker.core import pipelines

    config = pipelines.load_pipeline(pipeline)
    frames, times = [], []
    with pipelines.start_pipeline(config, camera_ids=[0], running_mode=running_mode, execution_provider=execution_provider,
                                  timing="off", device=device) as run:
        for index, image in enumerate(images):
            before = time.perf_counter()
            found = run.process(pipelines.Frame(image, frame_index=index, timestamp_ms=index * 33.0 if running_mode == "live" else None))
            times.append((time.perf_counter() - before) * 1000)
            boxes, body = found["boxes"], found["wholebody"]
            frames.append({"boxes": SimpleNamespace(present=np.array(boxes.present), xyxy=np.array(boxes.xyxy)),
                           "wholebody": SimpleNamespace(present=np.array(body.present), score=np.array(body.score), xy=np.array(body.xy))})
        models, warnings = run.models, sorted({warning.code for warning in run.warnings})
    return {"frames": frames, "ms": round(min(times[1:]), 1), "warnings": warnings,
            "models": [{field: model[field] for field in ("key", "version", "size", "precision", "execution_provider", "device")}
                       for _, model in sorted(models.items())]}


def _session_child(key: str, settings: dict, device_key: str | None, modes: tuple, connection) -> None:
    """The child of `session_run()`: it sends each running mode as a step, then `{mode: <session_frames()>}`.

    An error in one mode gives `{"error": <exception class name>}` for that mode. An error before the first mode, for
    example a test frames file that is not valid, gives it for the whole result.
    """
    try:
        with gate.certification_run():  # the check runs the EP before the EP has a result
            images, result = quick_frames(settings), {}
            for mode in modes:
                connection.send(mode)
                try:
                    result[mode] = session_frames(settings["pipeline"], key, images, mode, device_key)
                except Exception as error:  # noqa: BLE001 - a fixed code: an error text can hold a path
                    result[mode] = {"error": type(error).__name__}
    except Exception as error:  # noqa: BLE001 - a fixed code: an error text can hold a path
        result = {"error": type(error).__name__}
    connection.send(result)
    connection.close()


def mediapipe_frames(images: list) -> dict:
    """Start the pipeline `MEDIAPIPE_PIPELINE` on one camera in the running mode `live`, and run each image in order.

    A frame has a rising `timestamp_ms`. `frames` holds `present`, `score` and `xy` of the output `holistic` of each
    frame, as plain arrays, so that a child can send them. The pipeline has no ONNX model, so the run takes no EP.
    """
    import numpy as np

    from skellytracker.core import pipelines

    frames = []
    with pipelines.start_pipeline(pipelines.load_pipeline(MEDIAPIPE_PIPELINE), camera_ids=[0], running_mode="live", timing="off") as run:
        for index, image in enumerate(images):
            found = run.process(pipelines.Frame(image, frame_index=index, timestamp_ms=index * 33.0))["holistic"]
            frames.append(SimpleNamespace(present=np.array(found.present), score=np.array(found.score), xy=np.array(found.xy)))
    return {"frames": frames}


def _mediapipe_child(settings: dict, connection) -> None:
    """The child of `mediapipe_run()`: it sends `{"live": <mediapipe_frames()>}`, with the result shape of `_session_child()`.

    A model file that is not in the cache gives `{"error": "models-missing"}`: `certify()` downloads nothing.
    """
    try:
        from skellytracker.core.detectors.keypoint_detectors.mediapipe import mediapipe_model_manager as assets

        images = quick_frames(settings)
        if not assets.cached_model_path(assets.HOLISTIC_MODEL_URL).exists():
            result = {"error": "models-missing"}
        else:
            try:
                result = {"live": mediapipe_frames(images)}
            except Exception as error:  # noqa: BLE001 - a fixed code: an error text can hold a path
                result = {"live": {"error": type(error).__name__}}
    except Exception as error:  # noqa: BLE001 - a fixed code: an error text can hold a path
        result = {"error": type(error).__name__}
    connection.send(result)
    connection.close()


def mediapipe_run(settings: dict, *, cancel=None, timeout: float = WIDE_TIMEOUT_SECONDS) -> tuple:
    """Run `mediapipe_frames()` on the test frames in a `spawn` child, and give `(result, problem, exit_code)` of `spawn_child()`."""
    return verification.spawn_child(_mediapipe_child, (settings,), timeout=timeout, cancel=cancel)


def session_run(key: str, settings: dict, modes: tuple, device_key: str | None = None, *, cancel=None,
                progress: Callable[[str], None] | None = None, timeout: float = WIDE_TIMEOUT_SECONDS) -> tuple:
    """Run `session_frames()` for each running mode of `modes` on the EP `key` in one `spawn` child.

    It gives `(result, problem, exit_code)` of `spawn_child()`. `progress` gets the name of each mode when it starts.
    """
    return verification.spawn_child(_session_child, (key, settings, device_key, tuple(modes)), timeout=timeout, cancel=cancel,
                                    progress=progress)
