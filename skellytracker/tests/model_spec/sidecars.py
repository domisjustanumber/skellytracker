"""Valid sidecars for the tests of the spec loader, as Python data, and the helpers that change them."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import yaml

from skellytracker.core.model_spec.landmark_schemas import LandmarkGroup, LandmarkSchema

POINTS_3 = ["a", "b", "c"]
POINTS_17 = [f"p{index}" for index in range(17)]
SCHEMAS = {
    "Demo3": LandmarkSchema("Demo3", "test", (LandmarkGroup("body", tuple(POINTS_3)),), {}, Path("Demo3.yaml")),
    "Demo17": LandmarkSchema("Demo17", "test", (LandmarkGroup("body", tuple(POINTS_17)),), {}, Path("Demo17.yaml")),
}
SHA = "a" * 64


def _common(model_id: str, role: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "2.0.0",
        "source": {"name": "demo-exporter", "version": "0.1.0"},
        "model_id": model_id,
        "display_name": "Demo",
        "role": role,
        "license": {
            "model": {"id": "MIT"},
            "training_data": [{"name": "demo-set", "use": "training", "license": {"id": "MIT"}}],
        },
        "batching": {"batch": 3, "batch_conversion": {"profile_id": "static-batch-v1"}},
    }


def _size(model_id: str, name: str, height: int, width: int, output_shapes: list[list[int]], target: bool = True) -> dict[str, Any]:
    size_input: dict[str, Any] = {"shape": [-1, 3, height, width]}
    if target:
        size_input["resize"] = {"target_size": [height, width]}
    artifact = {"filename": f"{model_id}-{name}_b3_fp32.onnx", "sha256": SHA}
    return {"input": size_input, "onnx": {"precision_artifacts": {"fp32": artifact}, "output_shapes": output_shapes}}


def nms_detector() -> dict[str, Any]:
    """An object detector with a `boxes` primary output, a `scores` output, `letterbox` and `nms`."""
    return {
        **_common("demo", ["object_detector"]),
        "input": {
            "name": "input",
            "dtype": {"fp32": "float32"},
            "color_format": "bgr",
            "normalization": "none",
            "resize": {"method": "letterbox", "pad_position": "top_left", "rounding": "half_up", "pad_value": 114},
        },
        "outputs": [
            {"name": "boxes", "dtype": {"fp32": "float32"}, "shape": [-1, -1, 4], "semantic": "boxes"},
            {"name": "scores", "dtype": {"fp32": "float32"}, "shape": [-1, -1], "semantic": "scores"},
        ],
        "object": {
            "classes": ["person"],
            "decode": {
                "selection": "nms",
                "boxes_output": "boxes",
                "scores_output": "scores",
                "nms": {"iou_threshold": 0.65, "score_threshold": 0.01},
            },
        },
        "sizes": {"n": _size("demo", "n", 416, 416, [[3, 3549, 4], [3, 3549]])},
    }


def top_k_detector() -> dict[str, Any]:
    """An object detector with `boxes`, `class_logits`, `stretch` and `top_k`."""
    return {
        **_common("demo", ["object_detector"]),
        "input": {
            "name": "input",
            "dtype": {"fp32": "float32"},
            "color_format": "rgb",
            "normalization": "imagenet",
            "resize": {"method": "stretch"},
        },
        "outputs": [
            {"name": "dets", "dtype": {"fp32": "float32"}, "shape": [-1, 300, 4], "semantic": "boxes"},
            {"name": "labels", "dtype": {"fp32": "float32"}, "shape": [-1, 300, 2], "semantic": "class_logits"},
        ],
        "object": {
            "classes": ["person", "car"],
            "decode": {"selection": "top_k", "boxes_output": "dets", "class_logits_output": "labels", "top_k": 300},
        },
        "sizes": {"n": _size("demo", "n", 384, 384, [[3, 300, 4], [3, 300, 2]])},
    }


def packed_pose_detector() -> dict[str, Any]:
    """A one-stage model with both roles: packed keypoints, `selection: none` and no resize."""
    return {
        **_common("demo-body", ["object_detector", "keypoint_detector"]),
        "input": {"name": "images", "dtype": {"fp32": "float32"}, "color_format": "rgb", "normalization": "unit_float"},
        "outputs": [
            {
                "name": "output0",
                "dtype": {"fp32": "float32"},
                "shape": [-1, 300, 57],
                "semantic": "packed_detections",
                "fields": ["x1", "y1", "x2", "y2", "score", "class_index"],
                "packed_keypoints": {"offset": 6, "components": ["x", "y", "score"]},
            },
        ],
        "object": {
            "classes": ["person"],
            "decode": {"selection": "none", "score_field": "score", "class_field": "class_index", "max_detections": 300},
        },
        "keypoint": {
            "estimator_type": "bottom_up",
            "geometry": "2d",
            "landmark_schema": "Demo17",
            "point_names": list(POINTS_17),
            "skeletons": [{"name": "chain", "edges": [["p0", "p1"]]}],
            "decode": {"method": "coordinate"},
        },
        "sizes": {"n": _size("demo-body", "n", 640, 640, [[3, 300, 57]], target=False)},
    }


def instance_pose_detector() -> dict[str, Any]:
    """A one-stage model with both roles and a separate `instance_keypoints` output."""
    sidecar = packed_pose_detector()
    del sidecar["outputs"][0]["packed_keypoints"]
    sidecar["outputs"][0]["shape"] = [-1, 300, 6]
    sidecar["outputs"].append(
        {
            "name": "keypoints",
            "dtype": {"fp32": "float32"},
            "shape": [-1, 300, 17, 3],
            "semantic": "instance_keypoints",
            "keypoint_axis": 2,
        }
    )
    sidecar["sizes"]["n"]["onnx"]["output_shapes"] = [[3, 300, 6], [3, 300, 17, 3]]
    return sidecar


def simcc_keypoint_detector() -> dict[str, Any]:
    """A top-down keypoint detector with `affine_crop`, a `simcc` decoder and an overlay."""
    return {
        **_common("demo-body", ["keypoint_detector"]),
        "input": {
            "name": "input",
            "dtype": {"fp32": "float32"},
            "color_format": "rgb",
            "normalization": "imagenet",
            "resize": {"method": "affine_crop"},
        },
        "outputs": [
            {"name": "simcc_x", "dtype": {"fp32": "float32"}, "semantic": "simcc_x"},
            {"name": "simcc_y", "dtype": {"fp32": "float32"}, "semantic": "simcc_y"},
        ],
        "keypoint": {
            "estimator_type": "top_down",
            "geometry": "2d",
            "landmark_schema": "Demo3",
            "point_names": list(POINTS_3),
            "skeletons": [{"name": "chain", "edges": [["a", "b"], ["b", "c"]]}],
            "decode": {"method": "simcc"},
            "overlay": {"skeleton": "chain", "parts": {"body": {"edge_color": [0, 255, 0]}}},
        },
        "sizes": {"m": _size("demo-body", "m", 256, 192, [[3, 3, 384], [3, 3, 512]])},
    }


BASES = {
    "nms": nms_detector,
    "top_k": top_k_detector,
    "packed": packed_pose_detector,
    "instance": instance_pose_detector,
    "simcc": simcc_keypoint_detector,
}
MISSING = object()


def changed(sidecar: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of `sidecar` with each dotted path of `changes` set, or removed for `MISSING`.

    A path segment of digits is a list index.
    """
    result = copy.deepcopy(sidecar)
    for path, value in changes.items():
        *parents, last = (int(part) if part.isdigit() else part for part in path.split("."))
        node: Any = result
        for part in parents:
            node = node[part] if isinstance(part, int) else node.setdefault(part, {})
        if value is MISSING:
            del node[last]
        else:
            node[last] = copy.deepcopy(value)
    return result


def write_yaml(path: Path, data: Any) -> str:
    """Write `data` as YAML with LF line endings. Return the SHA-256 of the file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.safe_dump(data, sort_keys=False).encode("utf-8")
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()
