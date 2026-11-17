"""The inference sessions of one pipeline run, and the start checks that need the EP catalog.

Implements: pipeline.running

A run owns its sessions. In one run, the nodes with the same artifact SHA-256, batch, EP key, EP
options and device share one session. Two runs share no session: each run has its own
`RunSessions`. This module imports no `onnxruntime`: `open_session` of the generic detectors
builds each session with `eps.build_session()`.
"""
from __future__ import annotations

import importlib.util
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.recommendation import select_precision
from skellytracker.core.eps.records import RunDevice, SessionReport
from skellytracker.core.eps.state import check_start
from skellytracker.core.errors import EpRequestError, EpUnavailableError, MissingDependencyError
from skellytracker.core.metrics import free_vram
from skellytracker.core.pipelines._runtime import mediapipe_tasks
from skellytracker.core.pipelines._runtime.resolve import ResolvedNode, ResolvedPipeline
from skellytracker.core.pipelines.warnings import PipelineWarning

CPU_EP_NAME = "CPUExecutionProvider"
EP_PARTIAL_PLACEMENT = "ep_partial_placement"


@dataclass(frozen=True)
class NodePlan:
    """The EP, the EP options and the artifact of one `onnx_model` node (node.onnx_model, Fields)."""

    node_id: str
    execution_provider: str
    ep_options: tuple[tuple[str, str], ...]
    gpu: bool
    """True when the EP runs on a GPU: it then takes a device key."""
    precision: str
    artifact_sha256: str
    filename: str


@dataclass
class OpenedSession:
    """One session of a run. `batch` is the batch of the session, or `dynamic`. `node_ids` are the nodes that use it."""

    session: Any
    report: SessionReport
    batch: int | str
    node_ids: list[str] = field(default_factory=list)


def check_run_ep(resolved: ResolvedPipeline, execution_provider: str | None) -> None:
    """Check `V-pipeline.running-8` and `V-pipeline.running-9`."""
    if resolved.needs_execution_provider and execution_provider is None:
        nodes = [node.id for node in resolved.nodes.values() if node.type == "onnx_model" and node.node.params.execution_provider is None]
        raise ValueError(f"V-pipeline.running-8: the nodes {nodes} have no execution_provider, so the run must give an execution_provider")
    if not resolved.has_onnx_model and execution_provider is not None:
        raise ValueError("V-pipeline.running-9: the pipeline has no onnx_model node, so the run must not give an execution_provider")


def node_plan(node: ResolvedNode, execution_provider: str | None, ep_options: Mapping[str, str] | None) -> NodePlan:
    """Return the plan of one `onnx_model` node. `execution_provider` and `ep_options` are those of the run.

    The EP of the node is its `execution_provider`, else the EP of the run. Its options are its
    `ep_options`. When they are empty and the node uses the EP of the run, they are the options of
    the run. With no `precision`, the precision is fp16 on a GPU EP and fp32 on the CPU EP, and
    fp32 when the size has no fp16 artifact. An unknown or reserved EP key raises `EpRequestError`.
    """
    params, model = node.node.params, node.model
    key = params.execution_provider or execution_provider
    options = dict(params.ep_options) or ({} if params.execution_provider else dict(ep_options or {}))
    gpu = load_catalog().pack(key) is not None
    precision = params.precision or select_precision(key, model.precisions)
    artifact = model.entry.artifact(model.size, precision)
    return NodePlan(node.id, key, tuple(sorted(options.items())), gpu, precision, artifact.sha256, artifact.filename)


def check_dependencies(resolved: ResolvedPipeline, running: Sequence[str], plans: Mapping[str, NodePlan]) -> None:
    """Check `V-pipeline.running-3` for the nodes that run. Raise `MissingDependencyError`.

    An artifact is usable when its file is present with the hash of the sidecar, or when it has a
    `url`: the session start then downloads it. The catalog made this check at the load.
    """
    tasks = [node_id for node_id in running if resolved.nodes[node_id].type == "mediapipe_tasks"]
    if tasks and (extra := mediapipe_tasks.missing_extra()) is not None:
        raise MissingDependencyError(extra, tasks)
    missing = [
        (node_id, artifact) for node_id in running if node_id in plans
        for artifact in [resolved.nodes[node_id].model.entry.artifact(resolved.nodes[node_id].model.size, plans[node_id].precision)]
        if not artifact.available
    ]
    if missing:
        raise MissingDependencyError(
            None, [node_id for node_id, _ in missing], sorted({artifact.filename for _, artifact in missing}),
            str(missing[0][1].unavailable_reason),
        )


def run_gpus(plans: Sequence[NodePlan], device: str | Sequence[str] | None) -> tuple[RunDevice, ...]:
    """Check `V-pipeline.running-4` and return the GPUs of the run. A run with no GPU EP has no GPU.

    `eps.check_start` checks each EP key, its options and its state. The GPU set of the run is the
    GPUs that each GPU EP of the plans lists (ADR-P1F3 item 8), in the order of the first GPU EP:
    the GPU with the most VRAM first.
    """
    gpus: list[RunDevice] | None = None
    for ep, options in dict.fromkeys((plan.execution_provider, plan.ep_options) for plan in plans):
        gpu = next(plan.gpu for plan in plans if plan.execution_provider == ep)
        found = list(check_start(ep, dict(options), device if gpu else None))
        if gpu:
            keys = {item.device_key for item in found}
            gpus = found if gpus is None else [item for item in gpus if item.device_key in keys]
    if gpus is None:
        if device is not None:
            raise EpRequestError(f"no node of the run uses a GPU, so the run takes no device; it got {device!r}")
        return ()
    if not gpus:
        raise EpUnavailableError("no GPU of this host can run each GPU execution provider of the run")
    return tuple(gpus)


def gpu_weights(gpus: Sequence[RunDevice], vram_reserve_bytes: int) -> list[int | None]:
    """Return the VRAM bytes that the run can use on each GPU, read one time at start (ADR-AMF7 item 2).

    The value is the free VRAM minus the reserve, with a floor of 0, when NVML gives the free VRAM
    of each GPU. Else it is the total VRAM minus the reserve, and None for a GPU with no total.
    """
    free = [free_vram(gpu.device_key) for gpu in gpus]
    found = free if None not in free else [gpu.vram_total_bytes for gpu in gpus]
    return [None if value is None else max(0, value - vram_reserve_bytes) for value in found]


def split_cameras(camera_ids: Sequence[Any], weights: Sequence[int | None]) -> dict[Any, int]:
    """Return the GPU index of each camera (pipeline.running, Behaviour item 3; ADR-AMF7 item 1).

    `weights` has one value for each GPU, in the order of the GPUs of the run. The count of a GPU
    comes from the largest-remainder method on `weight × camera count / sum of the weights`. A tie
    goes to the earlier GPU. A None weight or all zero weights make the weights equal. A GPU with
    the count 0 takes one camera from the GPU with the largest count (on a tie, the earlier GPU).
    With fewer cameras than GPUs, camera `j` uses GPU `j`. GPU 0 gets the first cameras, GPU 1 the
    next cameras, and so on.
    """
    cameras, count = len(camera_ids), len(weights)
    if cameras <= count:
        return {camera_id: index for index, camera_id in enumerate(camera_ids)}
    if None in weights or not any(weights):
        weights = [1] * count
    total = sum(weights)
    counts = [weight * cameras // total for weight in weights]
    by_remainder = sorted(range(count), key=lambda index: (-(weights[index] * cameras % total), index))
    for index in by_remainder[: cameras - sum(counts)]:
        counts[index] += 1
    for index in range(count):
        if counts[index] == 0:
            counts[max(range(count), key=lambda other: (counts[other], -other))] -= 1
            counts[index] = 1
    slots = [index for index, size in enumerate(counts) for _ in range(size)]
    return dict(zip(camera_ids, slots, strict=True))


class RunSessions:
    """The sessions of one run. `close()` frees them. `cpu_threads` is the thread count of each session on the CPU EP."""

    def __init__(self, cpu_threads: int | None = None) -> None:
        self.opened: dict[tuple[Any, ...], OpenedSession] = {}
        self.cpu_threads = cpu_threads

    def open(self, node: ResolvedNode, plan: NodePlan, device_key: str | None, batch: int) -> OpenedSession:
        """Return the session of one node on one device at `batch`. Build it when no node of the run has it.

        A sidecar with a fixed batch that is not `batch` gets the batch conversion. When the
        sidecar has no conversion profile, or the extra `onnx` is not installed, the session runs
        the artifact at its own batch, and `run_batches` pads each group.
        """
        from skellytracker.core.detectors.generic.session import open_session

        model = node.model
        batching = model.sidecar.batching
        can_convert = batching.batch_conversion is not None and importlib.util.find_spec("onnx") is not None
        used: int | str = batching.batch if batching.batch == "dynamic" or not can_convert else batch
        device_key = device_key if plan.gpu else None
        key = (plan.artifact_sha256, used, plan.execution_provider, plan.ep_options, device_key)
        if key not in self.opened:
            session, report = open_session(
                model.entry, model.sidecar, model.size, plan.precision, execution_provider=plan.execution_provider,
                batch=None if used in ("dynamic", batching.batch) else batch, ep_options=dict(plan.ep_options), device_key=device_key,
                cpu_threads=self.cpu_threads,
            )
            self.opened[key] = OpenedSession(session, report, used)
        opened = self.opened[key]
        if node.id not in opened.node_ids:
            opened.node_ids.append(node.id)
        return opened

    def partial_placement(self) -> list[PipelineWarning]:
        """Return one warning `ep_partial_placement` for each session with nodes on the CPU EP, on an EP that is not the CPU EP."""
        found = []
        for opened in self.opened.values():
            report = opened.report
            if report.cpu_nodes > 0 and report.ep_name != CPU_EP_NAME:
                found.append(PipelineWarning(
                    EP_PARTIAL_PLACEMENT,
                    f"{', '.join(opened.node_ids)}: {report.cpu_nodes} nodes of the session on '{report.requested_ep}' run on the CPU EP "
                    f"({', '.join(report.cpu_op_types)})",
                    tuple(opened.node_ids),
                    {"nodes_by_ep": dict(report.nodes_by_ep), "cpu_op_types": list(report.cpu_op_types)},
                ))
        return found

    def close(self) -> None:
        """Free each session. A second call does nothing."""
        self.opened.clear()
