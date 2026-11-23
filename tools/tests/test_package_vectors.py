"""The skellytracker functions that `verified_against` names agree with the vector cases.

Each function of the package that a vector file names in `verified_against` still gives the same
results as the cases that list it, and differs where a case does not. An adapter of
`PACKAGE_RUNNERS` runs each function on one case.

This test stays in skellytracker: it imports the package. The vector files and their form checks
are in `tools/tests/test_vectors.py`, which moves to the specs repository with the vector tools.
This file uses the helpers of that file. That file must never import this file.
"""

from __future__ import annotations

import functools
import importlib
import math
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest
from test_vectors import REPO_ROOT, exact_unless_fractional, load, vector_paths

import make_vectors as mv
from vector_form import agrees


def resolve_function(reference: str) -> Any:
    """Return the function named by `path/to/module.py::function`."""
    path, _, name = reference.partition("::")
    assert (REPO_ROOT / path).is_file(), f"no file {path}"
    module = importlib.import_module(
        Path(path).with_suffix("").as_posix().replace("/", ".")
    )
    return getattr(module, name)


# ---------------------------------------------------------------------------
# skellytracker functions named in `verified_against`
# ---------------------------------------------------------------------------

SOURCE_VALUE = 200
LETTERBOX_PAD = 114


def letterbox_runner(function: Any, case: dict[str, Any]) -> dict[str, int] | None:
    """Run `letterbox_preprocess` on a flat image; None when it cannot run the case.

    The function reports only a scale factor, so the geometry is read from the
    padded image: the source value (200) differs from the padding (114). The
    function does not compute the Inverse.
    """
    params = case["params"]
    if "function" in case or params["pad_position"] != "top_left":
        return None  # the function has no Inverse and no `center`
    image = np.full(
        (case["input"]["src_h"], case["input"]["src_w"], 3),
        SOURCE_VALUE,
        dtype=np.uint8,
    )
    try:
        padded, _ratio = function(
            image, tuple(params["target_size"]), pad_value=LETTERBOX_PAD
        )
    except cv2.error:
        return None
    covered = (padded != LETTERBOX_PAD).any(axis=2)
    columns, rows = np.flatnonzero(covered.any(axis=0)), np.flatnonzero(
        covered.any(axis=1)
    )
    return {
        "n_w": len(columns),
        "n_h": len(rows),
        "left": int(columns[0]) if len(columns) else 0,
        "top": int(rows[0]) if len(rows) else 0,
    }


def _axis_extent(mask_axis: np.ndarray) -> tuple[int, int]:
    indexes = np.flatnonzero(mask_axis)
    return int(indexes[0]), int(indexes[-1])


def fit_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    """Run `fit_preprocess` on a flat image.

    A forward case gives the reported geometry, after a check that the warped
    image agrees with it. An `-inverse` case gives `model_xy` mapped through the
    inverted warp matrix of the function: the function has no Inverse. A
    `border` case gives pixel (0, 0), which is in the padding of each such case.
    """
    t_h, t_w = case["params"]["target_size"]
    src_w, src_h = case["input"]["src_w"], case["input"]["src_h"]
    image = np.full((src_h, src_w, 3), SOURCE_VALUE, dtype=np.uint8)
    if case.get("function") == "border":
        padded, _ = function(image, (t_h, t_w), pad_value=case["params"]["pad_value"])
        return {"border": padded[0, 0].tolist()}
    padded, (scale, left, top) = function(image, (t_h, t_w), pad_value=0)

    if case.get("function") == "inverse":
        matrix = np.array([[scale, 0, left], [0, scale, top]], dtype=float)
        model_x, model_y = case["input"]["model_xy"]
        source = cv2.invertAffineTransform(matrix) @ np.array([model_x, model_y, 1.0])
        return {"source_xy": source.tolist()}

    # The warped image agrees with the reported geometry. The edges blend with
    # the border, so allow the blend zone of one source pixel (`scale` pixels).
    assert padded.shape == (t_h, t_w, 3)
    margin = math.ceil(scale) + 1
    covered = (padded > 0).any(axis=2)
    for axis, size, start, length in ((0, t_w, left, src_w), (1, t_h, top, src_h)):
        first, last = _axis_extent(covered.any(axis=axis))
        low, high = max(start, 0.0), min(start + length * scale, size)
        assert math.floor(low) - margin <= first <= math.ceil(low) + 1
        assert math.floor(high) - 2 <= last <= math.ceil(high) + margin
    return {"scale": scale, "left": left, "top": top}


@functools.cache
def validator_sections() -> dict[str, str]:
    """The section of each data-only validator case, by case id. The ids are unique."""
    cases = [
        (case["id"], data["section"])
        for data in (load(path.name) for path in vector_paths())
        for case in data["cases"]
        if case.get("function") == "none"
    ]
    assert len(dict(cases)) == len(cases)
    return dict(cases)


def check_sidecar_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    """Run `check_sidecar` on a data-only validator case. It cannot run a case of another kind.

    The result holds the failed rules of the section of the case. A case with `input.path` holds
    only the rules of the path under the sidecar root: V-common.identity-7 and V-common.identity-8.
    The function gets the landmark schema registry of the package, for V-post.keypoint.score_map-4.
    """
    from skellytracker.core.model_spec.landmark_schemas import load_landmark_schema_registry

    if case.get("function") != "none":
        return None
    relative_path = case["input"].get("path")
    registry = load_landmark_schema_registry()
    failed = {failure.rule for failure in function(case["input"]["sidecar"], relative_path=relative_path, landmark_schemas=registry)}
    if relative_path is not None:
        wanted = failed & {"V-common.identity-7", "V-common.identity-8"}
    else:
        prefix = f"V-{validator_sections()[case['id']]}-"
        wanted = {rule for rule in failed if rule.startswith(prefix)}
    return {"failed": sorted(wanted)}


# ---------------------------------------------------------------------------
# The adapters of the spec processing modules (`processing/pre/` and `processing/post/`)
# ---------------------------------------------------------------------------

PRE = "skellytracker/core/detectors/processing/pre"
POST = "skellytracker/core/detectors/processing/post"
NMS_KEYS = ("iou_threshold", "score_threshold", "class_agnostic", "post_nms_top_k")


def sibling(function: Any, name: str) -> Any:
    """Return another function of the module of `function`."""
    return getattr(sys.modules[function.__module__], name)


def flat_image(case: dict[str, Any], value: int = SOURCE_VALUE) -> np.ndarray:
    return np.full((case["input"]["src_h"], case["input"]["src_w"], 3), value, dtype=np.uint8)


def case_geometry(resize: dict[str, Any], inp: dict[str, Any]) -> Any:
    """The `ResizeGeometry` of the flat `resize` keys of a case, from the resize dispatcher."""
    from skellytracker.core.detectors.processing.pre.preprocess import resize_geometry
    from skellytracker.core.detectors.processing.pre.resize_affine_crop import roi_from_box
    from skellytracker.core.model_spec.model import ResizeSpec

    fields = {key: resize[key] for key in ("method", "pad_position", "rounding") if key in resize}
    roi = None
    if resize["method"] == "affine_crop":
        policy = {key: resize[key] for key in ("expand_ratio", "maintain_aspect_ratio") if key in resize}
        fields["crop_policy"] = policy
        roi = inp["roi"] if "roi" in inp else roi_from_box(inp["bbox_xyxy"])
    return resize_geometry(
        ResizeSpec(**fields), resize.get("target_size"), inp.get("src_w", 0), inp.get("src_h", 0), roi
    )


def letterbox_geometry_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    if "function" in case:
        return None
    params, inp = case["params"], case["input"]
    return function(inp["src_w"], inp["src_h"], params["target_size"], params["pad_position"], params["rounding"])


def letterbox_inverse_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    if case.get("function") != "inverse":
        return None
    params, inp = case["params"], case["input"]
    geometry = sibling(function, "letterbox_geometry")(
        inp["src_w"], inp["src_h"], params["target_size"], params["pad_position"], params["rounding"]
    )
    return {"source_xy": function(inp["model_xy"], geometry, inp["src_w"], inp["src_h"]).tolist()}


def new_fit_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    """Run `fit` on a flat image: the geometry of a forward case, or pixel (0, 0) of a `border` case."""
    from skellytracker.core.detectors.processing.pre.resize_interpolation import border_values

    if case.get("function") == "inverse":
        return None
    target = case["params"]["target_size"]
    if case.get("function") == "border":
        canvas, _ = function(flat_image(case), target, border_values(case["params"]["pad_value"]), cv2.INTER_LINEAR)
        return {"border": canvas[0, 0].tolist()}
    return function(flat_image(case), target, (0.0, 0.0, 0.0), cv2.INTER_LINEAR)[1]


def fit_inverse_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    if case.get("function") != "inverse":
        return None
    inp = case["input"]
    geometry = sibling(function, "fit_geometry")(inp["src_w"], inp["src_h"], case["params"]["target_size"])
    return {"source_xy": function(inp["model_xy"], geometry).tolist()}


def _crop_geometry(crop_geometry: Any, case: dict[str, Any]) -> dict[str, Any]:
    params, inp = case["params"], case["input"]
    roi = inp["roi"] if "roi" in inp else sibling(crop_geometry, "roi_from_box")(inp["bbox_xyxy"])
    return crop_geometry(
        roi, params["target_size"], float(params.get("expand_ratio", 1.25)), params.get("maintain_aspect_ratio", True)
    )


def crop_geometry_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    if "function" in case:
        return None

    def run() -> dict[str, Any]:
        geometry = _crop_geometry(function, case)
        return {**geometry, "matrix": geometry["matrix"].tolist()}

    return mv.outcome(run)


def crop_unproject_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    if case.get("function") != "inverse":
        return None
    matrix = _crop_geometry(sibling(function, "crop_geometry"), case)["matrix"]
    # The form of `expect` has 6 decimals: the inverse of M gives 134.99999999999997 for 135.
    return mv.clean({"source_xy": function(case["input"]["model_xy"], matrix).tolist()}, digits=6)


def affine_crop_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    """Run `affine_crop` on a black image: pixel (0, 0) of a `border` case."""
    from skellytracker.core.detectors.processing.pre.resize_interpolation import border_values

    if case.get("function") != "border":
        return None
    params, inp = case["params"], case["input"]
    roi = inp["roi"] if "roi" in inp else sibling(function, "roi_from_box")(inp["bbox_xyxy"])
    crop, _ = function(
        flat_image(case, 0),
        roi,
        params["target_size"],
        float(params.get("expand_ratio", 1.25)),
        params.get("maintain_aspect_ratio", True),
        border_values(params.get("pad_value", 0)),
        cv2.INTER_LINEAR,
    )
    return {"border": crop[0, 0].tolist()}


def normalize_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    """Run `normalize` on the pixels of a numeric case, with the resolved mode of the spec model."""
    from skellytracker.core.model_spec.model import InputSpec

    if case.get("function") == "none":
        return None
    params = case["params"]
    precision, dtype = params.get("precision", "fp32"), params.get("dtype")
    compute = (params.get("resize") or {}).get("compute_dtype", "uint8")
    pixels = np.asarray(case["input"]["pixels_bgr"], dtype=np.float64)
    if compute == "uint8" and not np.array_equal(pixels, pixels.astype(np.uint8)):
        return None  # these pixels are not an 8-bit image
    spec = InputSpec(
        name="input",
        dtype={precision: dtype or "float32"},
        color_format=params["color_format"],
        normalization=params["normalization"],
        normalization_by_precision=params.get("normalization_by_precision", {}),
    )
    mode = spec.normalization_for(precision)
    values = function(pixels.astype(compute), mode, spec.color_format, dtype)
    return {
        "resolved_mode": mode if isinstance(mode, str) else "custom",
        "channel_order": spec.color_format,
        "values": values.tolist(),
    }


def resize_limit_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    """Run `within_resize_limit` on the two images of a `check_resize` case."""
    if case.get("function") != "check_resize":
        return None
    inp, compute = case["input"], case["params"]["resize"].get("compute_dtype", "uint8")

    def run() -> dict[str, Any]:
        difference, within = function(np.asarray(inp["reference"]), np.asarray(inp["result"]), compute)
        return {"max_difference": difference, "within_limit": within}

    return node_outcome(run)


def simcc_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    def run() -> dict[str, Any]:
        x, y = (np.asarray(case["input"][key], dtype=np.float32) for key in ("simcc_x", "simcc_y"))
        result = function(x, y, case["params"]["target_size"])
        return {
            "bins": result["bins"].tolist(),
            "keypoints": result["keypoints"].tolist(),
            "scores": result["scores"].astype(np.float64).tolist(),
        }

    return mv.outcome(run)


def score_map_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    """Run `map_scores` on a numeric case of `post.keypoint.score_map`, with the block as a `ScoreMapSpec`."""
    from skellytracker.core.model_spec.model import ScoreMapSpec

    if case.get("function") == "none":
        return None
    params = case["params"]

    def run() -> dict[str, Any]:
        raw = np.asarray(case["input"]["raw"], dtype=np.float32)
        scores = function(raw, ScoreMapSpec.model_validate(params["score_map"]), params.get("point_groups"))
        return {"scores": scores.astype(np.float64).tolist()}

    return mv.outcome(run)


def nms_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    """Run `decode_nms` on a numeric case. The box space comes from `resize` of the case (ADR-0PK7)."""
    from skellytracker.core.model_spec.model import ObjectDecodeSpec

    if case.get("function") == "none":
        return None
    params, inp = case["params"], case["input"]
    other = {key: value for key, value in params.items() if key not in (*NMS_KEYS, "classes", "input_size", "resize")}
    decode = ObjectDecodeSpec(selection="nms", nms={key: params[key] for key in NMS_KEYS if key in params}, **other)
    class_indexes = None
    if "rows" in inp:
        table = np.asarray(inp["rows"], dtype=np.float64).reshape(-1, len(inp["fields"]))
        boxes, scores = table[:, 0:4], table[:, inp["fields"].index(params["score_field"])]
        if params.get("class_field") is not None:
            class_indexes = table[:, inp["fields"].index(params["class_field"])]
    else:
        boxes, scores = inp["boxes"], inp["scores"]
    geometry = case_geometry(params["resize"], inp) if "resize" in params else None
    found = function(boxes, scores, class_indexes, decode, params["classes"], params.get("input_size", [1, 1]), geometry)
    return {
        "kept_rows": found["rows"].tolist(),
        "scores": found["scores"].tolist(),
        "class_indices": found["class_indices"].tolist(),
        "boxes_xyxy": found["boxes"].tolist(),
        "boxes_space": "model_input" if geometry is None else "source",
    }


def unproject_points_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    params, inp = case["params"], case["input"]
    if "decoded_xy" not in inp:
        return None
    geometry = case_geometry(params["resize"], inp)
    model = sibling(function, "to_model_pixels")(inp["decoded_xy"], params["scale"], geometry.input_size)
    return {"model_xy": model.tolist(), "source_xy": function(inp["decoded_xy"], params["scale"], geometry).tolist()}


def unproject_boxes_runner(function: Any, case: dict[str, Any]) -> dict[str, Any] | None:
    """Run `unproject_boxes`, then the clamp and the size filter of the object decode, on a box case."""
    from skellytracker.core.detectors.processing.post.object_decode import clamp, size_mask

    params, inp = case["params"], case["input"]
    if "decoded_xyxy" not in inp:
        return None
    geometry = case_geometry(params["resize"], inp)
    corners = np.asarray(inp["decoded_xyxy"], dtype=np.float64).reshape(2, 2)
    model = sibling(function, "to_model_pixels")(corners, params["scale"], geometry.input_size).reshape(4)
    source = function(inp["decoded_xyxy"], params["scale"], geometry)
    output = clamp(source, inp["src_w"], inp["src_h"]) if params.get("clamp_boxes", True) else source
    keep = bool(size_mask(output, params.get("min_box_size")))
    return {"model_xyxy": model.tolist(), "source_xyxy": source.tolist(), "output_xyxy": output.tolist() if keep else None}


# ---------------------------------------------------------------------------
# The adapters of the glue nodes of the pipeline spec (`core/pipelines/_runtime/`)
# ---------------------------------------------------------------------------

NODES = "skellytracker/core/pipelines/_runtime"
ANY_RULE = re.compile(r"V-[a-z][a-z0-9_.]*[a-z0-9]-\d+")


def node_outcome(run: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Return the result of `run`, or its refusal as `{error: <rule ID>}`.

    A params model refuses with a pydantic error, which has the rule ID inside its message.
    """
    try:
        return run()
    except ValueError as error:
        match = ANY_RULE.search(str(error))
        return {"error": match.group(0) if match else "no-rule"}


def node_frame(index: int = 0, timestamp_ms: float | None = 0.0, running_mode: str = "video") -> Any:
    from skellytracker.core.pipelines._runtime.context import FrameContext

    stamp = None if running_mode == "image" or timestamp_ms is None else float(timestamp_ms)
    return FrameContext(index, stamp, 640, 480, running_mode)


def keypoints_info(names: list[str], rows: int, source: str | None = "person", geometry: str | None = "2d") -> Any:
    """The facts of a `keypoints` port with the groups of `names`."""
    from skellytracker.core.pipelines.values import Group, PortInfo

    groups: list[Any] = []
    for column, name in enumerate(names):
        group = name.partition("/")[0]
        if groups and groups[-1].name == group:
            groups[-1] = Group(group, groups[-1].start, groups[-1].count + 1, None)
        else:
            groups.append(Group(group, column, 1, None))
    return PortInfo(
        "keypoints", max_instances=rows, instance_source=source, point_names=tuple(names), groups=tuple(groups), geometry=geometry
    )


def boxes_info(rows: int, source: str | None = "person") -> Any:
    from skellytracker.core.pipelines.values import PortInfo

    return PortInfo("boxes", max_instances=rows, instance_source=source)


def keypoints_value(value: dict[str, Any] | None, info: Any) -> Any:
    """A `keypoints` value from the mapping form of a case. None gives the empty value."""
    from skellytracker.core.pipelines.values import InstanceKeypoints

    if value is None:
        return info.empty()
    rows, points = len(value["present"]), len(info.point_names)
    score = np.array(value["score"], dtype=np.float64).reshape(rows, points)
    return InstanceKeypoints(
        info.point_names,
        np.array(value["xy"], dtype=np.float64).reshape(rows, points, 2),
        score,
        score.copy(),  # a case gives no raw score: raw_score equals score, as for a model with no score map
        np.array(value["instance_score"], dtype=np.float64),
        np.array(value["present"], dtype=bool),
        np.array(value["track_ids"], dtype=np.int64),
        np.array(value["z"], dtype=np.float64).reshape(rows, points) if "z" in value else None,
    )


def keypoints_mapping(value: Any, info: Any) -> dict[str, Any] | None:
    """The mapping form of a `keypoints` value, or None for an empty value."""
    if not value.present.any():
        return None
    # Each input has raw_score = score, so each node that treats raw_score as score keeps them equal (pipeline.outputs item 9).
    np.testing.assert_array_equal(value.raw_score, value.score)
    return {
        "point_names": list(value.point_names),
        "xy": value.xy.tolist(),
        **({} if value.z is None else {"z": value.z.tolist()}),
        "score": value.score.tolist(),
        "instance_score": value.instance_score.tolist(),
        "present": value.present.tolist(),
        "track_ids": value.track_ids.tolist(),
        "instance_source": info.instance_source,
        "geometry": info.geometry,
    }


def xy_keypoints(rows: list[Any], present: list[bool], info: Any, scores: list[Any] | None = None, **row_values: Any) -> Any:
    """A `keypoints` value from rows of [x, y] points. A row can be None or shorter than `P`."""
    from skellytracker.core.pipelines.values import InstanceKeypoints

    out = InstanceKeypoints.empty(info.point_names, info.max_instances)
    for i, row in enumerate(rows):
        if row is None or not present[i]:
            continue
        out.xy[i, : len(row)] = [point[:2] for point in row]
        out.score[i, : len(row)] = out.raw_score[i, : len(row)] = [1.0] * len(row) if scores is None else scores[i]
        out.present[i] = True
        out.instance_score[i] = row_values["instance_score"][i] if "instance_score" in row_values else 0.0
        out.track_ids[i] = row_values["track_ids"][i] if "track_ids" in row_values else -1
    return out


def boxes_value(rows: list[Any] | None, count: int, scores: list[float] | None = None) -> Any:
    """A `boxes` value from rows of [cx, cy, w, h, rotation] or None. None gives the empty value."""
    from skellytracker.core.pipelines.values import InstanceBoxes

    out = InstanceBoxes.empty(count)
    for i, row in enumerate(rows or []):
        if row is not None:
            out.boxes[i], out.present[i] = row, True
            out.instance_score[i] = 0.0 if scores is None else scores[i]
    return out


def boxes_rows(value: Any) -> list[Any]:
    return [row.tolist() if present else None for row, present in zip(value.boxes, value.present, strict=True)]


def first_of_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    from skellytracker.core.pipelines.config import NoParams

    def run() -> dict[str, Any]:
        given = case["input"]["values"]
        infos, values = [], []
        for item in given:
            info = None if item is None else keypoints_info(item["point_names"], len(item["present"]), item["instance_source"], item["geometry"])
            infos.append(info)
            values.append(None if item is None else keypoints_value(item, info))
        typed = next(info for info in infos if info is not None)  # each case has a `keypoints` value
        infos = [typed if info is None else info for info in infos]
        values = [typed.empty() if value is None else value for value in values]
        params = NoParams(**case["params"])
        outputs, _ = sibling(function, "output_info")("node", params, infos)
        plan = sibling(function, "prepare")("node", params, infos, outputs)
        value = function(params, values, None, node_frame(), plan)[0]["value"]
        if not value.present.any():
            return {"value": None}
        return {"value": keypoints_mapping(value, infos[next(i for i, item in enumerate(values) if item is value)])}

    return node_outcome(run)


def assign_keypoints_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    from skellytracker.core.pipelines.config import AssignKeypointsParams

    def run() -> dict[str, Any]:
        inp = case["input"]
        infos, values = {}, {}
        for name in ("target", "source"):
            item = inp[name] or {}
            rows = len(item["present"]) if item else 1
            infos[name] = keypoints_info(inp[f"{name}_names"], rows, item.get("instance_source", name), item.get("geometry", "2d"))
            values[name] = keypoints_value(inp[name], infos[name])
        params, canonical = AssignKeypointsParams(**case["params"]), inp.get("canonical")
        outputs, _ = sibling(function, "output_info")("node", params, infos, canonical)
        if not values["target"].present.any():
            return {"keypoints": None}  # an empty required input: the executor does not call the node
        plan = sibling(function, "prepare")("node", params, infos, outputs, canonical)
        result = function(params, values, None, node_frame(), plan)[0]["keypoints"]
        return {"keypoints": keypoints_mapping(result, outputs["keypoints"])}

    return node_outcome(run)


def merge_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    """The node `merge`: the layout, the canonical names, the schemas and the regions of a case are the facts that the load gives."""
    import dataclasses

    from skellytracker.core.pipelines.config import MERGE_PARTS, MergeParams
    from skellytracker.core.pipelines.values import Group, PortInfo

    def run() -> dict[str, Any]:
        inp = case["input"]
        given = [inp.get(name) for name in ("body", *MERGE_PARTS) if inp.get(name)]
        rows = len(given[0]["present"]) if given else 1
        schemas = inp.get("schemas", {})
        infos, values = {}, {}
        for name in ("body", *MERGE_PARTS):
            if f"{name}_names" not in inp:
                continue
            item = inp.get(name) or {}
            info = keypoints_info(inp[f"{name}_names"], rows, item.get("instance_source", "person"), item.get("geometry", (given[0] if given else {}).get("geometry", "2d")))
            if name in schemas:
                info = dataclasses.replace(info, groups=tuple(dataclasses.replace(group, landmark_schema=schemas[name]) for group in info.groups))
            infos[name], values[name] = info, keypoints_value(inp.get(name), info)
        names, groups = [], []
        for item in inp["layout"]:
            groups.append(Group(item["name"], len(names), len(item["points"]), None))
            names += [f"{item['name']}/{point}" for point in item["points"]]
        layout = PortInfo("keypoints", point_names=tuple(names), groups=tuple(groups))
        regions = {name: tuple(value) for name, value in inp.get("regions", {}).items()}
        params, canonical = MergeParams(**case["params"]), inp.get("canonical")
        outputs, _ = sibling(function, "output_info")("node", params, infos, canonical, layout, regions)
        if not values["body"].present.any():
            return {"keypoints": None}  # an empty required input: the executor does not call the node
        plan = sibling(function, "prepare")("node", params, infos, outputs, canonical)
        result = function(params, values, None, node_frame(), plan)[0]["keypoints"]
        return {"keypoints": keypoints_mapping(result, outputs["keypoints"])}

    return node_outcome(run)


def flag_when_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    """The node `flag_when`: the rows of `value` in the form of node.gate."""
    from skellytracker.core.pipelines.config import FlagWhenParams
    from skellytracker.core.pipelines.values import InstanceBoxes, PortInfo

    def run() -> dict[str, Any]:
        inp = case["input"]
        params, kind, given = FlagWhenParams(**case["params"]), inp["value_type"], inp["value"]
        rows = len(given) if given else 1
        if kind == "keypoints":
            points = max((len(row["xy"]) for row in given or [] if row), default=1)
            info = keypoints_info([f"g/p{column}" for column in range(points)], rows)
            value = xy_keypoints([row and row["xy"] for row in given or [None] * rows], [row is not None for row in given or [None] * rows], info,
                                 [row and row["score"] for row in given or [None] * rows])
        else:
            info = PortInfo("boxes", max_instances=rows, instance_source="person")
            value = InstanceBoxes.empty(rows)
            for i, row in enumerate(given or []):
                if row is not None:
                    value.boxes[i], value.instance_score[i], value.present[i] = [10, 10, 4, 4, 0], row["instance_score"], True
        outputs, _ = sibling(function, "output_info")("node", params, {"value": info})
        assert outputs == {"flag": PortInfo("flag")}
        return {"flag": function(params, {"value": value}, None, node_frame(), None)[0]["flag"]}

    return node_outcome(run)


def gate_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    from skellytracker.core.pipelines.config import GateParams
    from skellytracker.core.pipelines.values import InstanceBoxes, PortInfo

    instance = ("boxes", "keypoints")

    def run() -> dict[str, Any]:
        inp = case["input"]
        value, condition = inp["value"], inp["condition"]
        params = GateParams(**case["params"])
        points = max((len(row["xy"]) for row in (condition if isinstance(condition, list) else []) if row and "xy" in row), default=1)
        infos = {}
        for name, item, other in (("value", value, condition), ("condition", condition, value)):
            kind = inp[f"{name}_type"]
            rows = len(item) if isinstance(item, list) else len(other) if isinstance(other, list) else 1
            if kind == "keypoints":
                infos[name] = keypoints_info([f"g/p{column}" for column in range(points)], rows)
            else:
                infos[name] = PortInfo(
                    kind, max_instances=rows if kind in instance else None, instance_source="person" if kind in instance else None
                )
        outputs, _ = sibling(function, "output_info")("node", params, infos)
        if value is None:
            return {"value": None}  # an empty required input: the executor does not call the node
        rows = infos["condition"].max_instances or 0
        if inp["condition_type"] == "keypoints":
            given = condition or [None] * rows
            sent = xy_keypoints(
                [row and row["xy"] for row in given], [row is not None for row in given], infos["condition"],
                [row and row["score"] for row in given],
            )
        elif inp["condition_type"] == "boxes":
            sent = InstanceBoxes.empty(rows)
            for i, row in enumerate(condition or []):
                if row is not None:
                    sent.boxes[i], sent.instance_score[i], sent.present[i] = 0.0, row["instance_score"], True
        else:
            sent = condition  # a flag
        plan = sibling(function, "prepare")("node", params, infos, outputs)
        result = function(params, {"value": boxes_value(value, len(value)), "condition": sent}, None, node_frame(), plan)[0]["value"]
        if inp["condition_type"] in instance or result.present.any():
            return {"value": boxes_rows(result)}
        return {"value": None}

    return node_outcome(run)


def boxes_from_points_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    from skellytracker.core.pipelines.config import BoxesFromPointsParams

    def run() -> dict[str, Any]:
        inp = case["input"]
        keypoints = inp["keypoints"]
        params = BoxesFromPointsParams(**case["params"])
        rows = 1 if keypoints is None else len(keypoints["present"])
        infos = {"keypoints": keypoints_info(inp["point_names"], rows)}
        floors = [name for name in ("previous_boxes", "reference_boxes") if name in inp]
        infos.update({name: boxes_info(rows) for name in floors})
        sibling(function, "output_info")("node", params, infos)
        if keypoints is None:
            return {"boxes": None}  # an empty required input: the executor does not call the node
        values = {
            "keypoints": xy_keypoints(
                keypoints["xy"], keypoints["present"], infos["keypoints"], keypoints["score"],
                **({"instance_score": keypoints["instance_score"]} if "instance_score" in keypoints else {}),
            ),
            **{name: boxes_value(inp[name], rows) for name in floors},
        }
        result = function(params, values, None, node_frame())[0]["boxes"]
        out = {"boxes": boxes_rows(result)}
        if "instance_score" in keypoints:
            out["instance_score"] = result.instance_score.tolist()
        return out

    return node_outcome(run)


def hold_boxes_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    from skellytracker.core.pipelines.config import HoldBoxesParams

    def run() -> dict[str, Any]:
        inp = case["input"]
        previous, current, keypoints = inp["previous"], inp["current"], inp.get("previous_keypoints")
        params = HoldBoxesParams(**case["params"])
        rows = len(current or previous or [None])
        infos = {"previous": boxes_info(rows), "current": boxes_info(rows)}
        values = {
            "previous": boxes_value(previous, rows, inp.get("previous_instance_score")),
            "current": boxes_value(current, rows, inp.get("current_instance_score")),
        }
        if keypoints is not None:
            points = max(len(row) for row in keypoints["xy"])
            infos["previous_keypoints"] = keypoints_info([f"g/p{column}" for column in range(points)], rows)
            values["previous_keypoints"] = xy_keypoints(keypoints["xy"], keypoints["present"], infos["previous_keypoints"])
        sibling(function, "output_info")("node", params, infos)
        if current is None:
            return {"boxes": None}  # an empty required input: the executor does not call the node
        result = function(params, values, None, node_frame())[0]["boxes"]
        out = {"boxes": boxes_rows(result)}
        if "current_instance_score" in inp:
            out["instance_score"] = result.instance_score.tolist()
        return out

    return node_outcome(run)


def smooth_boxes_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    from skellytracker.core.pipelines.config import SmoothBoxesParams

    def run() -> dict[str, Any]:
        inp = case["input"]
        params = SmoothBoxesParams(**case["params"])
        frames = inp["frames"]
        rows = max(len(frame) for frame in frames if frame is not None)
        stamps = inp.get("timestamps_ms") or [index * 1000.0 / 30.0 for index in range(len(frames))]
        sibling(function, "output_info")("node", params, {"boxes": boxes_info(rows)})
        state, output = None, []
        for index, frame in enumerate(frames):
            context = node_frame(index, stamps[index], inp["running_mode"])
            result, state = function(params, {"boxes": boxes_value(frame, rows)}, state, context)
            output.append(None if frame is None else boxes_rows(result["boxes"]))
        return mv.clean({"boxes": output}, digits=mv.ROUND_DIGITS)  # `expect` has 6 decimals

    return node_outcome(run)


def smooth_keypoints_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    from skellytracker.core.pipelines.config import SmoothKeypointsParams

    def run() -> dict[str, Any]:
        inp = case["input"]
        params = SmoothKeypointsParams(**case["params"])
        frames, mode, with_rows = inp["frames"], inp["running_mode"], "present" in inp
        shaped = next(frame for frame in frames if frame is not None)
        info = keypoints_info([f"g/p{column}" for column in range(len(shaped[0]))], len(shaped))
        stamps = inp.get("timestamps_ms") or [index * 1000.0 / inp.get("fps", 30.0) for index in range(len(frames))]
        sibling(function, "output_info")("node", params, {"keypoints": info})
        state = None
        out: dict[str, list[Any]] = {"keypoints": [], "instance_score": [], "track_ids": []}
        for index, frame in enumerate(frames):
            if frame is None:
                value = info.empty()
            else:
                # A row of a case with no `present` is present when it has a valid point.
                valid = [any(not (math.isnan(x) or math.isnan(y)) for x, y in row) for row in frame]
                row_values = {key: inp[key][index] for key in ("instance_score", "track_ids")} if with_rows else {}
                value = xy_keypoints(frame, inp["present"][index] if with_rows else valid, info, **row_values)
            result, state = function(params, {"keypoints": value}, state, node_frame(index, stamps[index], mode))
            ran = not (frame is None and state is None)  # before its first input, the node does not run
            result = result["keypoints"]
            out["keypoints"].append(result.xy.tolist() if ran else None)
            out["instance_score"].append(result.instance_score.tolist() if ran else None)
            out["track_ids"].append(result.track_ids.tolist() if ran else None)
        # `expect` has 6 decimals, and the tolerance of the file is smaller.
        return mv.clean(out if with_rows else {"keypoints": out["keypoints"]}, digits=mv.ROUND_DIGITS)

    return node_outcome(run)


def redetect_trigger_runner(function: Any, case: dict[str, Any]) -> dict[str, Any]:
    from skellytracker.core.pipelines.config import RedetectTriggerParams

    def run() -> dict[str, Any]:
        inp = case["input"]
        params = RedetectTriggerParams(**case["params"])
        frames = inp["frames"]
        connected = any("previous_keypoints" in frame for frame in frames)
        given = [(frame.get("previous_keypoints") or [], frame["previous_boxes"] or []) for frame in frames]
        rows = max([1, *(max(len(keypoints), len(boxes)) for keypoints, boxes in given)])
        points = max([1, *(len(row) for keypoints, _ in given for row in keypoints if row is not None)])
        info = keypoints_info([f"g/p{column}" for column in range(points)], rows)
        infos = {"previous_boxes": boxes_info(rows), **({"previous_keypoints": info} if connected else {})}
        sibling(function, "output_info")("node", params, infos)
        state, triggered = None, []
        for frame, (keypoints, boxes) in zip(frames, given, strict=True):
            values = {"previous_boxes": boxes_value(boxes, rows)}
            if connected:
                values["previous_keypoints"] = xy_keypoints(
                    keypoints, [row is not None for row in keypoints], info,
                    [row and [point[2] for point in row] for row in keypoints],
                )
            context = node_frame(frame["frame_index"], frame["frame_index"] * 1000.0 / 30.0, inp["running_mode"])
            result, state = function(params, values, state, context)
            triggered.append(result["redetect"])
        return {"triggered": triggered}

    return node_outcome(run)


# The adapter of each skellytracker `verified_against` entry. An adapter runs
# the function on one case and returns its result in the form of `expect`, or
# None when the function cannot run the case.
PACKAGE_RUNNERS: dict[str, Callable[[Any, dict[str, Any]], dict[str, Any] | None]] = {
    "skellytracker/core/detectors/processing/image_preprocessing.py::letterbox_preprocess": (
        letterbox_runner
    ),
    "skellytracker/core/detectors/processing/image_preprocessing.py::fit_preprocess": fit_runner,
    "skellytracker/core/model_spec/rules.py::check_sidecar": check_sidecar_runner,
    f"{PRE}/resize_letterbox.py::letterbox_geometry": letterbox_geometry_runner,
    f"{PRE}/resize_letterbox.py::inverse_points": letterbox_inverse_runner,
    f"{PRE}/resize_fit.py::fit": new_fit_runner,
    f"{PRE}/resize_fit.py::inverse_points": fit_inverse_runner,
    f"{PRE}/resize_affine_crop.py::crop_geometry": crop_geometry_runner,
    f"{PRE}/resize_affine_crop.py::unproject": crop_unproject_runner,
    f"{PRE}/resize_affine_crop.py::affine_crop": affine_crop_runner,
    f"{PRE}/normalize.py::normalize": normalize_runner,
    f"{PRE}/resize_interpolation.py::within_resize_limit": resize_limit_runner,
    f"{POST}/keypoint_decode_simcc.py::decode_simcc": simcc_runner,
    f"{POST}/keypoint_score_map.py::map_scores": score_map_runner,
    f"{POST}/object_selection_nms.py::decode_nms": nms_runner,
    f"{POST}/unprojection.py::unproject_points": unproject_points_runner,
    f"{POST}/unprojection.py::unproject_boxes": unproject_boxes_runner,
    f"{NODES}/node_boxes_from_points.py::run": boxes_from_points_runner,
    f"{NODES}/node_hold_boxes.py::run": hold_boxes_runner,
    f"{NODES}/node_gate.py::run": gate_runner,
    f"{NODES}/node_first_of.py::run": first_of_runner,
    f"{NODES}/node_assign_keypoints.py::run": assign_keypoints_runner,
    f"{NODES}/node_merge.py::run": merge_runner,
    f"{NODES}/node_flag_when.py::run": flag_when_runner,
    f"{NODES}/node_smooth_keypoints.py::run": smooth_keypoints_runner,
    f"{NODES}/node_smooth_boxes.py::run": smooth_boxes_runner,
    f"{NODES}/node_redetect_trigger.py::run": redetect_trigger_runner,
}


def package_entries(data: dict[str, Any]) -> list[str]:
    """The skellytracker entries that a vector file names, at file or case level, in order."""
    entries = [
        *data.get("verified_against", []),
        *(entry for case in data["cases"] for entry in case.get("verified_against", [])),
    ]
    return list(dict.fromkeys(entry for entry in entries if isinstance(entry, str)))


def package_params() -> list[Any]:
    """Each case of each file that names a skellytracker entry, with that entry."""
    return [
        pytest.param(data["section"], entry, case, id=f"{data['section']}:{case['id']}")
        for data in (load(path.name) for path in vector_paths())
        for entry in package_entries(data)
        for case in data["cases"]
    ]


def test_each_package_runner_is_named_in_verified_against() -> None:
    named = {entry for path in vector_paths() for entry in package_entries(load(path.name))}
    assert set(PACKAGE_RUNNERS) == named


@pytest.mark.parametrize(("section", "entry", "case"), package_params())
def test_the_package_agrees_exactly_where_verified_against_names_it(
    section: str, entry: str, case: dict[str, Any]
) -> None:
    """A file or a case that names the function agrees with it; each other case does not."""
    listed = entry in load(f"{section}.yaml").get("verified_against", []) or entry in case.get(
        "verified_against", []
    )
    result = PACKAGE_RUNNERS[entry](resolve_function(entry), case)
    if result is None:
        assert not listed, "a case the function cannot run is not verified"
        return
    tolerance = exact_unless_fractional(section, case["input"], case["expect"])
    assert agrees(result, case["expect"], case, tolerance) == listed, result
