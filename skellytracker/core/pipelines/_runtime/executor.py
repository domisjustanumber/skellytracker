"""The executor of one pipeline run: the start checks, one call, the params during a run and the close.

Implements: pipeline.running
Implements: pipeline.graph
Implements: pipeline.outputs
Implements: pipeline.timing

The executor has no lock. `PipelineRun` of `core/pipelines/run.py` makes its calls serial.

One call runs each node in the same-frame order. An inference node runs one time for the cameras
of the call. A glue node runs for each camera. A call commits the new node states and the new
`@prev` values of its cameras only when each node ran: a refused call changes nothing.
"""
from __future__ import annotations

import concurrent.futures
import functools
import logging
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from skellytracker.core._hardware.sanitize import sanitize_text
from skellytracker.core.decode import cpu
from skellytracker.core.decode.frame import DecodedFrame
from skellytracker.core.eps import session as eps_session
from skellytracker.core.eps.session import cpu_thread_count
from skellytracker.core.errors import CallRefusedError, EpRequestError, SetParamsRefusedError
from skellytracker.core.pipelines import timing as timing_module
from skellytracker.core.pipelines._runtime import mediapipe_tasks, onnx_model, sessions, taps
from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines._runtime.resolve import MODULES, ResolvedNode, ResolvedPipeline, resolve
from skellytracker.core.pipelines.config import BY_TYPE, FRAME, RESERVED_NODE_ID, PipelineConfig
from skellytracker.core.pipelines.canonical import to_canonical
from skellytracker.core.pipelines.loading import _union
from skellytracker.core.pipelines.values import PortInfo, is_empty, to_output_boxes
from skellytracker.core.pipelines.warnings import PipelineWarning

logger = logging.getLogger(__name__)

RUNNING_MODES = ("image", "video", "live")
INFERENCE_TYPES = ("onnx_model", "mediapipe_tasks")
TIMESTAMP_RULE = "V-node.smooth_keypoints-3"
BATCH_LIMITED_BY_STATE = "batch_limited_by_state"
JPEG_DECODED_ON_CPU = "jpeg_decoded_on_cpu"
JPEG_DECODER_EPS = frozenset({"cuda", "trt-rtx"})
"""The EPs of the GPU JPEG decoder. A test adds `cpu` and patches `open_jpeg_decoder` to run that path on the CPU EP."""
Port = tuple[str, str]


def open_jpeg_decoder(execution_provider: str, device_key: str | None, ep_device_id: Any) -> Any:
    """Open the GPU JPEG decoder of one device, or return None when the run must decode on the CPU. A test patches this seam."""
    from skellytracker.core.decode.nvidia import NvJpegDecoder

    return NvJpegDecoder.open(execution_provider, device_key, ep_device_id)


def decoder_missing_warning(execution_provider: str, cause: str | None = None) -> PipelineWarning:
    """The warning `jpeg_decoded_on_cpu` of a GPU JPEG decoder that does not open (pipeline.running, Behaviour item 8).

    `cause` is the text of the error of the open, or None when the open gave None (its log line gives the reason).
    """
    from skellytracker.core.eps import store
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.eps.recommendation import install_hint

    catalog = load_catalog()
    component, state = catalog.component(execution_provider), store.component_state(catalog, execution_provider)
    package = None if component is None else component["id"]
    hint = install_hint(execution_provider) if state in ("missing", "other_version") else None
    why = f"did not open: {cause or 'see the log'}" if state == "installed" else f"is {state or 'not available'}"
    message = f"the GPU JPEG decoder {package} of '{execution_provider}' {why}; the run decodes each JPEG buffer on the CPU"
    return PipelineWarning(JPEG_DECODED_ON_CPU, message + (f". {hint}" if hint else ""), (), {
        "reason": "decoder_unavailable", "package": package, "jpeg_decoder": state, "install_hint": hint, "cause": cause,
    })


def stored_jpeg_checks(execution_provider: str, device_key: str | None) -> dict[str, Any]:  # Any: beartype must not check a damaged value
    """The stored result of each JPEG check of the quick check of the EP on one GPU, for example `{"jpeg-decode": "fail"}` (Behaviour item 13).

    The row of the pair in `quick-checks.json` of the EP store. The read takes no store lock: the writer
    replaces the file in one step, and the lock would make the store folder. Each fault gives {}: a run
    never fails on it.
    """
    from skellytracker.core.eps import certification, store
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.system.host import gpu_device_keys, probe_host

    if device_key is None:
        return {}
    try:
        host = probe_host()  # the record of the start check of the run: no second probe
        pair = certification.pair_key(load_catalog(), execution_provider, dict(gpu_device_keys(host))[device_key], host.os_name)
        return dict(store.read_json(store.store_root() / "quick-checks.json")[pair]["jpeg"])
    except Exception:  # noqa: BLE001 - no file, no row, no `jpeg` or a damaged file: no stored result
        return {}


def _port(ref: str) -> Port:
    node_id, _, port = ref.partition(".")
    return node_id, port


def running_nodes(resolved: ResolvedPipeline, replayed: set[Port], recorded: Sequence[Port]) -> set[str]:
    """Return the nodes that run (pipeline.running, Behaviour item 9).

    A port is used when it is an output, an input of a node that runs, or the port of a `record`
    tap. A node runs when a used port of it is not replayed.
    """
    todo = [*map(_port, resolved.config.outputs.values()), *recorded]
    runs: set[str] = set()
    while todo:
        node_id, port = todo.pop()
        if node_id != FRAME and (node_id, port) not in replayed and node_id not in runs:
            runs.add(node_id)
            todo += [(item.node, item.port) for item in resolved.nodes[node_id].inputs]
    return runs


def deliver(info: PortInfo, value: Any, node_ran: Mapping[str, bool], user_root: Path) -> Any:
    """Return the delivered form of the value of an output port (pipeline.outputs, Behaviour item 6).

    A `keypoints` value gives its canonical form. A `boxes` value gives `OutputBoxes`, with the
    `node_ran` of its instance source as `detector_ran`.
    """
    if info.port_type == "keypoints":
        return to_canonical(value, info.groups, user_root=user_root)
    return to_output_boxes(value, node_ran[info.instance_source])


class Executor:
    """One run of a resolved pipeline. The constructor does each start check and builds the sessions."""

    def __init__(
        self,
        resolved: ResolvedPipeline,
        *,
        camera_ids: Sequence[str | int],
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
        image_ids: Sequence[int] | None = None,
    ) -> None:
        config = resolved.config
        self.resolved, self.config, self.running_mode = resolved, config, running_mode
        self.camera_ids = list(camera_ids)
        self.fps = float(fps)
        self.vram_reserve_bytes = vram_reserve_bytes
        self.preprocess = preprocess
        self.batch_k = 1  # k is 1 on each GPU in this version (pipeline.running, Behaviour item 4)
        self.on_warning = on_warning
        self.warnings: list[PipelineWarning] = []
        self.run_id = uuid.uuid4().hex
        self.image_ids = None if image_ids is None else [int(item) for item in image_ids]
        self.calls = 0
        self.port_values: dict[Any, dict[Port, Any]] = {}
        self.closed = False

        if running_mode not in RUNNING_MODES:
            raise ValueError(f"running_mode must be one of {list(RUNNING_MODES)}, not {running_mode!r}")
        if timing not in ("on", "off"):
            raise ValueError(f"timing must be 'on' or 'off', not {timing!r}")
        if preprocess not in ("auto", "cpu", "gpu"):
            raise ValueError(f"preprocess must be 'auto', 'cpu' or 'gpu', not {preprocess!r}")
        if not self.fps > 0:
            raise ValueError(f"fps must be more than 0, not {fps!r}")
        try:
            self.cpu_threads = cpu_thread_count(cpu_threads)
        except EpRequestError as error:
            raise ValueError(f"V-pipeline.running-11: {error}") from None
        if not self.camera_ids or len(set(self.camera_ids)) != len(self.camera_ids):
            raise ValueError(f"V-pipeline.running-1: camera_ids must be a non-empty list of unique ids, not {self.camera_ids!r}")
        if running_mode == "image" and len(self.camera_ids) != 1:
            raise ValueError(f"V-pipeline.running-1: the running mode `image` needs exactly one camera id, not {len(self.camera_ids)}")
        if self.image_ids is not None and len(self.camera_ids) != 1:
            raise ValueError("the COCO input form has one camera")
        sessions.check_run_ep(resolved, execution_provider)
        # (key, port, port facts) of each output: the result holds the delivered form of the port value.
        self.outputs = [(name, _port(ref), resolved.port_info(*_port(ref))) for name, ref in config.outputs.items()]

        # The taps, and the nodes that run.
        tap_list = list(config.instrumentation.taps)
        if tap_list and tap_dir is None:
            raise ValueError("V-pipeline.taps-2: the pipeline file has a tap, so the run must have a tap folder (tap_dir)")
        for tap in tap_list:
            taps.check_tap_port(tap, resolved.port_info(*_port(tap.port)))
        replay_list = [tap for tap in tap_list if tap.action == "replay"]
        record_list = [tap for tap in tap_list if tap.action == "record"]
        replayed = {_port(tap.port) for tap in replay_list}
        self.runs = running_nodes(resolved, replayed, [_port(tap.port) for tap in record_list])
        for node_id, port in sorted(replayed):
            if node_id in self.runs:
                raise ValueError(f"V-pipeline.running-5: the node {node_id} runs, but its output port {node_id}.{port} is replayed")
        self.order = [node_id for node_id in resolved.order if node_id in self.runs]
        self.inference_nodes = [node.id for node in config.nodes if node.type in INFERENCE_TYPES]
        self.params: dict[str, Any] = {node_id: node.node.params for node_id, node in resolved.nodes.items()}
        self.infos: dict[str, Any] = {node_id: node.infos for node_id, node in resolved.nodes.items()}
        self.prev_ports = sorted({(item.node, item.port) for node_id in self.order for item in resolved.nodes[node_id].inputs if item.prev})

        # The start checks of the models, and the devices.
        models = [node for node in resolved.nodes.values() if node.type == "onnx_model"]
        for node in models:
            if node.id in self.runs:
                onnx_model.check_runs(node)
        self.plans = {node.id: sessions.node_plan(node, execution_provider, ep_options) for node in models}
        sessions.check_dependencies(resolved, self.order, self.plans)
        running_plans = [self.plans[node_id] for node_id in self.order if node_id in self.plans]
        gpus = (sessions.run_gpus(running_plans, device) if running_plans else ())[: len(self.camera_ids)]
        self.devices = tuple(gpu.device_key for gpu in gpus) or (None,)
        weights = sessions.gpu_weights(gpus, vram_reserve_bytes) if len(gpus) > 1 else [None] * len(self.devices)
        self.device_of = sessions.split_cameras(self.camera_ids, weights)

        image_list = None if self.image_ids is None else timing_module.image_list_sha256(self.image_ids)
        self.sessions = sessions.RunSessions(self.cpu_threads)
        self.reports: dict[str, list[Any]] = {}  # node id -> the `SessionReport` of its session on each device
        self.models: dict[str, onnx_model.OnnxModelRunner] = {}
        self.states: dict[tuple[Any, str], Any] = {}
        self.prev: dict[Any, dict[Port, Any]] = {camera_id: {} for camera_id in self.camera_ids}
        self.last_timestamp: dict[Any, float | None] = dict.fromkeys(self.camera_ids)
        self.gives_timestamp: dict[Any, bool | None] = dict.fromkeys(self.camera_ids)
        self.records: list[tuple[taps.RecordTap, dict[str, Any]]] = []
        self.replays: dict[Port, taps.ReplayTap] = {}
        self.writer: timing_module.TimingWriter | None = None
        self.spans_on: frozenset[str] = frozenset()
        # The frame stage of the graph path: the upload device of each device index with a graph-on node, the
        # last frame size of each camera (its fixed slot), the zero frame of each (device index, size), and the
        # slots of the call.
        self.upload_devices: dict[int, tuple[Any, str]] = {}
        self.slot_sizes: dict[Any, tuple[int, int]] = {}
        self.zero_frames: dict[tuple[int, tuple[int, int]], Any] = {}
        self.call_slots: dict[int, onnx_model.CallSlots] = {}
        # The GPU JPEG decode: (EP, device key, CUDA device id) of each device index with a graph-on node on an EP of
        # `JPEG_DECODER_EPS`, the decoder of each device index after its first JPEG call (None: decode on the CPU), the
        # error text of an open that raised, and the keys of the `jpeg_decoded_on_cpu` warnings that the run gave.
        self.decoder_places: dict[int, tuple[str, str | None, Any]] = {}
        self.decoders: dict[int, Any] = {}
        self.open_errors: dict[int, str] = {}
        self.jpeg_warned: set[Any] = set()
        # the device indices where a stored quick check moves the JPEG decode to the CPU, and the warnings of the start
        self.decode_failed: set[int] = set()
        self.start_warnings: list[PipelineWarning] = []
        self.decode_pool: concurrent.futures.ThreadPoolExecutor | None = None  # the CPU JPEG decode, opened at the first call that uses it
        try:
            opened = self._open_sessions()
            self.reports = {node_id: [item.report for item in items] for node_id, items in opened.items()}
            for node_id in self.order:
                if resolved.nodes[node_id].type == "mediapipe_tasks":
                    for camera_id in self.camera_ids:
                        self.states[(camera_id, node_id)] = mediapipe_tasks.make_state(self.params[node_id], running_mode, node_id)
            items = self._node_items(opened)
            manifest = {
                tap.name: taps.make_manifest(
                    config, tap, resolved.port_info(*_port(tap.port)), run_id=self.run_id, node_items=items,
                    image_list_sha256=image_list, camera_ids=self.camera_ids, running_mode=running_mode,
                )
                for tap in tap_list
            }
            for tap in replay_list:
                facts = {
                    node_id: (items[node_id]["sidecar_sha256"], items[node_id]["artifact_sha256"], self.plans[node_id].execution_provider)
                    if node_id in self.plans else (None, None, None)
                    for node_id in taps.upstream_nodes(config, tap.port.split(".")[0])
                }
                self.replays[_port(tap.port)] = taps.ReplayTap(
                    tap, Path(tap_dir), resolved.port_info(*_port(tap.port)), manifest[tap.name], facts, self.image_ids,
                )
            for tap in record_list:
                self.records.append((taps.RecordTap(tap, Path(tap_dir), resolved.port_info(*_port(tap.port))), manifest[tap.name]))
            if timing == "on" and timing_sink is not None:
                self.writer = timing_module.TimingWriter(timing_sink)
                self.spans_on = frozenset(config.instrumentation.timing_spans)
                self.writer.write_header(timing_module.make_header(
                    config, run_id=self.run_id, running_mode=running_mode,
                    # `eps.build_session` does one warm-up run for each session (pipeline.timing, Fields)
                    warmup_passes=1 if opened else 0,
                    camera_ids=self.camera_ids, nodes=list(items.values()), image_list_sha256=image_list,
                ))
        except BaseException:
            self.close(write_taps=False)
            raise

        for warning in (*resolved.warnings, *self.sessions.partial_placement(), *self._not_wired(), *self.start_warnings):
            self._warn(warning)
        stateful = resolved.stateful_nodes(running_mode)
        if stateful and running_mode == "video":
            message = f"the pipeline is stateful (nodes: {', '.join(stateful)}): in `video` it runs at batch = camera count ({len(self.camera_ids)})"
            self._warn(PipelineWarning(BATCH_LIMITED_BY_STATE, message, tuple(stateful), {"batch": len(self.camera_ids)}))

    # ---- start ----------------------------------------------------------------------------

    def _warn(self, warning: PipelineWarning) -> None:
        """Add a warning to the list of the run, log it and give it to the warning receiver, one time."""
        self.warnings.append(warning)
        logger.warning("%s: %s", warning.code, warning.message)
        if self.on_warning is not None:
            self.on_warning(warning)

    def _open_sessions(self) -> dict[str, list[sessions.OpenedSession]]:
        """Build the sessions of each `onnx_model` node that runs: one for each device, at the batch of that device."""
        opened: dict[str, list[sessions.OpenedSession]] = {}
        for node_id in self.order:
            node = self.resolved.nodes[node_id]
            if node.type != "onnx_model":
                continue
            plan = self.plans[node_id]
            rows = node.inputs_info["boxes"].max_instances if node.model.kind == "top_down" else 1
            opened[node_id], places, slots = [], [], 0
            for index, device_key in enumerate(self.devices):
                cameras = sum(1 for slot in self.device_of.values() if slot == index)
                slots = max(slots, cameras)
                opened[node_id].append(self.sessions.open(node, plan, device_key, self.batch_k * cameras * rows))
                report = opened[node_id][-1].report
                # a DML session keeps its device memory under the device id 0 on each adapter: the session selects the adapter
                device_id = None if report.ep_name == sessions.DML_EP_NAME else report.ep_device_id
                places.append(onnx_model.GraphDevice(device_key, device_id, self.batch_k * cameras * rows))
            graph = None
            # the GPU preprocess (pipeline.running, Implementer guidance); with `preprocess="cpu"` no node has a graph, so no
            # frame uploads and no GPU JPEG decoder opens, and the run gives no warning of the CPU path (Behaviour item 14)
            graph_eps = {"auto": onnx_model.GRAPH_DEFAULT_EPS, "gpu": onnx_model.GRAPH_EPS, "cpu": frozenset()}[self.preprocess]
            # with `auto`, a stored `fail` of a JPEG check of the quick check switches off its part of the GPU frame path on
            # its device (Behaviour item 13): `jpeg-preprocess` the GPU preprocess and the GPU decode, `jpeg-decode` the GPU decode
            reads = self.preprocess == "auto" and plan.execution_provider in graph_eps and plan.execution_provider in JPEG_DECODER_EPS
            stored = [stored_jpeg_checks(plan.execution_provider, device_key) if reads else {} for device_key in self.devices]
            off = frozenset(index for index, checks in enumerate(stored) if checks.get("jpeg-preprocess") == "fail")
            if plan.execution_provider in graph_eps and len(off) < len(self.devices):
                # the device memory of the bound values is that of the provider of the model session
                device_type = {sessions.CPU_EP_NAME: "cpu", sessions.DML_EP_NAME: "dml"}.get(opened[node_id][0].report.ep_name, "cuda")
                graph = onnx_model.GraphPath(
                    functools.partial(self.sessions.open_preprocess, node, plan), places, device_type, self._warn,
                    onnx_model.graph_refusal(node.model, plan.precision, slots), off,
                )
            self.models[node_id] = onnx_model.OnnxModelRunner(node, plan.precision, [item.session for item in opened[node_id]], graph)
            if off:
                cause = f"a stored quick check of '{plan.execution_provider}' on this system gives fail for jpeg-preprocess"
                self.start_warnings.append(PipelineWarning(
                    onnx_model.PREPROCESSED_ON_CPU, f"{node_id}: the preprocess runs on the CPU ({sessions.QUICK_CHECK_FAILED}): {cause}", (node_id,),
                    {"node": node_id, "reason": sessions.QUICK_CHECK_FAILED, "frame_sizes": None, "cause": cause},
                ))
            # the frame stage uploads or GPU-decodes the frames of the devices where the node starts on the graph
            on = [] if graph is None or graph.refused is not None else [index for index in range(len(places)) if index not in off]
            for index in on:
                place = places[index]
                # a DML session does not see a frame of `OrtValue.ortvalue_from_numpy(..., "dml")`: it gets the host
                # frame and copies it to the device in its own run (ADR-W4NW, Evidence)
                self.upload_devices.setdefault(index, (place.ep_device_id, "cpu" if graph.device_type == "dml" else graph.device_type))
                if plan.execution_provider in JPEG_DECODER_EPS:
                    self.decoder_places.setdefault(index, (plan.execution_provider, place.device_key, place.ep_device_id))
            for index, checks in enumerate(stored):
                if index in off or (index in on and checks.get("jpeg-decode") == "fail"):  # no GPU decoder opens there
                    self.decoder_places.setdefault(index, (plan.execution_provider, places[index].device_key, places[index].ep_device_id))
                    self.decode_failed.add(index)
        return opened

    def _not_wired(self) -> list[PipelineWarning]:
        """With `preprocess="gpu"`, the warning `preprocessed_on_cpu` of each node that runs on an EP with no GPU preprocess (Behaviour item 14)."""
        if self.preprocess != "gpu":
            return []
        found = []
        for node_id in self.models:
            ep = self.plans[node_id].execution_provider
            if ep not in onnx_model.GRAPH_EPS:
                cause = f"the EP {ep} has no GPU preprocess"
                found.append(PipelineWarning(
                    onnx_model.PREPROCESSED_ON_CPU, f"{node_id}: the preprocess runs on the CPU ({sessions.EP_NOT_WIRED}): {cause}", (node_id,),
                    {"node": node_id, "reason": sessions.EP_NOT_WIRED, "frame_sizes": None, "cause": cause},
                ))
        return found

    def _node_items(self, opened: Mapping[str, list[sessions.OpenedSession]]) -> dict[str, dict[str, Any]]:
        """Return the node item of each node of the file, for the timing header and for `tap.json`.

        The item of an `onnx_model` node that runs gets its `execution` from the `SessionReport`.
        """
        items: dict[str, dict[str, Any]] = {}
        for node in self.config.nodes:
            plan, model = self.plans.get(node.id), self.resolved.nodes[node.id].model
            facts: dict[str, Any] = {}
            if plan is not None:
                facts = {"sidecar_sha256": model.sidecar_sha256, "artifact_sha256": plan.artifact_sha256, "precision": plan.precision}
            if node.id in opened:
                # the item of a node with a session on each of two or more GPUs is that of the first GPU (pipeline.timing, Fields)
                first = opened[node.id][0]
                report = first.report
                facts.update(
                    batching=first.batch,
                    execution={
                        "requested_ep": report.requested_ep, "used_ep": report.used_ep, "device": report.device_key,
                        "gpu_uuid": report.gpu_uuid, "ep_device_id": report.ep_device_id, "ep_options": dict(report.ep_options),
                        "cpu_nodes": report.cpu_nodes, "cpu_op_types": list(report.cpu_op_types), "cpu_threads": report.cpu_threads,
                    },
                    # the preprocess graph at the start has the provider of the session, else the preprocessing runs on
                    # the host; the postprocessing runs on the host, so its provider is null (pipeline.timing, Fields)
                    stage_providers={
                        "preprocess": report.ep_name if self.models[node.id].graph_on_at_start else None,
                        "inference": report.ep_name, "postprocess": None,
                    },
                    shared_with=[other for other in first.node_ids if other != node.id],
                )
            items[node.id] = timing_module.make_node_item(node, **facts)
        return items

    # ---- one call -------------------------------------------------------------------------

    def _check_call(self, frames: Mapping[Any, Any]) -> dict[Any, float | None]:
        """Check the cameras and the frame times of a call. Return the `timestamp_ms` of each camera, in the order of the run."""
        mode = self.running_mode
        unknown = [camera_id for camera_id in frames if camera_id not in self.prev]
        missing = [camera_id for camera_id in self.camera_ids if camera_id not in frames]
        if unknown or not frames or (missing and mode != "live"):
            raise CallRefusedError(
                f"V-pipeline.running-2: a call in `{mode}` must give a frame for "
                f"{'one or more camera ids' if mode == 'live' else 'each camera id'} of the run {self.camera_ids}, and for no other id; "
                f"it got {list(frames)}", "V-pipeline.running-2",
            )
        found: dict[Any, float | None] = {}
        for camera_id in self.camera_ids:
            if camera_id not in frames:
                continue
            frame = frames[camera_id]
            given = frame.timestamp_ms
            if self.image_ids is not None and not 0 <= frame.frame_index < len(self.image_ids):
                raise CallRefusedError(f"the frame_index {frame.frame_index} is not an image of the image list of the run")
            if mode == "image":
                found[camera_id] = None
                continue
            if mode == "live" and given is None:
                raise CallRefusedError(f"V-pipeline.running-6: camera {camera_id!r}: each frame must have a timestamp_ms in `live`", "V-pipeline.running-6")
            before = self.gives_timestamp[camera_id]
            if mode == "video" and before is not None and before != (given is not None):
                raise CallRefusedError(
                    f"V-pipeline.running-7: camera {camera_id!r}: a camera must give a timestamp_ms on each of its frames or on none; "
                    f"this frame {'has one' if given is not None else 'has none'}", "V-pipeline.running-7",
                )
            timestamp = float(given) if given is not None else frame.frame_index * 1000.0 / self.fps
            last = self.last_timestamp[camera_id]
            if last is not None and not timestamp > last:
                raise CallRefusedError(f"{TIMESTAMP_RULE}: camera {camera_id!r}: timestamp_ms must increase: got {timestamp} after {last}", TIMESTAMP_RULE)
            found[camera_id] = timestamp
        return found

    def _frame_images(self, frames: Mapping[Any, Any], cameras: Sequence[Any], events: list[dict[str, Any]]) -> dict[Any, DecodedFrame]:
        """Return `frame.image` of each camera of the call: decoded and turned by `rotation_deg` (pipeline.running, Behaviour item 13).

        `V-pipeline.running-13` and the SOI check of each JPEG buffer come before any decode. On a
        device of `decoder_places`, the JPEG buffers of the call go to the GPU decoder in one batch.
        The decoder opens at the first call with a JPEG buffer on its device. A buffer that the GPU
        decoder refuses, each buffer of a device with no GPU decoder, and each buffer of a device of
        `decode_failed` (no decoder opens there), decodes on the CPU. Two or
        more such buffers decode in the thread pool of the run, with at most `cpu_threads` threads,
        when `cpu_threads` is more than 1. The call waits for each decode, then reads the results in
        camera order: a refused call names the first bad camera, as a decode in a row does. A refused
        call gives no warning: the warnings of the decode go out only when each buffer decoded.
        """
        rotations = {}
        for camera_id in cameras:
            frame = frames[camera_id]
            rotation = rotations[camera_id] = 0 if frame.rotation_deg is None else frame.rotation_deg
            if type(rotation) is not int or rotation not in cpu.ROTATIONS:  # `type` refuses a bool and a float such as 90.0
                raise CallRefusedError(f"V-pipeline.running-13: camera {camera_id!r}: rotation_deg must be 0, 90, 180 or 270; got {rotation!r}", "V-pipeline.running-13")
            if isinstance(frame.image, bytes | bytearray) and not cpu.starts_as_jpeg(frame.image):  # also an empty buffer
                raise CallRefusedError(
                    f"V-pipeline.running-12: camera {camera_id!r}: the buffer is not a JPEG image: it does not start with the JPEG SOI marker", "V-pipeline.running-12",
                )
        jpegs = [camera_id for camera_id in cameras if isinstance(frames[camera_id].image, bytes | bytearray)]
        # the array of the caller as given for 0, else a new array; this turn is in no `frame` span (pipeline.timing)
        found = {camera_id: DecodedFrame.from_host(cpu.turn(frames[camera_id].image, rotations[camera_id])) for camera_id in cameras if camera_id not in jpegs}
        if not jpegs:
            return found
        begin = time.perf_counter_ns()
        pending: dict[Any, PipelineWarning] = {}
        for index, place in self.decoder_places.items():
            group = [camera_id for camera_id in jpegs if self.device_of[camera_id] == index]
            if not group:
                continue
            if index in self.decode_failed:  # a stored quick check: no GPU decoder opens, one warning for the run
                if sessions.QUICK_CHECK_FAILED not in self.jpeg_warned:
                    pending[sessions.QUICK_CHECK_FAILED] = PipelineWarning(
                        JPEG_DECODED_ON_CPU, f"a stored quick check of '{place[0]}' on this system gives fail for a JPEG check: the run decodes "
                        "the JPEG buffers of that GPU on the CPU", (), {"reason": sessions.QUICK_CHECK_FAILED},
                    )
                continue
            if index not in self.decoders:  # one open for each device and run, also when it gives None or raises
                try:
                    self.decoders[index] = open_jpeg_decoder(*place)
                except Exception as exc:  # the CPU decode is correct: an open error must not stop each JPEG call
                    logger.warning("the GPU JPEG decoder of '%s' did not open", place[0], exc_info=True)
                    self.decoders[index], self.open_errors[index] = None, sanitize_text(f"{type(exc).__name__}: {exc}")[:300]
            if self.decoders[index] is None:
                if "decoder_unavailable" not in self.jpeg_warned and "decoder_unavailable" not in pending:  # the catalog read only until the warning
                    pending["decoder_unavailable"] = decoder_missing_warning(place[0], self.open_errors.get(index))
                continue
            decoded = self.decoders[index].decode([frames[camera_id].image for camera_id in group], [rotations[camera_id] for camera_id in group])
            for camera_id, frame in zip(group, decoded, strict=True):
                if frame is not None:
                    found[camera_id] = frame
                else:
                    pending[("decoder_refused", camera_id)] = PipelineWarning(
                        JPEG_DECODED_ON_CPU, f"camera {camera_id!r}: the GPU JPEG decoder refuses the JPEG buffer: the run decodes it on the CPU", (),
                        {"reason": "decoder_refused", "camera_id": camera_id},
                    )
        on_cpu = [camera_id for camera_id in jpegs if camera_id not in found]
        if len(on_cpu) > 1 and self.cpu_threads > 1:
            if self.decode_pool is None:
                self.decode_pool = concurrent.futures.ThreadPoolExecutor(min(self.cpu_threads, len(self.camera_ids)), thread_name_prefix="skellytracker-jpeg")
            futures = [self.decode_pool.submit(cpu.decode_jpeg, frames[camera_id].image, rotations[camera_id]) for camera_id in on_cpu]
            concurrent.futures.wait(futures)  # no decode still runs when the call returns or raises
            decodes = [future.result for future in futures]
        else:
            decodes = [functools.partial(cpu.decode_jpeg, frames[camera_id].image, rotations[camera_id]) for camera_id in on_cpu]
        for camera_id, decode in zip(on_cpu, decodes, strict=True):  # camera order: the error is that of the first bad camera
            try:
                found[camera_id] = DecodedFrame.from_host(decode())
            except ValueError as exc:
                raise CallRefusedError(f"V-pipeline.running-12: camera {camera_id!r}: {exc}", "V-pipeline.running-12") from exc
        if f"{FRAME}.decode" in self.spans_on:
            events.append(timing_module.make_event([(frames[camera_id].frame_index, camera_id) for camera_id in jpegs], FRAME, "decode", begin, time.perf_counter_ns()))
        for key, warning in pending.items():
            if key not in self.jpeg_warned:
                self.jpeg_warned.add(key)
                self._warn(warning)
        return {camera_id: found[camera_id] for camera_id in cameras}

    def _frame_stage(
        self, pixels: Mapping[Any, DecodedFrame], frames: Mapping[Any, Any], events: list[dict[str, Any]],
    ) -> tuple[dict[int, onnx_model.CallSlots], dict[Any, tuple[int, int]]]:
        """The frame stage of one call, after the decode and the turn and before the first node. Return the slots and the slot sizes.

        On each device with a node that starts on the graph path, each camera of the device has a
        fixed slot. The frame of a camera of the call goes to GPU memory one time
        (`DecodedFrame.on_device`), and each node of the call reads that copy. A camera that is not
        in the call gets a zero frame of the last size of the camera, one upload for each device and
        size, kept until the close. Before its first frame, a camera takes the size of the first
        frame of the call on its device. The set of frame sizes thus changes only when a camera
        changes its frame size. The slot sizes are committed with the call. A frame of the GPU
        decoder is in GPU memory already: it does not upload. The event `frame.upload` gives the
        cameras whose frame uploads; its time also holds the upload of a new zero frame.
        """
        begin = time.perf_counter_ns()
        uploaded = []
        sizes = {camera_id: (frame.width, frame.height) for camera_id, frame in pixels.items()}
        found = {}
        for index, (device_id, device_type) in self.upload_devices.items():
            slot_cameras = [camera_id for camera_id in self.camera_ids if self.device_of[camera_id] == index]
            present = [camera_id for camera_id in slot_cameras if camera_id in pixels]
            if not present:
                continue
            upload = functools.partial(eps_session.upload_frame, device_type=device_type)
            values, sources = [], []
            for camera_id in slot_cameras:
                size = sizes.setdefault(camera_id, self.slot_sizes.get(camera_id, sizes[present[0]]))
                sources.append(size)
                if camera_id in pixels:
                    if pixels[camera_id].device is None:
                        uploaded.append(camera_id)
                    values.append(pixels[camera_id].on_device(device_id, upload))
                    continue
                if (index, size) not in self.zero_frames:
                    self.zero_frames[(index, size)] = upload(np.zeros((size[1], size[0], 3), np.uint8), device_id)
                values.append(self.zero_frames[(index, size)])
            slot_of = {id(pixels[camera_id]): slot for slot, camera_id in enumerate(slot_cameras) if camera_id in pixels}
            found[index] = onnx_model.CallSlots(tuple(values), tuple(sources), slot_of)
        if uploaded and f"{FRAME}.upload" in self.spans_on:
            events.append(timing_module.make_event([(frames[camera_id].frame_index, camera_id) for camera_id in uploaded], FRAME, "upload", begin, time.perf_counter_ns()))
        return found, sizes

    def _inputs(self, node: ResolvedNode, camera_id: Any, values: Mapping[Port, Any]) -> Any:
        """Return the inputs of a node for one camera: a list for a variadic node, else a mapping by input name."""
        found = []
        for item in node.inputs:
            port = (item.node, item.port)
            if not item.prev:
                value = values[port]
            elif self.running_mode != "image" and port in self.prev[camera_id]:
                value = self.prev[camera_id][port]
            else:
                value = self.resolved.port_info(*port).empty()
            found.append((item.name, value))
        return [value for _, value in found] if isinstance(node.inputs_info, list) else dict(found)

    @staticmethod
    def _stops(node: ResolvedNode, inputs: Any) -> bool:
        """Return true when an empty required input or a false `run_if` stops the node (pipeline.graph, Behaviour item 6)."""
        if isinstance(inputs, list):
            return False  # `first_of` reads each empty item of its list
        if inputs.get("run_if") is False:
            return True
        required = BY_TYPE[node.type].required_inputs + (("boxes",) if node.model is not None and node.model.kind == "top_down" else ())
        reads = onnx_model.READS_EMPTY if node.type == "onnx_model" else MODULES[node.type].READS_EMPTY
        return any(name in inputs and name not in reads and is_empty(inputs[name]) for name in required)

    def process(self, frames: Mapping[Any, Any]) -> dict[Any, dict[str, Any]]:
        """Run one call: one frame for each camera of the call. Return the result of each camera.

        A frame has `image`, `frame_index`, `timestamp_ms` and `rotation_deg`. A call that breaks a
        rule of the call raises `CallRefusedError` before a node runs.
        """
        clock = time.perf_counter_ns
        start = clock()
        timestamps = self._check_call(frames)
        cameras = list(timestamps)
        images = [(frames[camera_id].frame_index, camera_id) for camera_id in cameras]
        events: list[dict[str, Any]] = []
        pixels = self._frame_images(frames, cameras, events)  # each JPEG decode before a node runs
        self.call_slots, slot_sizes = self._frame_stage(pixels, frames, events)
        contexts, values = {}, {}
        for camera_id in cameras:
            frame = frames[camera_id]
            contexts[camera_id] = FrameContext(frame.frame_index, timestamps[camera_id], pixels[camera_id].width, pixels[camera_id].height, self.running_mode)
            values[camera_id] = {(FRAME, "image"): pixels[camera_id]}
            for port, replay in self.replays.items():
                values[camera_id][port] = replay.value(frame.frame_index, camera_id)
        node_ran = {camera_id: dict.fromkeys(self.inference_nodes, False) for camera_id in cameras}
        new_states: dict[tuple[Any, str], Any] = {}

        for node_id in self.order:
            node = self.resolved.nodes[node_id]
            ready: dict[Any, Any] = {}
            node_start = clock()
            for camera_id in cameras:
                inputs = self._inputs(node, camera_id, values[camera_id])
                if self._stops(node, inputs):
                    values[camera_id].update({(node_id, port): info.empty() for port, info in node.outputs_info.items()})
                else:
                    ready[camera_id] = inputs
            if node.type == "onnx_model":
                self._run_model(node, ready, frames, values, events)
            else:
                for camera_id, inputs in ready.items():
                    try:
                        outputs, state = MODULES[node.type].run(
                            self.params[node_id], inputs, self.states.get((camera_id, node_id)), contexts[camera_id], self.infos[node_id],
                        )
                    except ValueError as exc:
                        if str(exc).startswith(TIMESTAMP_RULE):
                            raise CallRefusedError(f"{node_id}: camera {camera_id!r}: {exc}", TIMESTAMP_RULE) from exc
                        raise
                    new_states[(camera_id, node_id)] = state
                    values[camera_id].update({(node_id, port): value for port, value in outputs.items()})
                if ready and f"{node_id}.run" in self.spans_on:
                    events.append(timing_module.make_event([(frames[c].frame_index, c) for c in ready], node_id, "run", node_start, clock()))
            if node.type in INFERENCE_TYPES:
                for camera_id in ready:
                    node_ran[camera_id][node_id] = True

        results: dict[Any, dict[str, Any]] = {}
        for camera_id in cameras:
            frame, context = frames[camera_id], contexts[camera_id]
            result = {name: deliver(info, values[camera_id][port], node_ran[camera_id], self.resolved.user_root) for name, port, info in self.outputs}
            result.update(frame_index=frame.frame_index, image_width=context.image_width, image_height=context.image_height, timestamp_ms=timestamps[camera_id], node_ran=node_ran[camera_id])
            results[camera_id] = result
            for record, _ in self.records:
                image_id = (
                    self.image_ids[frame.frame_index] if self.image_ids is not None
                    else frame.frame_index * len(self.camera_ids) + self.camera_ids.index(camera_id)
                )
                record.write(values[camera_id][_port(record.tap.port)], frame.frame_index, camera_id, image_id)

        # The call ran: commit the states, the `@prev` values, the frame times and the slot sizes of its cameras.
        self.states.update(new_states)
        self.slot_sizes.update(slot_sizes)
        for camera_id in cameras:
            if self.running_mode != "image":
                self.prev[camera_id].update({port: values[camera_id][port] for port in self.prev_ports})
            self.last_timestamp[camera_id] = timestamps[camera_id]
            self.gives_timestamp[camera_id] = frames[camera_id].timestamp_ms is not None
        self.calls += 1
        self.port_values = values  # camera id -> port -> the value of the last call: the tests read the internal ports here
        if self.writer is not None:
            for event in events:
                self.writer.write_event(event)
            if f"{RESERVED_NODE_ID}.run" in self.spans_on:
                self.writer.write_event(timing_module.make_event(images, RESERVED_NODE_ID, "run", start, clock()))
        return results

    def _run_model(
        self, node: ResolvedNode, ready: Mapping[Any, Any], frames: Mapping[Any, Any], values: Mapping[Any, dict[Port, Any]],
        events: list[dict[str, Any]],
    ) -> None:
        """Run an `onnx_model` node for the cameras of the call that it runs for: one inference call for each device."""
        runner = self.models[node.id]
        for index in range(len(self.devices)):
            cameras = [camera_id for camera_id in ready if self.device_of[camera_id] == index]
            if not cameras:
                continue
            # A partial, not a nested def: `beartype_this_package` decorates a nested def again on each call.
            timer = None if self.writer is None else functools.partial(
                self._add_span, events, node.id, [(frames[camera_id].frame_index, camera_id) for camera_id in cameras],
            )
            boxes = [ready[camera_id]["boxes"] for camera_id in cameras] if runner.kind == "top_down" else None
            if runner.graph is None:
                found = runner.run(index, [ready[camera_id]["image"].host for camera_id in cameras], boxes, timer)
            else:  # the graph path reads the device frames of the frame stage
                found = runner.run(index, [ready[camera_id]["image"] for camera_id in cameras], boxes, timer, self.call_slots.get(index))
            for camera_id, outputs in zip(cameras, found, strict=True):
                values[camera_id].update({(node.id, port): value for port, value in outputs.items()})

    def _add_span(self, events: list[dict[str, Any]], node_id: str, images: list[tuple[int, Any]], span: str, start_ns: int, end_ns: int) -> None:
        """Add the event of one span of an `onnx_model` node when the span is on."""
        if f"{node_id}.{span}" in self.spans_on:
            events.append(timing_module.make_event(images, node_id, span, start_ns, end_ns))

    # ---- params during a run --------------------------------------------------------------

    def set_params(self, node_id: str, params: Mapping[str, Any]) -> None:
        """Set params of one node (pipeline.running, Behaviour item 11). A refused call raises `SetParamsRefusedError` and changes no param."""
        rule = "V-pipeline.running-10"
        if node_id not in self.resolved.nodes:
            raise SetParamsRefusedError(f"{rule}: {node_id!r} is not a node of the run")
        fields = type(self.params[node_id]).model_fields
        for name in params:
            if name not in fields:
                raise SetParamsRefusedError(f"{rule}: {name!r} is not a param of the node {node_id} ({self.resolved.nodes[node_id].type})")
            if not (fields[name].json_schema_extra or {}).get("set_during_run"):
                raise SetParamsRefusedError(f"{rule}: the param {name!r} of the node {node_id} cannot change during a run")
        if self.calls and (self.running_mode != "live" or self.records):
            raise SetParamsRefusedError(
                f"{rule}: after the first call, a run takes set_params only in `live` and with no record tap; "
                f"this run is in `{self.running_mode}` and has {len(self.records)} record taps"
            )
        # The form as written: a dump with each default does not load again (ADR-97X9 item 10).
        data = _union(self.config.model_dump(mode="json", exclude_unset=True), self.config.model_dump(mode="json", exclude_defaults=True))
        next(item for item in data["nodes"] if item["id"] == node_id).setdefault("params", {}).update(params)
        try:  # the whole config, as the load checks it: the type, the range and the rules of the params
            changed = resolve(PipelineConfig.model_validate(data), self.resolved.user_root)
        except ValueError as exc:
            raise SetParamsRefusedError(f"{rule}: {node_id}: {exc}") from exc
        if changed.nodes[node_id].outputs_info != self.resolved.nodes[node_id].outputs_info:
            raise SetParamsRefusedError(f"{rule}: {node_id}: the change would change the facts of the ports of the node")
        self.config = changed.config
        self.params[node_id] = changed.nodes[node_id].node.params
        self.infos[node_id] = changed.nodes[node_id].infos

    # ---- close ----------------------------------------------------------------------------

    def close(self, write_taps: bool = True) -> None:
        """Write `tap.json` of each record tap, close the timing file, and free the MediaPipe runners, the sessions and the GPU JPEG decoders.

        The order of pipeline.running, Implementer guidance: the IO bindings (the run keeps none),
        the decoded frames, the sessions, then each decoder, which closes its turn sessions and then
        its CUDA stream. Before the sessions, the thread pool of the CPU JPEG decode stops after its
        last decode. When a close of the pool, a session or a decoder raises, the other closes still
        run, and then the first error raises.
        """
        if self.closed:
            return
        self.closed = True
        for record, manifest in self.records:
            if write_taps:
                record.close(manifest)
            else:
                record.discard()
        if self.writer is not None:
            self.writer.close()
        for (_, node_id), state in self.states.items():
            if self.resolved.nodes[node_id].type == "mediapipe_tasks":
                mediapipe_tasks.close_state(state)
        self.states.clear()
        # The decoded frames and the zero frames first: no frame in device memory outlives the sessions.
        self.port_values, self.call_slots = {}, {}
        self.zero_frames.clear()
        # Each close runs also when an earlier one raises; the first error goes to the caller after the last close.
        pool = [] if self.decode_pool is None else [functools.partial(self.decode_pool.shutdown, wait=True, cancel_futures=True)]
        closes = [*pool, *(runner.close for runner in self.models.values()), self.sessions.close,
                  *(decoder.close for decoder in self.decoders.values() if decoder is not None)]
        self.models.clear()
        self.decoders.clear()
        errors = []
        for close in closes:
            try:
                close()
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise errors[0]
