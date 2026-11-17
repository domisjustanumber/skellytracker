"""The host load checks of a pipeline config: the checks that need the sidecars, the landmark schema registry or the MediaPipe assets.

Implements: node.onnx_model
Implements: pipeline.graph
Implements: pipeline.outputs

    resolved = resolve(config, user_root)
    resolved.output_schema      # the schema of each output, before frame 0
    resolved.nodes["person"]    # the facts of each port, the model and the `prepare` result of a node

`resolve` raises `ValueError` for a config that fails a load rule. The message starts with the rule
ID. An ONNX file that is absent, or an optional extra that is not installed, is not an error: it
gives the warning `missing_dependency`. `resolve` opens no session and loads no MediaPipe.

The facts of `x@prev` are the facts of `x`, and `x` can be downstream of the node that reads
`x@prev`. `_Resolver.port_facts` gives the order in which the facts come.
"""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from skellytracker.core.detectors.catalog import (
    DetectorEntry,
    DetectorNotFoundError,
    _entry,
    _select,
    model_ports,
    resolve_user_root,
    scan_sidecar_roots,
)
from skellytracker.core.model_spec.artifacts import HashCache
from skellytracker.core.model_spec.errors import SidecarError
from skellytracker.core.model_spec.landmark_schemas import LandmarkSchema, has_bad_point_character, load_landmark_schema_registry
from skellytracker.core.model_spec.loader import is_in_examples
from skellytracker.core.model_spec.model import KeypointSpec, ObjectDecodeSpec, SidecarModel
from skellytracker.core.model_spec.resolution import resolve_sidecar_composition
from skellytracker.core.model_spec.rules import check_sidecar
from skellytracker.core.pipelines import canonical
from skellytracker.core.pipelines._runtime import (
    mediapipe_tasks,
    node_concat,
    node_first_of,
    node_gate,
    node_merge,
    node_redetect_trigger,
    node_boxes_from_points,
    node_hold_boxes,
    node_smooth_keypoints,
    node_smooth_boxes,
)
from skellytracker.core.pipelines.config import FRAME, PORT_REF, VARIADIC, PipelineConfig, _ref_type, input_items
from skellytracker.core.pipelines.values import Group, PortInfo
from skellytracker.core.pipelines.warnings import PipelineWarning

logger = logging.getLogger(__name__)

MODULES: dict[str, Any] = {
    "mediapipe_tasks": mediapipe_tasks,
    "boxes_from_points": node_boxes_from_points,
    "hold_boxes": node_hold_boxes,
    "gate": node_gate,
    "first_of": node_first_of,
    "concat": node_concat,
    "merge": node_merge,
    "smooth_keypoints": node_smooth_keypoints,
    "smooth_boxes": node_smooth_boxes,
    "redetect_trigger": node_redetect_trigger,
}
"""The module of each node type that is not `onnx_model`."""
TEMPORAL_TYPES = ("smooth_boxes", "smooth_keypoints", "redetect_trigger")
INSTANCE_TYPES = ("boxes", "keypoints")
HOLISTIC_GROUPS = ("body", "right_hand", "left_hand", "face")
"""The groups of the output `holistic`, in column order (V-pipeline.outputs-4)."""
MISSING_DEPENDENCY = "missing_dependency"
_FRAME_INFO = PortInfo("image")


@dataclass(frozen=True)
class ResolvedInput:
    """One input of a node. `name` is None for an item of a variadic node. `node` is `frame` for the camera frame."""

    name: str | None
    node: str
    port: str
    prev: bool


@dataclass(frozen=True)
class ResolvedModel:
    """The model of an `onnx_model` node. `entry.artifact(size, precision)` gives the ONNX file of one precision.

    `decode` is `object.decode` of the sidecar with the changes of `object_decode`. It is None for a
    keypoint model. `precisions` are the precisions of the size.
    """

    entry: DetectorEntry
    sidecar: SidecarModel
    key: str
    version: str | None
    sidecar_sha256: str
    size: str
    kind: Literal["object", "top_down", "bottom_up"]
    decode: ObjectDecodeSpec | None
    precisions: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedNode:
    """One node with the facts of its ports. `infos` is the `prepare` result of the node module, or None."""

    id: str
    type: str
    node: Any
    inputs: tuple[ResolvedInput, ...]
    inputs_info: dict[str, PortInfo] | list[PortInfo]
    outputs_info: dict[str, PortInfo]
    infos: Any
    model: ResolvedModel | None


@dataclass(frozen=True)
class ResolvedPipeline:
    """A config that passed the load checks. `order` is the same-frame topological order of the nodes."""

    config: PipelineConfig
    user_root: Path
    nodes: dict[str, ResolvedNode]
    order: tuple[str, ...]
    output_schema: dict[str, dict[str, Any]]
    warnings: tuple[PipelineWarning, ...]
    needs_execution_provider: bool
    has_onnx_model: bool

    def stateful_nodes(self, running_mode: str) -> tuple[str, ...]:
        """Return the nodes that make the pipeline stateful, in `order`. It is empty for a pipeline that is not stateful.

        Implements: pipeline.running

        They are each node with an `@prev` input, and each temporal node upstream of an
        `onnx_model` node. A `mediapipe_tasks` node is temporal only in `video` and `live`.
        """
        upstream: set[str] = set()
        stack = [node_id for node_id in self.order if self.nodes[node_id].type == "onnx_model"]
        while stack:
            for item in self.nodes[stack.pop()].inputs:
                if item.node != FRAME and item.node not in upstream:
                    upstream.add(item.node)
                    stack.append(item.node)
        temporal = TEMPORAL_TYPES + (("mediapipe_tasks",) if running_mode in mediapipe_tasks.TEMPORAL_IN else ())
        return tuple(
            node_id for node_id in self.order
            if any(item.prev for item in self.nodes[node_id].inputs) or (self.nodes[node_id].type in temporal and node_id in upstream)
        )

    def port_info(self, node: str, port: str) -> PortInfo:
        """Return the facts of an output port of a node, or of `frame.image`."""
        return _FRAME_INFO if node == FRAME else self.nodes[node].outputs_info[port]


def _merge(base: Any, changes: Any) -> Any:
    """Return `base` with the nested `changes`: a mapping changes the keys that it gives, each other value replaces."""
    if isinstance(base, dict) and isinstance(changes, dict):
        return {**base, **{key: _merge(base.get(key), value) for key, value in changes.items()}}
    return copy.deepcopy(changes)


def keypoint_port_info(node_id: str, keypoint: KeypointSpec, schema: LandmarkSchema, boxes: PortInfo) -> PortInfo:
    """Return the facts of the port `keypoints` of a top-down keypoint model (pipeline.graph, Behaviour items 7 and 8).

    A schema with one group gives the group the id of the node. The rows and the instance source
    come from the `boxes` input. An edge with a derived point name is not in `edges`.
    """
    from skellytracker.core.detectors.generic.overlay import overlay_edges  # the package `generic` imports the detectors

    bad = [name for name in keypoint.point_names if has_bad_point_character(name)]
    if bad:
        raise ValueError(f"V-pipeline.graph-8: {node_id}: the point name {bad[0]!r} of the sidecar has `/` or whitespace")
    if list(schema.point_names) != keypoint.point_names:
        raise ValueError(f"{node_id}: the point names of the sidecar are not the point names of the landmark schema {schema.name}")
    names: list[str] = []
    groups: list[Group] = []
    group_of: dict[str, str] = {}
    for part in schema.groups:
        name = node_id if len(schema.groups) == 1 else part.name
        groups.append(Group(name, len(names), len(part.points), schema.name))
        names += [f"{name}/{point}" for point in part.points]
        group_of.update(dict.fromkeys(part.points, name))
    edges = tuple(
        (f"{group_of[a]}/{a}", f"{group_of[b]}/{b}") for a, b in overlay_edges(keypoint) if a in group_of and b in group_of
    )
    return PortInfo(
        "keypoints", max_instances=boxes.max_instances, instance_source=boxes.instance_source, point_names=tuple(names),
        groups=tuple(groups), geometry=keypoint.geometry, depth_unit=keypoint.decode.depth_unit if keypoint.geometry == "3d" else None,
        edges=edges, tracked=boxes.tracked,
    )


def canonical_point_names(infos: list[PortInfo], registry: dict[str, LandmarkSchema]) -> dict[str, str]:
    """Return point name -> canonical point name of the points of `infos` (node.merge, Behaviour step 5).

    The canonical name of a point is the name of the first passthrough entry whose source is that
    point, in the region of the group of the point in its schema file.
    """
    found: dict[str, str] = {}
    for info in infos:
        for group in info.groups:
            schema = registry.get(group.landmark_schema or "")
            if schema is None:
                continue
            parts = schema.groups if len(schema.groups) == 1 else [part for part in schema.groups if part.name == group.name]
            for part in parts:
                column = {point: group.start + position for position, point in enumerate(part.points)}
                for canonical_name, source in schema.canonical_mapping.get(part.name, {}).items():
                    if isinstance(source, str) and source in column:
                        found.setdefault(info.point_names[column[source]], canonical_name)
    return found


class _Resolver:
    def __init__(self, config: PipelineConfig, user_root: Path) -> None:
        self.config, self.user_root = config, user_root
        self.by_id: dict[str, Any] = {node.id: node for node in config.nodes}
        self.inputs: dict[str, tuple[ResolvedInput, ...]] = {}
        for node in config.nodes:
            matches = [(name, PORT_REF.match(ref)) for name, ref in input_items(node)]
            self.inputs[node.id] = tuple(
                ResolvedInput(None if name == VARIADIC else name, match["node"], match["port"], match["prev"] is not None)
                for name, match in matches
            )
        self.order: list[str] = []
        for node in config.nodes:
            self._visit(node.id)
        self.warnings: list[PipelineWarning] = []
        self.models: dict[str, ResolvedModel] = {}
        self._sidecars: list[Any] | None = None
        self._registry: dict[str, LandmarkSchema] | None = None

    def _visit(self, node_id: str) -> None:
        """Add `node_id` to `order` after each node that it takes a same-frame input from. `check_structure` refused a cycle."""
        if node_id in self.order:
            return
        for item in self.inputs[node_id]:
            if not item.prev and item.node != FRAME:
                self._visit(item.node)
        self.order.append(node_id)

    @property
    def registry(self) -> dict[str, LandmarkSchema]:
        if self._registry is None:
            try:
                self._registry = load_landmark_schema_registry(self.user_root)
            except SidecarError as exc:
                raise ValueError(f"the landmark schema registry does not load: {exc}") from exc
        return self._registry

    # ---- the onnx_model nodes ------------------------------------------------------------

    def used_ports(self, node_id: str) -> set[str]:
        """Return the output ports of a node that the graph uses: an input of a node, an output or a tap."""
        refs = [ref for node in self.config.nodes for _, ref in input_items(node)]
        refs += [*self.config.outputs.values(), *(tap.port for tap in self.config.instrumentation.taps)]
        return {match["port"] for match in map(PORT_REF.match, refs) if match is not None and match["node"] == node_id}

    def model(self, node: Any) -> ResolvedModel:
        """Do the load checks of one `onnx_model` node, and return its model."""
        params, rule = node.params, "V-node.onnx_model-"
        if self._sidecars is None:
            self._sidecars = scan_sidecar_roots(self.user_root)
        try:
            found = _select(params.key, self._sidecars)
        except DetectorNotFoundError as exc:
            raise ValueError(f"{node.id}: key {params.key!r}: {exc.args[0]}") from None
        if found.model is None:
            raise ValueError(f"{node.id}: the sidecar of {params.key!r} does not load: {found.reason}")
        if params.sidecar_sha256 is None:
            logger.info("%s: the sidecar file of %s has the SHA-256 %s; the node gives no sidecar_sha256", node.id, params.key, found.sha256)
        elif params.sidecar_sha256 != found.sha256:
            raise ValueError(
                f"{rule}1: {node.id}: sidecar_sha256 is {params.sidecar_sha256}, but the sidecar file of {params.key} has {found.sha256}"
            )
        sidecar: SidecarModel = found.model
        if found.reason is not None:
            raise ValueError(f"{node.id}: this release does not run {params.key!r}: {found.reason}")
        if len(set(sidecar.role)) > 1:
            raise ValueError(f"{node.id}: this release does not run {params.key!r}: a model with both roles")
        if params.size not in sidecar.sizes:
            raise ValueError(f"{rule}4: {node.id}: size {params.size!r} is not a size of {params.key}; it has {list(sidecar.sizes)}")
        precisions = tuple(sidecar.sizes[params.size].onnx.precision_artifacts)
        if params.precision is not None and params.precision not in precisions:
            raise ValueError(f"{rule}4: {node.id}: the size {params.size!r} of {params.key} has no precision {params.precision}; it has {list(precisions)}")

        ports = model_ports(sidecar)
        outputs = {port.name for port in ports if port.direction == "output"}
        takes_boxes = any(port.name == "boxes" and port.direction == "input" for port in ports)
        if takes_boxes != ("boxes" in node.inputs):
            raise ValueError(
                f"{rule}2: {node.id}: {params.key} is {'a top-down keypoint model and needs' if takes_boxes else 'not a top-down keypoint model and takes no'} `boxes` input"
            )
        if unused := sorted(self.used_ports(node.id) - outputs):
            raise ValueError(f"{rule}2: {node.id}: the graph uses the ports {unused}, but the role of {params.key} gives {sorted(outputs)}")

        decode = self.decode(node, found, sidecar)
        if "object_detector" in sidecar.role:
            kind = "object"
            if decode.selection != "nms":  # as the generic object detector
                raise ValueError(f"{node.id}: this release has no decode for object.decode.selection: {decode.selection}")
            # shortcut: only the two `nms` limits, the release runs no other selection mode; add `top_k` and `none` with their decode
            limit = decode.nms.post_nms_top_k
            if limit is None:
                primary = next(
                    index for index, spec in enumerate(sidecar.outputs)
                    if spec.semantic in ("packed_detections", "boxes") and decode.boxes_output in (None, spec.name)
                )
                rows = sidecar.sizes[params.size].onnx.output_shapes[primary][1]
                limit = rows if rows > 0 else None
            if limit is not None and params.max_instances > limit:
                raise ValueError(f"{rule}5: {node.id}: max_instances {params.max_instances} is more than the limit {limit} of {params.key}")
        else:
            kind = "bottom_up" if sidecar.keypoint.estimator_type == "bottom_up" else "top_down"

        cache = HashCache()
        entry = _entry(found, cache)
        cache.save()
        # with no `precision`, the load warns only when no artifact of the size is usable (pipeline.running, Behaviour item 8)
        wanted = [entry.artifact(params.size, precision) for precision in ([params.precision] if params.precision else precisions)]
        if not any(artifact.available for artifact in wanted):
            files = [artifact.filename for artifact in wanted]
            self.warnings.append(PipelineWarning(
                MISSING_DEPENDENCY, f"{node.id}: {params.key}: {wanted[0].unavailable_reason}", (node.id,),
                {"files": files, "key": found.key},
            ))
        return ResolvedModel(entry, sidecar, found.key, found.version, found.sha256, params.size, kind, decode, precisions)

    def decode(self, node: Any, found: Any, sidecar: SidecarModel) -> ObjectDecodeSpec | None:
        """Return `object.decode` of the sidecar with the changes of `object_decode` (V-node.onnx_model-3)."""
        changes, rule = node.params.object_decode, f"V-node.onnx_model-3: {node.id}: "
        if sidecar.object is None:
            if changes:
                raise ValueError(f"{rule}{node.params.key} has no object.decode block, but object_decode gives {sorted(changes)}")
            return None
        if not changes:
            return sidecar.object.decode
        # The changed block must pass the rules and the model of the sidecar spec, as the block of a sidecar does.
        resolved = copy.deepcopy(resolve_sidecar_composition(found.path, found.root))
        resolved["object"]["decode"] = _merge(resolved["object"]["decode"], changes)
        if failures := check_sidecar(resolved, in_examples=is_in_examples(found.path)):
            raise ValueError(rule + "; ".join(str(failure) for failure in failures))
        try:
            return ObjectDecodeSpec.model_validate(resolved["object"]["decode"])
        except ValidationError as exc:
            raise ValueError(rule + "; ".join(f"object.decode.{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors())) from exc

    # ---- the facts of the ports ----------------------------------------------------------

    def gather(self, node_id: str, facts: dict[str, dict[str, PortInfo]], pending: str) -> Any:
        """Return the facts of the inputs of a node: a list for a variadic node, else a mapping.

        An input is pending when its node has no facts yet. `pending` tells what to do with it:
        `full` returns None, `omit` leaves the input out, and `placeholder` gives it a `PortInfo`
        with only its port type.
        """
        found: list[tuple[str | None, PortInfo]] = []
        for item in self.inputs[node_id]:
            if item.node == FRAME:
                info = _FRAME_INFO
            elif item.node in facts:
                info = facts[item.node][item.port]
            elif pending == "full":
                return None
            elif pending == "omit":
                continue
            else:
                info = PortInfo(_ref_type(f"{item.node}.{item.port}", self.by_id))
            found.append((item.name, info))
        if isinstance(self.by_id[node_id].inputs, list):
            return [info for _, info in found]
        return dict(found)

    def node_facts(self, node: Any, inputs: Any) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
        """Return the facts of the output ports of a node and its load warnings. It does the load checks of the node."""
        if node.type == "merge":
            return node_merge.output_info(node.id, node.params, inputs, canonical=canonical_point_names(list(inputs.values()), self.registry))
        if node.type != "onnx_model":
            return MODULES[node.type].output_info(node.id, node.params, inputs)
        model, rows = self.models[node.id], node.params.max_instances
        if model.kind == "object":
            return {"boxes": PortInfo("boxes", max_instances=rows, instance_source=node.id, class_names=tuple(model.sidecar.object.classes))}, []
        keypoint = model.sidecar.keypoint
        if keypoint.landmark_schema not in self.registry:
            raise ValueError(f"{node.id}: the landmark schema {keypoint.landmark_schema!r} is not in the registry")
        return {"keypoints": keypoint_port_info(node.id, keypoint, self.registry[keypoint.landmark_schema], inputs["boxes"])}, []

    def port_facts(self) -> dict[str, dict[str, PortInfo]]:
        """Return the facts of the output ports of each node, before the last pass checks them.

        A node whose inputs all have facts gets its facts. When no node is in that state, one node
        gets provisional facts from a call with its pending inputs left out. When no such call
        works, one node gets them from a call with a placeholder for each pending input. `resolve`
        then runs each node again with all its inputs, and the result must be the same.
        """
        facts: dict[str, dict[str, PortInfo]] = {}
        while len(facts) < len(self.order):
            before = len(facts)
            for node_id in self.order:
                if node_id not in facts and (inputs := self.gather(node_id, facts, "full")) is not None:
                    facts[node_id] = self.node_facts(self.by_id[node_id], inputs)[0]
            for pending in ("omit", "placeholder"):
                for node_id in self.order:
                    if len(facts) > before:
                        break
                    if node_id not in facts:
                        try:
                            facts[node_id] = self.node_facts(self.by_id[node_id], self.gather(node_id, facts, pending))[0]
                        except (ValueError, LookupError):
                            pass  # the node needs a pending input
            if len(facts) == before:
                raise ValueError(_unresolved([node_id for node_id in self.order if node_id not in facts]))
        return facts

    def run(self) -> ResolvedPipeline:
        config = self.config
        for node in config.nodes:
            if node.type == "onnx_model":
                self.models[node.id] = self.model(node)
        tasks = tuple(node.id for node in config.nodes if node.type == "mediapipe_tasks")
        if tasks and (extra := mediapipe_tasks.missing_extra()) is not None:
            self.warnings.append(PipelineWarning(
                MISSING_DEPENDENCY, f"{', '.join(tasks)}: the extra `{extra}` is not installed (`pip install skellytracker[{extra}]`)",
                tasks, {"extra": extra},
            ))

        facts = self.port_facts()
        nodes: dict[str, ResolvedNode] = {}
        for node_id in self.order:  # the pass that checks the rules: each node with all its inputs
            node = self.by_id[node_id]
            inputs = self.gather(node_id, facts, "full")
            outputs, found = self.node_facts(node, inputs)
            if outputs != facts[node_id]:
                raise ValueError(_unresolved([node_id]))
            self.warnings += [
                PipelineWarning(item["code"], item["message"], tuple(item.get("node_ids", (node_id,))), dict(item.get("details", {})))
                for item in found
            ]
            infos, module = None, MODULES.get(node.type)
            if node.type == "merge":
                infos = node_merge.prepare(node_id, node.params, inputs, outputs, canonical=canonical_point_names(list(inputs.values()), self.registry))
            elif hasattr(module, "prepare"):
                infos = module.prepare(node_id, node.params, inputs, outputs)
            nodes[node_id] = ResolvedNode(node_id, node.type, node, self.inputs[node_id], inputs, outputs, infos, self.models.get(node_id))

        self.check_rows(nodes)
        self.check_groups(nodes)
        models = [node for node in config.nodes if node.type == "onnx_model"]
        return ResolvedPipeline(
            config=config, user_root=self.user_root, nodes=nodes, order=tuple(self.order), output_schema=self.output_schema(nodes),
            warnings=tuple(self.warnings), needs_execution_provider=any(node.params.execution_provider is None for node in models),
            has_onnx_model=bool(models),
        )

    # ---- the rules of the whole graph ----------------------------------------------------

    def check_rows(self, nodes: dict[str, ResolvedNode]) -> None:
        """Check that each instance port has its rows and its instance source, and V-pipeline.graph-11."""
        for node in nodes.values():
            for port, info in node.outputs_info.items():
                if info.port_type in INSTANCE_TYPES and (info.max_instances is None or info.instance_source is None):
                    raise ValueError(_unresolved([node.id]) + f" The port {node.id}.{port} has no instance source.")
        for node in nodes.values():
            infos = list(node.inputs_info.values()) if isinstance(node.inputs_info, dict) else node.inputs_info
            for item, info in zip(node.inputs, infos, strict=True):
                if (node.type in TEMPORAL_TYPES or item.prev) and info.port_type in INSTANCE_TYPES and info.max_instances != 1:
                    ref = f"{item.node}.{item.port}{'@prev' if item.prev else ''}"
                    raise ValueError(
                        f"V-pipeline.graph-11: {node.id}: the input {ref} has I = {info.max_instances}; "
                        f"each input of a temporal node and each `@prev` input must have I = 1"
                    )

    def check_groups(self, nodes: dict[str, ResolvedNode]) -> None:
        """Check V-pipeline.graph-10: the groups that the nodes of the file make have unique names."""
        made: dict[str, str] = {}
        for node in nodes.values():
            names: list[str] = []
            if node.type in ("onnx_model", "mediapipe_tasks"):
                names = [group.name for info in node.outputs_info.values() for group in info.groups]
            elif node.type == "merge":
                target = {group.name for group in node.inputs_info["target"].groups}
                names = [slot for slot in node.node.params.slots if slot not in target]
            for name in names:
                if name in made:
                    raise ValueError(f"V-pipeline.graph-10: the nodes {made[name]} and {node.id} both make the group {name!r}")
                made[name] = node.id

    def output_schema(self, nodes: dict[str, ResolvedNode]) -> dict[str, dict[str, Any]]:
        """Return the output schema of the delivered values, and check V-pipeline.outputs-2 and the groups of V-pipeline.outputs-4.

        For `wholebody` and `holistic`, `point_names`, `groups` and `edges` are those of the canonical form.
        """
        schema: dict[str, dict[str, Any]] = {}
        for name, ref in self.config.outputs.items():
            node_id, _, port = ref.partition(".")
            info = nodes[node_id].outputs_info[port]
            entry: dict[str, Any] = {"port_type": info.port_type}
            if info.port_type == "keypoints":
                repeated = sorted({point for point in info.point_names if info.point_names.count(point) > 1})
                if repeated:
                    raise ValueError(f"V-pipeline.outputs-2: the output {name!r} has the point names {repeated} more than one time")
                names = [group.name for group in info.groups]
                if (name == "wholebody" and "body" not in names) or (name == "holistic" and names != list(HOLISTIC_GROUPS)):
                    wanted = "a group body" if name == "wholebody" else f"exactly the groups {list(HOLISTIC_GROUPS)}"
                    raise ValueError(f"V-pipeline.outputs-4: the output {name} ({ref}) must have {wanted}; it has the groups {names}")
                plan = canonical._plan(info.groups, info.point_names, self.user_root)
                entry["point_names"] = list(plan.names)
                entry["groups"] = [
                    {"name": group.name, "start": group.start, "count": group.count, "landmark_schema": group.landmark_schema}
                    for group in plan.groups
                ]
                entry["geometry"] = info.geometry
                if info.geometry == "3d":
                    entry["depth_unit"] = info.depth_unit
            if info.port_type == "boxes":
                entry["class_names"] = None if info.class_names is None else list(info.class_names)
            entry.update(max_instances=info.max_instances, tracked=info.tracked, instance_source=info.instance_source)
            if info.port_type == "keypoints":
                entry["edges"] = [list(edge) for edge in canonical.canonical_edges(info.groups, info.point_names, info.edges, self.user_root)]
            schema[name] = entry
        return schema


def _unresolved(node_ids: list[str]) -> str:
    return (
        f"the load cannot find the port facts of the nodes {node_ids}: "
        "their rows and their point names depend only on `@prev` values of the nodes themselves."
    )


def resolve(config: PipelineConfig, user_root: Path | str | None = None) -> ResolvedPipeline:
    """Do each load check of `config` that needs the sidecars, the registry or the MediaPipe assets.

    Implements: node.onnx_model
    Implements: pipeline.graph
    Implements: pipeline.outputs

    `user_root` is the user root of the catalog. Raise `ValueError` for a config that fails a rule.
    The message starts with the rule ID, or names the node when no rule has the check.
    """
    return _Resolver(config, resolve_user_root(user_root)).run()


def sidecar_hashes(config: PipelineConfig, user_root: Path | str | None = None) -> dict[str, str]:
    """Return node id -> the SHA-256 of the sidecar file that `key` resolves, for each `onnx_model` node."""
    nodes = [node for node in config.nodes if node.type == "onnx_model"]
    sidecars = scan_sidecar_roots(user_root) if nodes else []
    found: dict[str, str] = {}
    for node in nodes:
        try:
            found[node.id] = _select(node.params.key, sidecars).sha256
        except DetectorNotFoundError as exc:
            raise ValueError(f"{node.id}: key {node.params.key!r}: {exc.args[0]}") from None
    return found


__all__ = [
    "MISSING_DEPENDENCY",
    "ResolvedInput",
    "ResolvedModel",
    "ResolvedNode",
    "ResolvedPipeline",
    "canonical_point_names",
    "keypoint_port_info",
    "resolve",
    "sidecar_hashes",
]
