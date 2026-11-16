"""The V- rules of the sidecar spec, checked by `check_sidecar`: one or more cases for each rule ID.

Each case changes a valid sidecar and names the rule that the change breaks. The data-only cases
of the vector files (`function: none`) run here too.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from skellytracker.core.model_spec.errors import SidecarValidationError
from skellytracker.core.model_spec.loader import load_sidecar
from skellytracker.core.model_spec.model import SidecarModel
from skellytracker.core.model_spec.resolution import resolve_sidecar_composition
from skellytracker.core.model_spec.rules import NULL_VALUE, PLACEHOLDER_SHA256, check_sidecar
from skellytracker.tests.model_spec.sidecars import BASES, MISSING, SCHEMAS, changed, write_yaml

VECTORS = Path(__file__).resolve().parents[3] / "specs" / "model-sidecar" / "vectors"
SHA = "b" * 64
LOGITS = {"name": "labels", "dtype": {"fp32": "float32"}, "shape": [-1, -1, 80], "semantic": "class_logits"}
RELATIVE_PATHS = {
    "nms": "detectors/object_detectors/demo/demo.yaml",
    "top_k": "detectors/object_detectors/demo/demo.yaml",
    "packed": "detectors/keypoint_detectors/demo/body/demo-body.yaml",
    "instance": "detectors/keypoint_detectors/demo/body/demo-body.yaml",
    "simcc": "detectors/keypoint_detectors/demo/body/demo-body.yaml",
}


def failed(sidecar: dict[str, Any], **options: Any) -> set[str]:
    options.setdefault("landmark_schemas", SCHEMAS)
    return {failure.rule for failure in check_sidecar(sidecar, **options)}


@pytest.mark.parametrize("base", BASES)
def test_each_base_sidecar_is_valid_and_gives_a_model(base: str) -> None:
    sidecar = BASES[base]()
    assert check_sidecar(sidecar, relative_path=RELATIVE_PATHS[base], landmark_schemas=SCHEMAS) == []
    assert SidecarModel.model_validate(sidecar).model_id == sidecar["model_id"]


# (rule, base, changes). `MISSING` removes a key.
CASES: list[tuple[str, str, dict[str, Any]]] = [
    # format.composition and format.versioning
    ("V-format.composition-5", "nms", {"input.layout": "NCHW"}),
    ("V-format.composition-5", "nms", {"input.resize.preserve_aspect_ratio": True}),
    ("V-format.composition-5", "nms", {"object.decode.requires_nms": True}),
    ("V-format.composition-5", "nms", {"input.resize.target_size": [416, 416]}),
    ("V-format.composition-5", "nms", {"sizes.n.onnx.precision_artifacts.fp32.input_dtype": "float32"}),
    ("V-format.composition-5", "simcc", {"keypoint.requires_object_detector": True}),
    ("V-format.composition-5", "simcc", {"keypoint.decode.is_3d": False}),
    ("V-format.composition-5", "nms", {"batching.batch_axis": 0}),
    (NULL_VALUE, "nms", {"input.resize.pad_value": None}),
    ("V-format.versioning-1", "nms", {"schema_version": 2.0}),
    ("V-format.versioning-1", "nms", {"schema_version": "v2024.09.1019"}),
    ("V-format.versioning-1", "nms", {"schema_version": MISSING}),
    ("V-format.versioning-2", "nms", {"schema_version": "3.0.0"}),
    ("V-format.versioning-2", "nms", {"schema_version": "2.0.0-rc.1"}),
    # common.identity
    ("V-common.identity-1", "nms", {"model_id": "other"}),
    ("V-common.identity-2", "nms", {"role": []}),
    ("V-common.identity-2", "nms", {"role": ["pose_estimator"]}),
    ("V-common.identity-2", "nms", {"role": "object_detector"}),
    ("V-common.identity-3", "nms", {"display_name": MISSING}),
    ("V-common.identity-3", "nms", {"input.name": MISSING}),
    ("V-common.identity-3", "nms", {"outputs": []}),
    ("V-common.identity-4", "nms", {"source": MISSING}),
    ("V-common.identity-4", "nms", {"source.url": "https://example.org"}),
    ("V-common.identity-5", "nms", {"source.version": 1.0}),
    ("V-common.identity-6", "nms", {"source.name": "Demo_Exporter"}),
    # common.sizes_and_artifacts, common.batching and common.batch_conversion
    ("V-common.sizes_and_artifacts-1", "nms", {"sizes": {}}),
    ("V-common.sizes_and_artifacts-2", "nms", {"sizes.n.input.shape": [3, 3, 416, 416]}),
    ("V-common.sizes_and_artifacts-2", "nms", {"sizes.n.input.shape": [-1, 3, -1, -1]}),
    ("V-common.sizes_and_artifacts-3", "nms", {"sizes.n.outputs": []}),
    ("V-common.sizes_and_artifacts-3", "nms", {"sizes.n.input.normalization": "none"}),
    ("V-common.sizes_and_artifacts-3", "nms", {"sizes.n.input.resize.method": "letterbox"}),
    ("V-common.sizes_and_artifacts-3", "nms", {"sizes.n.onnx.batch_artifacts": {}}),
    ("V-common.sizes_and_artifacts-4", "nms", {"sizes.n.input.resize.target_size": [320, 320]}),
    ("V-common.sizes_and_artifacts-5", "nms", {"sizes.n.onnx.precision_artifacts": {}}),
    ("V-common.sizes_and_artifacts-6", "nms", {"sizes.n.onnx.precision_artifacts.int8": {"filename": "a.onnx", "sha256": SHA}}),
    ("V-common.sizes_and_artifacts-7", "nms", {"sizes.n.onnx.precision_artifacts.fp32.filename": MISSING}),
    ("V-common.sizes_and_artifacts-7", "nms", {"sizes.n.onnx.precision_artifacts.fp32.filename": "../a.onnx"}),
    ("V-common.sizes_and_artifacts-7", "nms", {"sizes.n.onnx.precision_artifacts.fp32.url": "https://example.org/a.zip"}),
    ("V-common.sizes_and_artifacts-8", "nms", {"sizes.n.onnx.output_shapes": MISSING}),
    ("V-common.sizes_and_artifacts-8", "nms", {"sizes.n.onnx.output_shapes": [[3, 3549, 4]]}),
    ("V-common.sizes_and_artifacts-8", "nms", {"sizes.n.onnx.output_shapes": [[1, 3549, 4], [1, 3549]]}),
    ("V-common.sizes_and_artifacts-8", "nms", {"sizes.n.onnx.output_shapes": [[3, 3549, 5], [3, 3549]]}),
    ("V-common.sizes_and_artifacts-8", "nms", {"sizes.n.onnx.output_shapes": [[3, 3549], [3, 3549]]}),
    ("V-common.sizes_and_artifacts-8", "nms", {"batching": {"batch": "dynamic"}}),
    ("V-common.sizes_and_artifacts-9", "nms", {"sizes.n.onnx.precision_artifacts.fp32.sha256": MISSING}),
    ("V-common.sizes_and_artifacts-9", "nms", {"sizes.n.onnx.precision_artifacts.fp32.sha256": SHA.upper()}),
    ("V-common.sizes_and_artifacts-11", "nms", {"sizes.n.onnx.precision_artifacts.fp32.sha256": PLACEHOLDER_SHA256}),
    ("V-common.sizes_and_artifacts-12", "nms", {"batching": MISSING}),
    ("V-common.sizes_and_artifacts-12", "nms", {"batching.batch": 2}),
    ("V-common.sizes_and_artifacts-12", "nms", {"batching.batch": True}),
    ("V-common.sizes_and_artifacts-12", "nms", {"batching.batch_conversion": MISSING}),
    ("V-common.batch_conversion-1", "nms", {"batching.batch_conversion.steps": []}),
    ("V-common.batch_conversion-2", "nms", {"batching.batch_conversion.profile_id": "static-batch-v2"}),
    ("V-common.batch_conversion-3", "nms", {"batching.batch": 1}),
    # common.input and common.outputs
    ("V-common.input-1", "nms", {"sizes.n.input.resize.target_size": [416]}),
    ("V-common.input-2", "nms", {"input.dtype": MISSING}),
    ("V-common.input-2", "nms", {"input.dtype": {"fp32": "int8"}}),
    ("V-common.input-2", "nms", {"input.dtype": {"fp16": "float32"}}),
    ("V-common.input-2", "nms", {"input.dtype": {"fp32": "float32", "int8": "uint8"}}),
    ("V-common.input-3", "nms", {"input.resize.method": "pad"}),
    ("V-common.input-3", "nms", {"input.resize.interpolation": "lanczos"}),
    ("V-common.input-4", "nms", {"input.resize.pad_value": "grey"}),
    ("V-common.input-4", "nms", {"input.resize.pad_value": [114, 114]}),
    ("V-common.input-5", "nms", {"input.color_format": "gbr"}),
    ("V-common.outputs-1", "nms", {"outputs.1.name": "boxes"}),
    ("V-common.outputs-2", "nms", {"outputs.0.dtype": {"fp32": "float64"}}),
    ("V-common.outputs-2", "nms", {"outputs.0.dtype": MISSING}),
    ("V-common.outputs-3", "nms", {"outputs.1.semantic": "heatmap"}),
    ("V-common.outputs-3", "nms", {"outputs.1.semantic": "simcc_z"}),
    ("V-common.outputs-3", "nms", {"outputs.1.semantic": "simcc_x"}),
    ("V-common.outputs-3", "simcc", {"outputs.0.semantic": "scores"}),
    # common.license
    ("V-common.license-1", "nms", {"license": MISSING}),
    ("V-common.license-1", "nms", {"license.training_data_unknown_reason": "none"}),
    ("V-common.license-2", "nms", {"license.model.id": ""}),
    ("V-common.license-3", "nms", {"license.model.id": "Not-A-License"}),
    ("V-common.license-3", "nms", {"license.model.id": "LicenseRef-Demo"}),
    ("V-common.license-4", "nms", {"license.model.unknown_reason": "none"}),
    ("V-common.license-5", "nms", {"license.model": {"id": "unknown", "unknown_reason": "No file (checked 2026-11-16)."}}),
    ("V-common.license-6", "nms", {"license.training_data": "unknown"}),
    ("V-common.license-7", "nms", {"license.training_data.0.use": "finetuning"}),
    # pre.resize.* and pre.normalize
    ("V-pre.resize.letterbox-1", "nms", {"input.resize.rounding": MISSING}),
    ("V-pre.resize.letterbox-1", "nms", {"input.resize.pad_position": "bottom"}),
    ("V-pre.resize.letterbox-1", "nms", {"sizes.n.input.resize": MISSING}),
    ("V-pre.resize.letterbox-1", "nms", {"input.resize.crop_policy": {}}),
    ("V-pre.resize.stretch-1", "top_k", {"input.resize.pad_value": 0}),
    ("V-pre.resize.stretch-1", "top_k", {"sizes.n.input.resize": MISSING}),
    ("V-pre.resize.fit-1", "top_k", {"input.resize.method": "fit"}),
    ("V-pre.resize.fit-1", "top_k", {"input.resize": {"method": "fit", "pad_value": 114, "rounding": "half_up"}}),
    ("V-pre.resize.none-1", "packed", {"sizes.n.input.resize": {"target_size": [640, 640]}}),
    ("V-pre.resize.none-1", "packed", {"input.resize": {"method": "none", "compute_dtype": "uint8"}}),
    ("V-pre.resize.affine_crop-1", "simcc", {"input.resize.crop_policy": {"expand_ratio": 0}}),
    ("V-pre.resize.affine_crop-1", "simcc", {"input.resize.crop_policy": {"maintain_aspect_ratio": "yes"}}),
    ("V-pre.resize.affine_crop-2", "simcc", {"input.resize": {"method": "stretch"}}),
    ("V-pre.resize.affine_crop-3", "simcc", {"input.resize.pad_value": 0}),
    ("V-pre.resize.affine_crop-3", "simcc", {"sizes.m.input.resize": MISSING}),
    ("V-pre.resize.interpolation-1", "nms", {"input.resize.compute_dtype": "float16"}),
    ("V-pre.resize.interpolation-2", "nms", {"input.resize.pad_value": 114.5}),
    ("V-pre.resize.interpolation-2", "nms", {"input.resize.pad_value": [0, 0, 256]}),
    ("V-pre.resize.interpolation-2", "nms", {"input.resize.pad_value": -1}),
    ("V-pre.resize.interpolation-2", "nms", {"input.resize.pad_value": 114.5, "input.resize.compute_dtype": "uint8"}),
    ("V-pre.resize.interpolation-2", "simcc", {"input.resize.crop_policy": {"pad_value": [0.5, 0, 0]}}),
    ("V-pre.normalize-1", "nms", {"input.normalization": MISSING}),
    ("V-pre.normalize-1", "nms", {"input.normalization": "imagenet_bgr"}),
    ("V-pre.normalize-1", "nms", {"input.color_format": MISSING}),
    ("V-pre.normalize-1", "nms", {"input.normalization": {"mode": "custom", "mean": [0, 0]}}),
    ("V-pre.normalize-1", "nms", {"input.normalization": {"mode": "custom", "scale": 0}}),
    ("V-pre.normalize-2", "nms", {"input.normalization_by_precision": {"fp32": {"mode": "custom"}}}),
    ("V-pre.normalize-2", "nms", {"input.normalization_by_precision": {"int8": "none"}}),
    ("V-pre.normalize-3", "nms", {"input.dtype": {"fp32": "uint8"}, "input.normalization": "unit_float"}),
    ("V-pre.normalize-3", "nms", {"input.dtype": {"fp32": "uint8"}, "input.resize.compute_dtype": "float32"}),
    # post.object.*
    ("V-post.object.outputs-1", "nms", {"object.decode": MISSING}),
    ("V-post.object.outputs-1", "nms", {"outputs.1.semantic": "boxes"}),
    ("V-post.object.outputs-2", "packed", {"outputs.0.fields": MISSING}),
    ("V-post.object.outputs-2", "packed", {"outputs.0.fields": ["x1", "y1", "x2", "y2", "score"]}),
    ("V-post.object.outputs-2", "instance", {"outputs.0.fields": ["x1", "y1", "x2", "y2", "score"]}),
    ("V-post.object.outputs-2", "nms", {"outputs.0.fields": ["x1", "y1", "x2", "y2"]}),
    ("V-post.object.outputs-3", "nms", {"outputs.0.shape": [-1, -1, 5]}),
    ("V-post.object.outputs-3", "nms", {"outputs.1.shape": [-1, 100]}),
    ("V-post.object.outputs-3", "top_k", {"outputs.1.shape": [-1, 100, 2]}),
    ("V-post.object.outputs-3", "top_k", {"outputs.1.class_axis": 0}),
    ("V-post.object.outputs-3", "top_k", {"outputs.1.shape": [-1, 300, -1]}),
    ("V-post.object.outputs-4", "nms", {"outputs.1.dtype": {"fp32": "uint8"}}),
    ("V-post.object.decode-1", "nms", {"object.decode.boxes_output": "scores"}),
    ("V-post.object.decode-1", "nms", {"object.decode.scores_output": "missing"}),
    ("V-post.object.decode-2", "nms", {"object.decode.score_field": "score"}),
    ("V-post.object.decode-2", "packed", {"object.decode.class_field": "label"}),
    ("V-post.object.decode-3", "nms", {"object.decode.scores_output": MISSING}),
    ("V-post.object.decode-3", "packed", {"object.decode.score_field": MISSING}),
    ("V-post.object.decode-4", "nms", {"object.decode.selection": MISSING}),
    ("V-post.object.decode-4", "nms", {"object.decode.selection": "soft_nms"}),
    ("V-post.object.decode-5", "nms", {"object.decode.box_format": "ltrb"}),
    ("V-post.object.decode-5", "nms", {"object.decode.box_space": "source"}),
    ("V-post.object.decode-5", "top_k", {"object.decode.score_activation": "softmax"}),
    ("V-post.object.decode-5", "nms", {"object.decode.clamp_boxes": "yes"}),
    ("V-post.object.decode-8", "nms", {"object.decode.min_score": 1.5}),
    ("V-post.object.decode-8", "nms", {"object.decode.min_box_size": -1}),
    ("V-post.object.decode-9", "nms", {"object.classes": ["person", "car"]}),
    ("V-post.object.decode-10", "nms", {"object.classes": MISSING}),
    ("V-post.object.decode-10", "nms", {"object.classes": [None]}),
    ("V-post.object.decode-10", "top_k", {"object.classes": ["person", "person"]}),
    ("V-post.object.decode-10", "top_k", {"object.classes": ["person", "car", "dog"]}),
    ("V-post.object.decode-11", "top_k", {"object.decode.keep_classes": ["dog"]}),
    ("V-post.object.decode-11", "top_k", {"object.decode.keep_classes": []}),
    ("V-post.object.selection.none-1", "packed", {"object.decode.top_k": 100}),
    ("V-post.object.selection.none-1", "packed", {"object.decode.max_detections": 100}),
    ("V-post.object.selection.none-1", "packed", {"object.decode.max_detections": 0}),
    ("V-post.object.selection.top_k-1", "top_k", {"object.decode.top_k": MISSING}),
    ("V-post.object.selection.top_k-1", "top_k", {"object.decode.max_detections": 300}),
    ("V-post.object.selection.top_k-1", "packed", {"object.decode.selection": "top_k"}),
    ("V-post.object.selection.nms-1", "nms", {"object.decode.nms": MISSING}),
    ("V-post.object.selection.nms-1", "nms", {"object.decode.nms.iou_threshold": 1.5}),
    ("V-post.object.selection.nms-1", "nms", {"object.decode.max_detections": 100}),
    ("V-post.object.selection.nms-1", "nms", {"object.decode.nms.post_nms_top_k": 0}),
    ("V-post.object.selection.nms-1", "nms", {"object.decode.nms.class_agnostic": "no"}),
    # post.keypoint.*
    ("V-post.keypoint.schema-1", "simcc", {"keypoint.landmark_schema": MISSING}),
    ("V-post.keypoint.schema-1", "simcc", {"keypoint.geometry": MISSING}),
    ("V-post.keypoint.schema-1", "simcc", {"keypoint": MISSING}),
    ("V-post.keypoint.schema-3", "simcc", {"keypoint.estimator_type": "top_down_single_person"}),
    ("V-post.keypoint.schema-3", "simcc", {"keypoint.decode.method": "heatmap"}),
    ("V-post.keypoint.schema-4", "simcc", {"keypoint.point_names": ["a", "b", "a"]}),
    ("V-post.keypoint.schema-5", "simcc", {"keypoint.skeletons.0.edges": [["a", "z"]]}),
    ("V-post.keypoint.schema-5", "simcc", {"keypoint.skeletons": [{"name": "chain", "edges": []}, {"name": "chain", "edges": []}]}),
    ("V-post.keypoint.schema-6", "simcc", {"keypoint.derived_points": {"mid": {"a": 0.5, "b": 0.4}}}),
    ("V-post.keypoint.schema-6", "simcc", {"keypoint.derived_points": {"mid": ["a", "z"]}}),
    ("V-post.keypoint.schema-6", "simcc", {"keypoint.derived_points": {"mid": 5}}),
    ("V-post.keypoint.schema-6", "simcc", {"keypoint.derived_points": {"[prefix]mid": ["a", "b"]}}),
    ("V-post.keypoint.schema-6", "simcc", {"keypoint.derived_points": {"a": "b"}}),
    ("V-post.keypoint.schema-7", "simcc", {"outputs.1.semantic": "simcc_x"}),
    ("V-post.keypoint.schema-7", "simcc", {"keypoint.geometry": "3d", "keypoint.decode.depth_unit": "mm"}),
    ("V-post.keypoint.schema-7", "simcc", {"keypoint.decode.method": "coordinate"}),
    ("V-post.keypoint.schema-7", "packed", {"outputs.0.packed_keypoints": MISSING}),
    ("V-post.keypoint.schema-8", "simcc", {"outputs.0.keypoint_count": 5}),
    ("V-post.keypoint.schema-9", "simcc", {"keypoint.geometry": "4d"}),
    ("V-post.keypoint.schema-9", "simcc", {"keypoint.decode.depth_unit": "mm"}),
    ("V-post.keypoint.schema-9", "packed", {"keypoint.geometry": "3d"}),
    ("V-post.keypoint.schema-10", "simcc", {"keypoint.landmark_schema": "Nothing"}),
    ("V-post.keypoint.schema-10", "simcc", {"keypoint.point_names": ["b", "a", "c"]}),
    ("V-post.keypoint.schema-11", "simcc", {"keypoint.point_names": ["a", "b c", "body/c"]}),
    ("V-post.keypoint.decode.coordinate-1", "simcc", {"keypoint.decode.coordinate_space": "pixel"}),
    ("V-post.keypoint.decode.coordinate-1", "instance", {"keypoint.decode.coordinate_space": "source"}),
    ("V-post.keypoint.bottom_up-1", "instance", {"outputs.1.keypoint_axis": 1}),
    ("V-post.keypoint.bottom_up-1", "instance", {"outputs.1.shape": [-1, 100, 17, 3]}),
    ("V-post.keypoint.bottom_up-2", "packed", {"outputs.0.packed_keypoints.offset": 5}),
    ("V-post.keypoint.bottom_up-2", "packed", {"outputs.0.packed_keypoints.components": ["x", "score"]}),
    ("V-post.keypoint.bottom_up-2", "packed", {"outputs.0.packed_keypoints.components": ["x", "y", "z", "score"]}),
    ("V-post.keypoint.bottom_up-2", "packed", {"outputs.0.packed_keypoints.components": ["x", "y"]}),
    ("V-post.keypoint.bottom_up-2", "packed", {"keypoint.decode.coordinate_space": "pixel"}),
    ("V-post.keypoint.bottom_up-2", "packed", {"keypoint.estimator_type": "top_down"}),
    ("V-post.keypoint.overlay-1", "simcc", {"keypoint.overlay.skeleton": "other"}),
    ("V-post.keypoint.overlay-1", "simcc", {"keypoint.overlay.skeleton": [["a", "z"]]}),
    ("V-post.keypoint.overlay-2", "simcc", {"keypoint.overlay.parts.body.edge_color": MISSING}),
    ("V-post.keypoint.overlay-2", "simcc", {"keypoint.overlay.parts.body.edges": [["a", "b"]], "keypoint.overlay.parts.body.prefix": "a"}),
    ("V-post.keypoint.overlay-2", "simcc", {"keypoint.overlay.parts.other": {"edge_color": [0, 0, 0]}}),
    ("V-post.keypoint.overlay-3", "simcc", {"keypoint.overlay.parts.body.edge_thickness": 0}),
    ("V-post.keypoint.overlay-4", "simcc", {"keypoint.overlay.parts.body.edges": [["a", "c"]]}),
    ("V-post.keypoint.overlay-5", "simcc", {"keypoint.overlay.keypoint_color": [0, 0]}),
    ("V-post.keypoint.overlay-5", "simcc", {"keypoint.overlay.parts.body.edge_color": "green"}),
]


@pytest.mark.parametrize(("rule", "base", "changes"), CASES, ids=[f"{rule}:{index}" for index, (rule, _, _) in enumerate(CASES)])
def test_a_change_fails_its_rule(rule: str, base: str, changes: dict[str, Any]) -> None:
    sidecar = changed(BASES[base](), changes)
    assert rule in failed(sidecar, relative_path=RELATIVE_PATHS[base])


# Changes that keep a sidecar valid.
VALID_CASES: list[tuple[str, dict[str, Any]]] = [
    ("nms", {"input.resize.pad_value": 114.0}),
    ("nms", {"input.resize.pad_value": [0, 114, 255]}),
    ("nms", {"input.resize.pad_value": 114.5, "input.resize.compute_dtype": "float32"}),
    ("nms", {"input.resize.pad_value": MISSING}),
    ("nms", {"batching": {"batch": 1}, "sizes.n.onnx.output_shapes": [[1, 3549, 4], [1, 3549]]}),
    ("nms", {"batching": {"batch": "dynamic"}, "sizes.n.onnx.output_shapes": [[-1, -1, 4], [-1, -1]]}),
    ("nms", {"input.normalization": {"mode": "custom", "scale": 0.5, "mean": [1, 2, 3]}}),
    ("nms", {"input.dtype": {"fp32": "uint8"}}),
    ("nms", {"object.decode.keep_classes": ["person"], "object.decode.min_box_size": 0, "object.decode.min_score": 1}),
    ("nms", {"license.training_data": "unknown", "license.training_data_unknown_reason": "Not public (checked 2026-11-16)."}),
    ("nms", {"license.model": {"id": "CC-BY-4.0 AND LicenseRef-Demo", "url": "https://example.org/terms"}}),
    ("top_k", {"object.classes": ["person", None], "object.decode.keep_classes": ["person"]}),
    ("top_k", {"input.resize": {"method": "fit", "pad_value": [114, 114, 114]}}),
    ("top_k", {"outputs.1.shape": [-1, 2, 300], "outputs.1.class_axis": 1, "sizes.n.onnx.output_shapes": [[3, 300, 4], [3, 2, 300]]}),
    ("packed", {"object.decode.max_detections": MISSING, "outputs.0.shape": [-1, -1, 57], "sizes.n.onnx.output_shapes": [[3, -1, 57]]}),
    ("simcc", {"keypoint.derived_points": {"mid": ["a", "b"], "copy": "c", "lean": {"a": 1.5, "b": -0.5}}, "keypoint.skeletons.0.edges": [["mid", "copy"]]}),
    ("simcc", {"keypoint.overlay.parts.body.edges": [["b", "a"]], "keypoint.overlay.parts.rest": {"edge_color": [1, 2, 3]}}),
    ("simcc", {"keypoint.overlay.skeleton": [["a", "c"]], "keypoint.overlay.parts.body.edges": [["a", "c"]]}),
]


@pytest.mark.parametrize(("base", "changes"), VALID_CASES)
def test_a_valid_change_passes(base: str, changes: dict[str, Any]) -> None:
    sidecar = changed(BASES[base](), changes)
    assert check_sidecar(sidecar, relative_path=RELATIVE_PATHS[base], landmark_schemas=SCHEMAS) == []
    SidecarModel.model_validate(sidecar)


def test_the_placeholder_hash_is_valid_only_in_the_examples() -> None:
    sidecar = changed(BASES["nms"](), {"sizes.n.onnx.precision_artifacts.fp32.sha256": PLACEHOLDER_SHA256})
    assert "V-common.sizes_and_artifacts-11" in failed(sidecar)
    assert failed(sidecar, in_examples=True) == set()


def test_a_prefix_entry_gives_one_derived_point_for_each_prefix() -> None:
    points = ["l_a", "l_b", "r_a", "r_b"]
    sidecar = changed(
        BASES["simcc"](),
        {
            "keypoint.point_names": points,
            "keypoint.landmark_schema": MISSING,
            "keypoint.skeletons": [{"name": "s", "edges": [["l_mid", "r_mid"]]}],
            "keypoint.derived_points": {"prefixes": ["l_", "r_"], "[prefix]mid": ["a", "b"]},
            "keypoint.overlay": MISSING,
        },
    )
    assert failed(sidecar) == {"V-post.keypoint.schema-1"}
    model = SidecarModel.model_validate(changed(sidecar, {"keypoint.landmark_schema": "Demo4"}))
    assert model.keypoint is not None
    assert model.keypoint.derived_points == {"l_mid": ["l_a", "l_b"], "r_mid": ["r_a", "r_b"]}


def test_nms_with_class_logits_fails_only_the_nms_rule_of_its_section() -> None:
    sidecar = changed(BASES["nms"](), {"outputs.1": LOGITS, "object.decode.scores_output": MISSING, "object.decode.class_logits_output": "labels"})
    assert "V-post.object.selection.nms-1" in failed(sidecar)


# ---------------------------------------------------------------------------------------------
# The data-only cases of the vector files
# ---------------------------------------------------------------------------------------------

PATH_RULES = {"V-common.identity-7", "V-common.identity-8"}


def vector_cases() -> list[Any]:
    cases = []
    for path in sorted(VECTORS.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        cases += [
            pytest.param(data["section"], case, id=f"{data['section']}:{case['id']}")
            for case in data["cases"]
            if case.get("function") == "none"
        ]
    return cases


@pytest.mark.skipif(not VECTORS.is_dir(), reason="the vector files are not in an installed package")
@pytest.mark.parametrize(("section", "case"), vector_cases())
def test_a_data_only_vector_case_fails_the_rules_that_it_names(section: str, case: dict[str, Any], tmp_path: Path) -> None:
    """Each case gives a part of a sidecar. The result holds only the rules of the section of the case.

    A case with `input.path` goes to that path under a temporary sidecar root, and the resolver reads
    it from there. Such a case checks only V-common.identity-7 and V-common.identity-8.
    """
    sidecar, relative_path = case["input"]["sidecar"], case["input"].get("path")
    in_section = lambda rule: rule.startswith(f"V-{section}-")  # noqa: E731
    if relative_path is not None:
        write_yaml(tmp_path / relative_path, sidecar)
        sidecar = resolve_sidecar_composition(tmp_path / relative_path, tmp_path)
        in_section = PATH_RULES.__contains__
    rules = {failure.rule for failure in check_sidecar(sidecar, relative_path=relative_path)}
    assert sorted(filter(in_section, rules)) == case["expect"]["failed"]


@pytest.mark.parametrize(
    ("relative_path", "rule"),
    [
        ("detectors/keypoint_detectors/demo/body/other.yaml", "V-common.identity-1"),
        ("detectors/keypoint_detectors/rtmo/body/demo-body.yaml", "V-common.identity-7"),
        ("detectors/keypoint_detectors/demo/demo-body.yaml", "V-common.identity-7"),
        ("detectors/keypoint_detectors/demo/hands/demo-body.yaml", "V-common.identity-8"),
        ("detectors/keypoint_detectors/demo/body7/demo-body.yaml", "V-common.identity-8"),
    ],
)
def test_load_sidecar_checks_the_path_rules(tmp_path: Path, relative_path: str, rule: str) -> None:
    """`load_sidecar` gives the path under the root to the rules of the file name and the folder."""
    write_yaml(tmp_path / relative_path, changed(BASES["simcc"](), {"keypoint.landmark_schema": "COCO_WholeBody"}))
    with pytest.raises(SidecarValidationError) as info:
        load_sidecar(tmp_path / relative_path, tmp_path)
    assert rule in info.value.rules
