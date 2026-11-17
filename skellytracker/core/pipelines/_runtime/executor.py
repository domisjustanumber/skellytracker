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

import functools
import logging
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from skellytracker.core.errors import CallRefusedError, SetParamsRefusedError
from skellytracker.core.pipelines import timing as timing_module
from skellytracker.core.pipelines._runtime import mediapipe_tasks, onnx_model, sessions, taps
from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines._runtime.resolve import MODULES, ResolvedNode, ResolvedPipeline, resolve
from skellytracker.core.pipelines.config import BY_TYPE, FRAME, RESERVED_NODE_ID, PipelineConfig
from skellytracker.core.pipelines.loading import _union
from skellytracker.core.pipelines.values import is_empty
from skellytracker.core.pipelines.warnings import PipelineWarning

logger = logging.getLogger(__name__)

RUNNING_MODES = ("image", "video", "live")
INFERENCE_TYPES = ("onnx_model", "mediapipe_tasks")
TIMESTAMP_RULE = "V-node.smooth_keypoints-3"
BATCH_LIMITED_BY_STATE = "batch_limited_by_state"
Port = tuple[str, str]


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
        self.batch_k = 1  # k is 1 on each GPU in this version (pipeline.running, Behaviour item 4)
        self.on_warning = on_warning
        self.warnings: list[PipelineWarning] = []
        self.run_id = uuid.uuid4().hex
        self.image_ids = None if image_ids is None else [int(item) for item in image_ids]
        self.calls = 0
        self.closed = False

        if running_mode not in RUNNING_MODES:
            raise ValueError(f"running_mode must be one of {list(RUNNING_MODES)}, not {running_mode!r}")
        if timing not in ("on", "off"):
            raise ValueError(f"timing must be 'on' or 'off', not {timing!r}")
        if not self.fps > 0:
            raise ValueError(f"fps must be more than 0, not {fps!r}")
        if not self.camera_ids or len(set(self.camera_ids)) != len(self.camera_ids):
            raise ValueError(f"V-pipeline.running-1: camera_ids must be a non-empty list of unique ids, not {self.camera_ids!r}")
        if running_mode == "image" and len(self.camera_ids) != 1:
            raise ValueError(f"V-pipeline.running-1: the running mode `image` needs exactly one camera id, not {len(self.camera_ids)}")
        if self.image_ids is not None and len(self.camera_ids) != 1:
            raise ValueError("the COCO input form has one camera")
        sessions.check_run_ep(resolved, execution_provider)
        for name, ref in config.outputs.items():
            if (port_type := resolved.port_info(*_port(ref)).port_type) not in taps.JSONL_TYPES:
                raise ValueError(
                    f"the output {name!r} names the port {ref} of the type {port_type}: "
                    "the pipeline spec does not fix the value of an `image` or a `flag` output yet (pipeline.outputs, Behaviour item 6)"
                )

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
        self.sessions = sessions.RunSessions()
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

        for warning in (*resolved.warnings, *self.sessions.partial_placement()):
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
            rows = node.inputs_info["boxes"].max_instances if node.model.kind == "top_down" else 1
            opened[node_id] = []
            for index, device_key in enumerate(self.devices):
                cameras = sum(1 for slot in self.device_of.values() if slot == index)
                opened[node_id].append(self.sessions.open(node, self.plans[node_id], device_key, self.batch_k * cameras * rows))
            self.models[node_id] = onnx_model.OnnxModelRunner(node, self.plans[node_id].precision, [item.session for item in opened[node_id]])
        return opened

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
                        "cpu_nodes": report.cpu_nodes, "cpu_op_types": list(report.cpu_op_types),
                    },
                    # the preprocessing and the postprocessing run on the host, so their provider is null (pipeline.timing, Fields)
                    stage_providers={"preprocess": None, "inference": report.ep_name, "postprocess": None},
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
        """Return true when an empty required input stops the node (pipeline.graph, Behaviour item 6)."""
        if isinstance(inputs, list):
            return False  # `first_of` and `concat` read each empty item of their list
        required = BY_TYPE[node.type].required_inputs + (("boxes",) if node.model is not None and node.model.kind == "top_down" else ())
        reads = onnx_model.READS_EMPTY if node.type == "onnx_model" else MODULES[node.type].READS_EMPTY
        return any(name in inputs and name not in reads and is_empty(inputs[name]) for name in required)

    def process(self, frames: Mapping[Any, Any]) -> dict[Any, dict[str, Any]]:
        """Run one call: one frame for each camera of the call. Return the result of each camera.

        A frame has `image`, `frame_index` and `timestamp_ms`. A call that breaks a rule of the
        call raises `CallRefusedError` before a node runs.
        """
        clock = time.perf_counter_ns
        start = clock()
        timestamps = self._check_call(frames)
        cameras = list(timestamps)
        images = [(frames[camera_id].frame_index, camera_id) for camera_id in cameras]
        contexts, values = {}, {}
        for camera_id in cameras:
            frame = frames[camera_id]
            height, width = frame.image.shape[:2]
            contexts[camera_id] = FrameContext(frame.frame_index, timestamps[camera_id], int(width), int(height), self.running_mode)
            values[camera_id] = {(FRAME, "image"): frame.image}
            for port, replay in self.replays.items():
                values[camera_id][port] = replay.value(frame.frame_index, camera_id)
        node_ran = {camera_id: dict.fromkeys(self.inference_nodes, False) for camera_id in cameras}
        new_states: dict[tuple[Any, str], Any] = {}
        events: list[dict[str, Any]] = []

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
            result = {name: values[camera_id][_port(ref)] for name, ref in self.config.outputs.items()}
            result.update(frame_index=frame.frame_index, image_width=context.image_width, image_height=context.image_height, timestamp_ms=timestamps[camera_id], node_ran=node_ran[camera_id])
            results[camera_id] = result
            for record, _ in self.records:
                image_id = (
                    self.image_ids[frame.frame_index] if self.image_ids is not None
                    else frame.frame_index * len(self.camera_ids) + self.camera_ids.index(camera_id)
                )
                record.write(values[camera_id][_port(record.tap.port)], frame.frame_index, camera_id, image_id)

        # The call ran: commit the states, the `@prev` values and the frame times of its cameras.
        self.states.update(new_states)
        for camera_id in cameras:
            if self.running_mode != "image":
                self.prev[camera_id].update({port: values[camera_id][port] for port in self.prev_ports})
            self.last_timestamp[camera_id] = timestamps[camera_id]
            self.gives_timestamp[camera_id] = frames[camera_id].timestamp_ms is not None
        self.calls += 1
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
            found = runner.run(index, [ready[camera_id]["image"] for camera_id in cameras], boxes, timer)
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
        """Write `tap.json` of each record tap, close the timing file, and free the MediaPipe runners and the sessions."""
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
        for runner in self.models.values():
            runner.close()
        self.models.clear()
        self.sessions.close()
