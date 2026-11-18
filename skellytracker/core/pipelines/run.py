"""The run API of a pipeline: `start_pipeline` gives a `PipelineRun`.

Implements: pipeline.running

    config = load_pipeline("yolox-rtmw-wholebody@skellytracker")
    with start_pipeline(config, camera_ids=[0], running_mode="video", execution_provider="cpu") as run:
        run.output_schema                           # the schema of each output, before frame 0
        result = run.process(Frame(image, frame_index=0))
        result["wholebody"]                         # a `CanonicalKeypoints` value
        result["boxes"]                             # an `OutputBoxes` value, with `xyxy` and `detector_ran`
        result["node_ran"]                          # node id -> bool, for each inference node
        run.models                                  # node id -> the model and what it runs on

`run.models` has one item for each `onnx_model` node, with `key`, `version`, `sidecar_sha256`,
`size`, `precision`, `execution_provider`, `device` and `cpu_threads`. `execution_provider` is the
EP key that the session uses. `device` is the device key of its GPU, or None. For a node with a
session on each of two or more GPUs, `device` is the list of the device keys in the order of the
GPUs of the run. `cpu_threads` is the intra-op thread count of a session on the CPU EP `cpu`, else
None. A node that does not run has `execution_provider`, `device` and `cpu_threads` None. An
application reads what a model runs on from these items.

The result of a camera holds `image_width` and `image_height`, ints in pixels. It has no
`image_size`, and no alias for it.

A plain import of this module loads no `onnxruntime` and no `mediapipe`.
"""
from __future__ import annotations

import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from skellytracker.core.errors import RunClosedError, VRAMExhaustionError
from skellytracker.core.pipelines._runtime.executor import Executor
from skellytracker.core.pipelines._runtime.resolve import ResolvedPipeline, resolve
from skellytracker.core.pipelines.config import PipelineConfig
from skellytracker.core.pipelines.warnings import PipelineWarning

CameraId = str | int


@dataclass(frozen=True)
class Frame:
    """One frame of one camera for one call.

    `image` is the host frame (BGR, uint8, `(H, W, 3)`) or the bytes of one JPEG image (`bytes` or
    `bytearray`). The run decodes a JPEG buffer on the CPU before the first node, with no EXIF
    orientation. It turns the decoded frame, or a decoded array, clockwise by `rotation_deg`: 0, 90,
    180 or 270, and None means 0. It does not change the array of the caller. A `rotation_deg` that
    is not one of these refuses the call (`V-pipeline.running-13`), and so does a JPEG buffer that
    the run cannot decode (`V-pipeline.running-12`). `timestamp_ms` is the time of the frame in
    milliseconds. The running mode `live` needs it. In `video`, a camera gives it on each frame or
    on none. The running mode `image` does not use it.
    """

    image: np.ndarray | bytes | bytearray
    frame_index: int
    timestamp_ms: float | int | None = None
    rotation_deg: int | float | None = None


class PipelineRun:
    """One run of a pipeline. `start_pipeline` makes it. Call `close()`, or use the run in a `with` statement.

    Thread rules (pipeline.running, Behaviour item 12):

    - Each run has one lock. `process`, `process_batch`, `set_params` and `close` take it. The
      calls on one run are thus serial: a second call waits for the first call.
    - `start_pipeline` can run on one thread, and `process` on an other thread.
    - Two runs share no state. Two threads can call two runs at the same time, also when the two
      runs have MediaPipe nodes.
    - `close()` from an other thread waits for the call that runs. Then it frees the sessions and
      the MediaPipe runners. A later call raises `RunClosedError`. A second `close()` does nothing.
    - There is no cancel: a call that started runs to its end.
    - The warning receiver `on_warning` gets each warning from the thread that makes the call.
    """

    def __init__(self, executor: Executor) -> None:
        self._executor = executor
        self._lock = threading.RLock()

    @property
    def output_schema(self) -> dict[str, dict[str, Any]]:
        """The schema of each output: output name -> the fields of pipeline.outputs. It is known before frame 0."""
        return self._executor.resolved.output_schema

    @property
    def warnings(self) -> tuple[PipelineWarning, ...]:
        """Each warning of the run: the load warnings, the start warnings and the later warnings."""
        return tuple(self._executor.warnings)

    @property
    def camera_ids(self) -> tuple[CameraId, ...]:
        return tuple(self._executor.camera_ids)

    @property
    def running_mode(self) -> str:
        return self._executor.running_mode

    @property
    def models(self) -> dict[str, dict[str, Any]]:
        """The run metadata of each `onnx_model` node: node id -> what the node runs, and what it runs on.

        - `key`, `version`, `sidecar_sha256`: the catalog entry of the model.
        - `size`, `precision`: the size and the precision of the artifact that runs.
        - `execution_provider`: the EP key that the session of the node uses.
        - `device`: the device key of the GPU of the session, or None for an EP with no device key.
          For a node with a session on each of two or more GPUs, it is the list of the device keys,
          in the order of the GPUs of the run.
        - `cpu_threads`: the intra-op thread count of the session on the CPU EP `cpu`, or None for
          an other EP.

        A node that does not run, because a `replay` tap gives its ports, has no session: its
        `execution_provider`, its `device` and its `cpu_threads` are None. The values do not change
        during the run.
        """
        executor, found = self._executor, {}
        for node in executor.resolved.nodes.values():
            if node.model is None:
                continue
            reports = executor.reports.get(node.id, [])
            devices = [report.device_key for report in reports]
            found[node.id] = {
                "key": node.model.key, "version": node.model.version, "sidecar_sha256": node.model.sidecar_sha256,
                "size": node.model.size, "precision": executor.plans[node.id].precision,
                "execution_provider": reports[0].used_ep if reports else None,
                "device": devices if len(devices) > 1 else next(iter(devices), None),
                "cpu_threads": reports[0].cpu_threads if reports else None,
            }
        return found

    def process_batch(self, frames: Mapping[CameraId, Frame]) -> dict[CameraId, dict[str, Any]]:
        """Run one call. Return the result of each camera of the call.

        In `video` and `image`, `frames` must hold one frame for each camera id of the run. In
        `live`, it holds a frame for one or more camera ids. The result of a camera holds one value
        for each output name, and `frame_index`, `image_width` and `image_height` (ints, in pixels), `timestamp_ms` and
        `node_ran`. A call that breaks a rule of the call raises `CallRefusedError`: it changes no
        state, and the run accepts the next call. A session that runs out of memory raises
        `VRAMExhaustionError`: the run does not retry the call and does not change the batch. It
        closes the run, so each later call raises `RunClosedError`.
        """
        with self._lock:
            self._check_open()
            return self._process(frames)

    def process(self, frame: Frame) -> dict[str, Any]:
        """Run one call of a run with one camera. Return the result of that camera."""
        with self._lock:
            self._check_open()
            if len(self._executor.camera_ids) != 1:
                raise ValueError(f"process() is for a run with one camera; this run has {len(self._executor.camera_ids)}. Use process_batch().")
            camera_id = self._executor.camera_ids[0]
            return self._process({camera_id: frame})[camera_id]

    def set_params(self, node_id: str, params: Mapping[str, Any]) -> None:
        """Set params of one node. Only a param with the mark `set_during_run` can change.

        The run takes the call in each running mode before the first `process` or `process_batch`
        call. After that call, it takes it only in `live`, and only with no `record` tap. A change
        applies from the next call, to each camera. It resets no node state. A refused call raises
        `SetParamsRefusedError` and changes no param.
        """
        with self._lock:
            self._check_open()
            self._executor.set_params(node_id, params)

    def close(self) -> None:
        """Wait for the call that runs, then free the sessions and the MediaPipe runners. A second call does nothing."""
        with self._lock:
            self._executor.close()

    def _process(self, frames: Mapping[CameraId, Frame]) -> dict[CameraId, dict[str, Any]]:
        try:
            return self._executor.process(frames)
        except VRAMExhaustionError:
            self._executor.close()  # no retry and no smaller batch: the run is closed
            raise

    def _check_open(self) -> None:
        if self._executor.closed:
            raise RunClosedError("the pipeline run is closed")

    def __enter__(self) -> PipelineRun:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _start(
    source: PipelineConfig | ResolvedPipeline, *, user_root: Path | str | None = None, image_ids: Sequence[int] | None = None, **parameters: Any,
) -> PipelineRun:
    """Start a run. `image_ids` gives the COCO input form: one camera, and the frame `k` is the image `image_ids[k]`."""
    resolved = source if isinstance(source, ResolvedPipeline) else resolve(source, user_root)
    return PipelineRun(Executor(resolved, image_ids=image_ids, **parameters))


def start_pipeline(
    config: PipelineConfig,
    *,
    camera_ids: Sequence[CameraId],
    running_mode: str,
    execution_provider: str | None = None,
    ep_options: Mapping[str, str] | None = None,
    device: str | Sequence[str] | None = None,
    vram_reserve_bytes: int = 2**30,
    fps: float | int = 30.0,
    cpu_threads: int | None = None,
    preprocess: str = "auto",
    timing_sink: Any = None,
    timing: str = "on",
    tap_dir: str | Path | None = None,
    on_warning: Callable[[PipelineWarning], None] | None = None,
    user_root: Path | str | None = None,
) -> PipelineRun:
    """Start a run of `config` and return it. Each start check runs before frame 0.

    - `camera_ids`: the ids of the cameras, unique. The running mode `image` has one camera.
    - `running_mode`: `image`, `video` or `live`.
    - `execution_provider`, `ep_options`: the EP key and its options for each `onnx_model` node
      with no `execution_provider`. A pipeline with no `onnx_model` node takes no EP.
    - `device`: one GPU key or a list of GPU keys. With None, the run uses each GPU that the EP can use.
    - `vram_reserve_bytes`: the VRAM that the run leaves free on each GPU.
    - `fps`: only in `video`, for a camera that gives no `timestamp_ms`.
    - `cpu_threads`: the intra-op thread count of each session on the CPU EP `cpu`. With None, it
      is half of the physical cores of the host, at least 1, so that the run leaves cores free for
      the camera capture and the application. A session of a GPU pack uses one thread and ignores
      it. A `mediapipe_tasks` node does not use it. `run.models` gives the applied count.
    - `preprocess`: the place of the preprocess, `auto`, `cpu` or `gpu`. `auto` uses the GPU
      preprocess on the confirmed EPs `cuda` and `trt-rtx`, and the CPU preprocess on each other EP.
      `cpu` does the frame work on the CPU on each EP, for a benchmark of the CPU path against the
      GPU path: each JPEG buffer decodes on the CPU, no frame uploads, and each `onnx_model` node
      uses the CPU preprocess. Only the model runs on the EP. The run then gives no warning
      `preprocessed_on_cpu` and no warning `jpeg_decoded_on_cpu`. `gpu` uses the GPU preprocess on
      each EP that has it, also an EP that is not confirmed yet, for a certification run. On an EP
      with no GPU preprocess, the node uses the CPU preprocess and the run gives the warning
      `preprocessed_on_cpu` with the reason `ep_not_wired` at the start.
    - `timing_sink`, `timing`: a path, an open text file or a callable for the timing lines, and `on` or `off`.
    - `tap_dir`: the folder of the taps.
    - `on_warning`: a callable that gets each `PipelineWarning` one time.
    - `user_root`: the user root of the model files.

    Raise `ValueError` for a config or a parameter that fails a rule, with the rule ID in the
    message. Raise `MissingDependencyError` for an extra or an ONNX file that is absent. The errors
    of `eps` pass through: `EpRequestError`, `EpUnavailableError`, `SessionCreationError` and
    `VRAMExhaustionError`. A call of the run can also raise `VRAMExhaustionError`: the run is then
    closed.
    """
    return _start(
        config, user_root=user_root, camera_ids=camera_ids, running_mode=running_mode, execution_provider=execution_provider,
        ep_options=ep_options, device=device, vram_reserve_bytes=vram_reserve_bytes, fps=fps, cpu_threads=cpu_threads, preprocess=preprocess, timing_sink=timing_sink,
        timing=timing, tap_dir=tap_dir, on_warning=on_warning,
    )


__all__ = ["Frame", "PipelineRun", "start_pipeline"]
