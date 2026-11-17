"""The validation rules of the sidecar spec, checked on a resolved sidecar.

`check_sidecar` takes the tree that `resolve_sidecar_composition` returns and gives one `Failure`
for each failed check, with the rule ID `V-<section-id>-<n>` of the spec. It reads each field in its
one place of the current spec text. A rule that reads a block checks only a block that is present,
so the function can also check a part of a sidecar, as the data-only cases of the vector files do.
The rule that makes a block required fails when the block is absent.

These rules are not here:

- `V-format.composition-1` to `-4` and `-6`: `resolution.py` checks them on the files.
- `V-common.sizes_and_artifacts-10`: the catalog checks the bytes of an ONNX file.
- `V-post.keypoint.landmark_schema-1` to `-4` and `V-post.keypoint.canonical_mapping-1`:
  `landmark_schemas.py` checks them on the schema files.
- `V-common.outputs-4`: a size entry cannot hold an output (`V-common.sizes_and_artifacts-3`), and
  `V-common.sizes_and_artifacts-8` gives each size one shape for each output.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

from skellytracker.core.model_spec.errors import Failure
from skellytracker.core.model_spec.landmark_schemas import (
    LandmarkSchema,
    has_bad_point_character,
    source_names,
)
from skellytracker.core.model_spec.resolution import HEX64
from skellytracker.core.model_spec.spdx import has_license_ref, is_spdx_expression
from skellytracker.core.model_spec.versioning import check_schema_version

PLACEHOLDER_SHA256 = "0" * 64
NULL_VALUE = "format.composition:null"
"""The rule name of a field with the value null. The Behaviour text gives this rule no ID."""

PRECISIONS = ("fp32", "fp16")
ROLES = ("object_detector", "keypoint_detector")
INPUT_DTYPES = ("float32", "float16", "uint8")
OUTPUT_DTYPES = ("float32", "float16", "uint8", "int8")
FLOAT_DTYPES = ("float32", "float16")
RESIZE_METHODS = ("letterbox", "stretch", "fit", "affine_crop", "none")
INTERPOLATIONS = ("linear", "area", "cubic", "nearest")
COMPUTE_DTYPES = ("uint8", "float32")
NORMALIZATION_MODES = ("none", "unit_float", "imagenet")
DETECTION_SEMANTICS = ("packed_detections", "boxes", "scores", "class_logits")
KEYPOINT_SEMANTICS = ("simcc_x", "simcc_y", "keypoint_coordinates", "instance_keypoints")
PRIMARY_SEMANTICS = ("packed_detections", "boxes")
SELECTIONS = ("none", "top_k", "nms")
BOX_FORMATS = ("xyxy", "xywh", "cxcywh")
COORDINATE_SPACES = ("pixel", "normalized_01", "normalized_11")
SCORE_ACTIVATIONS = ("none", "sigmoid")
ESTIMATOR_TYPES = ("top_down", "bottom_up")
TOP_DOWN_TYPES = ESTIMATOR_TYPES[:1]
DECODE_METHODS = ("simcc", "coordinate")
DEPTH_UNITS = ("m", "mm", "pixel")
PACKED_COMPONENTS = ("x", "y", "z", "score")
BATCH_CONVERSION_PROFILES = ("static-batch-v1",)
BODY_REGIONS = ("hand", "face", "body", "wholebody")
PREFIX_TOKEN = "[prefix]"  # noqa: S105 (the marker of a derived point for each prefix)

_TOKENS = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_KEYPOINT_SET = re.compile(r"[a-z]+([1-9][0-9]*)")
_KEYPOINT_BRANCH = ("detectors", "keypoint_detectors")

_COMPOSITION_5 = "V-format.composition-5"
_TOP_KEYS = {
    "schema_version", "source", "model_id", "display_name", "role", "license", "input", "batching",
    "outputs", "object", "keypoint", "sizes",
}
_INPUT_KEYS = {"name", "dtype", "color_format", "normalization", "normalization_by_precision", "resize"}
_RESIZE_KEYS = {"method", "pad_value", "pad_position", "rounding", "interpolation", "compute_dtype", "crop_policy"}
_CROP_POLICY_KEYS = {"expand_ratio", "maintain_aspect_ratio", "pad_value"}
_OUTPUT_KEYS = {
    "name", "dtype", "shape", "semantic", "fields", "class_axis", "packed_keypoints", "keypoint_axis",
    "keypoint_count",
}
_ARTIFACT_KEYS = {"filename", "sha256", "url", "url_sha256"}
_OBJECT_DECODE_KEYS = {
    "selection", "boxes_output", "scores_output", "box_format", "box_space", "score_field", "class_field",
    "keep_classes", "min_score", "clamp_boxes", "min_box_size", "max_detections", "class_logits_output",
    "score_activation", "top_k", "nms",
}
_NMS_KEYS = {"iou_threshold", "score_threshold", "class_agnostic", "post_nms_top_k"}
_KEYPOINT_KEYS = {
    "estimator_type", "geometry", "landmark_schema", "point_names", "skeletons", "derived_points",
    "decode", "overlay",
}
_KEYPOINT_DECODE_KEYS = {"method", "depth_unit", "coordinate_space"}
_OVERLAY_KEYS = {"skeleton", "parts", "keypoint_color"}
_OVERLAY_PART_KEYS = {"edges", "prefix", "edge_color", "edge_thickness", "keypoint_color"}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _positive_int(value: Any) -> bool:
    return _is_int(value) and value > 0


def _in_unit_range(value: Any) -> bool:
    return _is_number(value) and 0 <= value <= 1


def _dict(value: Any) -> dict[Any, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _texts(value: Any) -> list[str] | None:
    """Return `value` when it is a list of non-empty strings, else None."""
    return value if isinstance(value, list) and all(_is_text(item) for item in value) else None


def _is_one_of(value: Any, allowed: tuple[Any, ...]) -> bool:
    return isinstance(value, str) and value in allowed


def _shape(value: Any) -> list[int] | None:
    """Return a tensor shape: a non-empty list in which each dim is -1 or a positive int."""
    if isinstance(value, list) and value and all(_is_int(d) and (d == -1 or d > 0) for d in value):
        return value
    return None


def _pad_values(value: Any) -> list[Any] | None:
    """Return the numbers of a pad value (a number, or 3 numbers), or None when its form is not valid."""
    if _is_number(value):
        return [value]
    if isinstance(value, list) and len(value) == 3 and all(_is_number(item) for item in value):
        return value
    return None


def _edge(value: Any) -> frozenset[str] | None:
    """Return one skeleton edge `[name, name]` as a set. An edge has no direction."""
    if isinstance(value, list) and len(value) == 2 and all(_is_text(item) for item in value):
        return frozenset(value)
    return None


def expand_derived_points(derived: dict[Any, Any]) -> dict[str, Any]:
    """Return the derived points with each `[prefix]` entry written once for each prefix.

    Implements: post.keypoint.schema

    The key `prefixes` of the map holds the prefix list. The prefix applies to the derived name and
    to each source. An entry without `[prefix]` is literal. Raise `ValueError` for a `[prefix]`
    entry with no prefix list, and for a name that the expansion gives two times.
    """
    prefixes = _texts(derived.get("prefixes", []))
    if prefixes is None:
        raise ValueError("prefixes must be a list of strings")
    expanded: dict[str, Any] = {}
    for key, entry in derived.items():
        if key == "prefixes":
            continue
        marked = isinstance(key, str) and key.startswith(PREFIX_TOKEN)
        if marked and not prefixes:
            raise ValueError(f"{key!r} uses [prefix], but the map has no prefixes list")
        for prefix in prefixes if marked else [""]:
            name = prefix + key[len(PREFIX_TOKEN):] if marked else key
            if name in expanded:
                raise ValueError(f"the derived point name {name!r} is not unique")
            if isinstance(entry, str):
                expanded[name] = prefix + entry
            elif isinstance(entry, list):
                expanded[name] = [prefix + item if isinstance(item, str) else item for item in entry]
            elif isinstance(entry, dict):
                expanded[name] = {(prefix + k if isinstance(k, str) else k): v for k, v in entry.items()}
            else:
                expanded[name] = entry
    return expanded


def check_sidecar(
    sidecar: dict[Any, Any],
    *,
    relative_path: str | None = None,
    landmark_schemas: Mapping[str, LandmarkSchema] | None = None,
    in_examples: bool = False,
) -> list[Failure]:
    """Return the failed rules of a resolved sidecar. An empty list means that the sidecar is valid.

    Implements: format.composition
    Implements: format.file_layout
    Implements: common.identity
    Implements: common.sizes_and_artifacts
    Implements: common.batching
    Implements: common.batch_conversion
    Implements: common.input
    Implements: common.outputs
    Implements: common.license
    Implements: pre.resize.letterbox
    Implements: pre.resize.stretch
    Implements: pre.resize.fit
    Implements: pre.resize.none
    Implements: pre.resize.affine_crop
    Implements: pre.resize.interpolation
    Implements: pre.normalize
    Implements: post.object.outputs
    Implements: post.object.decode
    Implements: post.object.selection.none
    Implements: post.object.selection.top_k
    Implements: post.object.selection.nms
    Implements: post.keypoint.schema
    Implements: post.keypoint.decode.simcc
    Implements: post.keypoint.score_map
    Implements: post.keypoint.decode.coordinate
    Implements: post.keypoint.bottom_up
    Implements: post.keypoint.overlay
    Implements: post.unprojection

    `relative_path` is the path of the sidecar under its sidecar root, with `/`. With it, the
    function checks V-common.identity-1, -7 and -8. `landmark_schemas` is the registry. With it, the
    function checks V-post.keypoint.schema-10 and the group names of V-post.keypoint.score_map-4.
    `in_examples` is True for a file under
    `specs/model-sidecar/examples/`, where the placeholder `sha256` is valid.
    """
    checker = _Checker(sidecar, relative_path, landmark_schemas, in_examples)
    checker.run()
    return checker.failures


class _Checker:
    def __init__(
        self,
        sidecar: dict[Any, Any],
        relative_path: str | None,
        landmark_schemas: Mapping[str, LandmarkSchema] | None,
        in_examples: bool,
    ) -> None:
        self.s = sidecar
        self.relative_path = relative_path
        self.landmark_schemas = landmark_schemas
        self.in_examples = in_examples
        self.failures: list[Failure] = []

        self.roles = _texts(sidecar.get("role")) or []
        self.input = _dict(sidecar.get("input"))
        self.resize = _dict(self.input.get("resize"))
        # An absent `input.resize` has the effect of `method: none`.
        self.method = self.resize.get("method") if "resize" in self.input else "none"
        self.sizes = {name: entry for name, entry in _dict(sidecar.get("sizes")).items() if isinstance(entry, dict)}
        self.outputs = [output for output in _list(sidecar.get("outputs")) if isinstance(output, dict)]
        self.batch = _dict(sidecar.get("batching")).get("batch")
        self.object = _dict(sidecar.get("object"))
        self.object_decode = _dict(self.object.get("decode"))
        self.keypoint = _dict(sidecar.get("keypoint"))
        self.keypoint_decode = _dict(self.keypoint.get("decode"))
        self.point_names = _texts(self.keypoint.get("point_names"))
        self.primaries = self.with_semantic(*PRIMARY_SEMANTICS)
        self.primary = self.primaries[0] if len(self.primaries) == 1 else None
        self.derived_names: set[str] = set()
        self.declared_precisions = {
            precision
            for entry in self.sizes.values()
            for precision in _dict(_dict(entry.get("onnx")).get("precision_artifacts"))
        }

    # ---- helpers -------------------------------------------------------------------------

    def fail(self, rule: str, message: str) -> None:
        self.failures.append(Failure(rule, message))

    def only(self, mapping: dict[Any, Any], allowed: set[str], where: str, rule: str = _COMPOSITION_5) -> None:
        for key in mapping:
            if key not in allowed:
                self.fail(rule, f"{where}: the spec does not define the key {key!r}")

    def with_semantic(self, *semantics: str) -> list[dict[Any, Any]]:
        return [output for output in self.outputs if _is_one_of(output.get("semantic"), semantics)]

    def run(self) -> None:
        self.nulls(self.s, ())
        self.only(self.s, _TOP_KEYS, "the sidecar")
        if failure := check_schema_version(self.s.get("schema_version")):
            self.failures.append(failure)
        self.identity()
        self.keypoint_folder()
        self.check_sizes()
        self.batching()
        self.check_input()
        self.resize_method()
        self.normalization()
        self.check_outputs()
        self.license()
        if "object_detector" in self.roles or "object" in self.s:
            self.object_outputs()
            self.check_object_decode()
            self.selection()
        if "keypoint_detector" in self.roles or "keypoint" in self.s:
            self.keypoint_schema()
            self.keypoint_outputs()
            self.overlay()

    def nulls(self, node: Any, path: tuple[Any, ...]) -> None:
        """No field has the value null. Only an item of `object.classes` can be null: a gap."""
        if node is None and path[:2] != ("object", "classes"):
            self.fail(NULL_VALUE, f"{'.'.join(map(str, path))} is null; a sidecar omits a field that has no value")
        elif isinstance(node, dict):
            for key, value in node.items():
                self.nulls(value, (*path, key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                self.nulls(value, (*path, index))

    # ---- common.identity -----------------------------------------------------------------

    def identity(self) -> None:
        s, rule = self.s, "V-common.identity-"
        model_id = s.get("model_id")
        if not _is_text(model_id):
            self.fail(rule + "1", "model_id must be a non-empty string")
        elif self.relative_path is not None and PurePosixPath(self.relative_path).name != f"{model_id}.yaml":
            self.fail(rule + "1", f"model_id {model_id!r} does not match the file name of {self.relative_path}")
        role = _texts(s.get("role"))
        if not (role and set(role) <= set(ROLES) and len(set(role)) == len(role)):
            self.fail(rule + "2", f"role must be a non-empty subset of {list(ROLES)}")
        if not _is_text(s.get("display_name")):
            self.fail(rule + "3", "display_name must be a non-empty string")
        if not _is_text(self.input.get("name")):
            self.fail(rule + "3", "the sidecar must have input, with name")
        outputs = s.get("outputs")
        if not (isinstance(outputs, list) and outputs and all(_is_text(_dict(o).get("name")) for o in outputs)):
            self.fail(rule + "3", "outputs must be a non-empty array, and each entry must have name")
        source = s.get("source")
        if not (isinstance(source, dict) and set(source) == {"name", "version"}):
            self.fail(rule + "4", "source must be a mapping with exactly the keys name and version")
        if isinstance(source, dict):
            if not (_is_text(source.get("name")) and _is_text(source.get("version"))):
                self.fail(rule + "5", "source.name and source.version must be non-empty strings; write a version such as \"1.0\" in quotes")
            if isinstance(source.get("name"), str) and not _TOKENS.fullmatch(source["name"]):
                self.fail(rule + "6", f"source.name {source['name']!r} must match ^[a-z0-9]+(-[a-z0-9]+)*$")

    def keypoint_folder(self) -> None:
        """V-common.identity-7 and -8: the folder of a sidecar under `detectors/keypoint_detectors/`."""
        model_id = self.s.get("model_id")
        if self.relative_path is None or not isinstance(model_id, str):
            return
        parts = PurePosixPath(self.relative_path).parts
        if parts[:2] != _KEYPOINT_BRANCH:
            return
        if len(parts) != 5:
            self.fail("V-common.identity-7", f"{self.relative_path} is not in detectors/keypoint_detectors/{{family}}/{{group}}/")
            return
        family, group = parts[2], parts[3]
        stem = f"{family}-{group}"
        variant = model_id[len(stem) + 1:] if model_id.startswith(stem + "-") else None
        if not (_TOKENS.fullmatch(family) and (model_id == stem or (variant and _TOKENS.fullmatch(variant)))):
            self.fail("V-common.identity-7", f"model_id {model_id!r} must be {stem!r} or {stem + '-{variant}'!r}")
        keypoint_set = _KEYPOINT_SET.fullmatch(group)
        if group in BODY_REGIONS:
            return
        if keypoint_set is None:
            self.fail("V-common.identity-8", f"the group folder {group!r} must be one of {list(BODY_REGIONS)} or match ^[a-z]+[1-9][0-9]*$")
        elif self.point_names is not None and int(keypoint_set.group(1)) != len(self.point_names):
            self.fail("V-common.identity-8", f"the group folder {group!r} gives {keypoint_set.group(1)} keypoints, but keypoint.point_names has {len(self.point_names)}")

    # ---- common.sizes_and_artifacts, common.batching, common.batch_conversion ---------------

    def check_sizes(self) -> None:
        rule = "V-common.sizes_and_artifacts-"
        sizes = self.s.get("sizes")
        if not (isinstance(sizes, dict) and sizes):
            self.fail(rule + "1", "sizes must be present, with one size or more")
        for name, entry in _dict(sizes).items():
            where = f"sizes.{name}"
            if not isinstance(entry, dict):
                self.fail(rule + "3", f"{where} must be a mapping")
                continue
            self.only(entry, {"input", "onnx", "score_map"}, where, rule + "3")
            self.score_map(where, entry)
            size_input = _dict(entry.get("input"))
            self.only(size_input, {"shape", "resize"}, f"{where}.input", rule + "3")
            shape = _shape(size_input.get("shape"))
            if not (shape and len(shape) == 4 and shape[0] == -1 and -1 not in shape[1:]):
                self.fail(rule + "2", f"{where}.input.shape must be [-1, channels, height, width], with -1 only as the batch axis")
                shape = None
            if "resize" in size_input:
                size_resize = size_input["resize"]
                if not isinstance(size_resize, dict):
                    self.fail(rule + "3", f"{where}.input.resize must be a mapping")
                    size_resize = {}
                self.only(size_resize, {"target_size"}, f"{where}.input.resize", rule + "3")
                if "target_size" in size_resize:
                    target = size_resize["target_size"]
                    if not (isinstance(target, list) and len(target) == 2 and all(_positive_int(v) for v in target)):
                        self.fail("V-common.input-1", f"{where}.input.resize.target_size must be [height, width]")
                    elif shape and shape[2:4] != target:
                        self.fail(rule + "4", f"{where}: input.shape[2:4] {shape[2:4]} is not target_size {target}")
            self.onnx(where, _dict(entry.get("onnx")))

    def score_map(self, where: str, entry: dict[Any, Any]) -> None:
        """V-post.keypoint.score_map-1 to -6: the score map of one size."""
        rule = "V-post.keypoint.score_map-"
        simcc = self.keypoint_decode.get("method") == "simcc"
        if "score_map" not in entry:
            if simcc:
                self.fail(rule + "1", f"{where}: a size of a simcc model must have score_map")
            return
        if not simcc:
            self.fail(rule + "6", f"{where}.score_map is valid only with keypoint.decode.method: simcc")
        block, at = entry["score_map"], f"{where}.score_map"
        if not isinstance(block, dict):
            self.fail(rule + "2", f"{at} must be a mapping")
            return
        if missing := [key for key in ("method", "a", "b") if key not in block]:
            self.fail(rule + "2", f"{at} must have {missing}")
        self.only(block, {"method", "a", "b", "groups", "fit"}, at, rule + "2")
        if "method" in block and block["method"] != "logistic":
            self.fail(rule + "2", f"{at}.method must be logistic")
        self.score_pair(at, block)
        if "groups" in block:
            self.score_groups(f"{at}.groups", block["groups"])
        if "fit" in block:
            fit = block["fit"]
            if not (isinstance(fit, dict) and set(fit) == {"dataset", "split", "recipe"} and all(_is_text(v) for v in fit.values())):
                self.fail(rule + "5", f"{at}.fit must have exactly dataset, split and recipe, each a non-empty string")

    def score_pair(self, at: str, pair: dict[Any, Any]) -> None:
        """V-post.keypoint.score_map-3: `a` is a finite number > 0, and `b` is a finite number."""
        a, b = pair.get("a"), pair.get("b")
        if "a" in pair and not (_is_number(a) and a > 0):
            self.fail("V-post.keypoint.score_map-3", f"{at}.a must be a finite number > 0")
        if "b" in pair and not _is_number(b):
            self.fail("V-post.keypoint.score_map-3", f"{at}.b must be a finite number")

    def score_groups(self, at: str, groups: Any) -> None:
        """V-post.keypoint.score_map-4, and -3 on each pair: the pairs of the landmark-schema groups."""
        rule = "V-post.keypoint.score_map-4"
        if not (isinstance(groups, dict) and groups):
            self.fail(rule, f"{at} must be a non-empty mapping")
            return
        name = self.keypoint.get("landmark_schema")
        schema = self.landmark_schemas.get(name) if self.landmark_schemas is not None and isinstance(name, str) else None
        known = None if schema is None else {group.name for group in schema.groups}
        for group, pair in groups.items():
            if known is not None and group not in known:
                self.fail(rule, f"{at}.{group} is not a group of the landmark schema {name!r}")
            if not (isinstance(pair, dict) and set(pair) == {"a", "b"}):
                self.fail(rule, f"{at}.{group} must have exactly the keys a and b")
            if isinstance(pair, dict):
                self.score_pair(f"{at}.{group}", pair)

    def onnx(self, where: str, onnx: dict[Any, Any]) -> None:
        rule = "V-common.sizes_and_artifacts-"
        self.only(onnx, {"precision_artifacts", "output_shapes"}, f"{where}.onnx", rule + "3")
        artifacts = onnx.get("precision_artifacts")
        if not (isinstance(artifacts, dict) and artifacts):
            self.fail(rule + "5", f"{where}.onnx.precision_artifacts must list one precision or more")
        for precision, artifact in _dict(artifacts).items():
            at = f"{where}.onnx.precision_artifacts.{precision}"
            if precision not in PRECISIONS:
                self.fail(rule + "6", f"{at}: the precision keys are {list(PRECISIONS)}")
            if not isinstance(artifact, dict):
                self.fail(rule + "7", f"{at} must be a mapping with filename")
                continue
            self.only(artifact, _ARTIFACT_KEYS, at)
            filename = artifact.get("filename")
            parts = PurePosixPath(filename.replace("\\", "/")).parts if _is_text(filename) else ("..",)
            if ".." in parts or len(parts) != 1 or ":" in parts[0]:
                self.fail(rule + "7", f"{at}.filename must be a file name in the folder of the sidecar")
            if "url" in artifact and not (_is_text(artifact["url"]) and _is_hash(artifact.get("url_sha256"))):
                self.fail(rule + "7", f"{at}: url must be a string, with url_sha256 in lowercase hex (64 characters)")
            if not _is_hash(artifact.get("sha256")):
                self.fail(rule + "9", f"{at}.sha256 must be a string of 64 lowercase hexadecimal characters, in quotes")
            elif artifact["sha256"] == PLACEHOLDER_SHA256 and not self.in_examples:
                self.fail(rule + "11", f"{at}.sha256 is the placeholder; it is valid only under specs/model-sidecar/examples/")
        self.output_shapes(where, onnx)

    def output_shapes(self, where: str, onnx: dict[Any, Any]) -> None:
        rule, at = "V-common.sizes_and_artifacts-8", f"{where}.onnx.output_shapes"
        shapes, outputs = onnx.get("output_shapes"), self.s.get("outputs")
        if not isinstance(shapes, list):
            self.fail(rule, f"{at} must be an array with one shape for each output")
            return
        if not isinstance(outputs, list):
            return
        if len(shapes) != len(outputs):
            self.fail(rule, f"{at} has {len(shapes)} entries for {len(outputs)} outputs")
            return
        # A batch that is not valid fails V-common.sizes_and_artifacts-12, not this rule.
        dim0 = -1 if self.batch == "dynamic" else self.batch if _is_int(self.batch) and self.batch in (1, 3) else None
        for index, (entry, output) in enumerate(zip(shapes, outputs, strict=True)):
            shape = _shape(entry)
            if shape is None:
                self.fail(rule, f"{at}[{index}] must be an array of dims; a dim is -1 or a positive int")
                continue
            if dim0 is not None and shape[0] != dim0:
                self.fail(rule, f"{at}[{index}]: dim 0 is {shape[0]}, but batching.batch gives {dim0}")
            family = _shape(_dict(output).get("shape"))
            if family is None:
                continue
            if len(shape) != len(family):
                self.fail(rule, f"{at}[{index}] has {len(shape)} dims, but outputs[{index}].shape has {len(family)}")
            elif any(f != -1 and d not in (f, -1) for f, d in zip(family, shape, strict=True)):
                self.fail(rule, f"{at}[{index}] {shape} does not agree with outputs[{index}].shape {family}")

    def batching(self) -> None:
        batching = self.s.get("batching")
        if not isinstance(batching, dict):
            self.fail("V-common.sizes_and_artifacts-12", "batching.batch must be present")
            return
        self.only(batching, {"batch", "batch_conversion"}, "batching")
        batch = batching.get("batch")
        is_three = _is_int(batch) and batch == 3
        if not (is_three or (_is_int(batch) and batch == 1) or _is_one_of(batch, ("dynamic",))):
            self.fail("V-common.sizes_and_artifacts-12", f"batching.batch {batch!r} must be the int 3, the int 1 or the string dynamic")
        elif is_three and "batch_conversion" not in batching:
            self.fail("V-common.sizes_and_artifacts-12", "batching.batch 3 is valid only with batching.batch_conversion")
        if "batch_conversion" not in batching:
            return
        conversion = batching["batch_conversion"]
        if not (isinstance(conversion, dict) and set(conversion) == {"profile_id"}):
            self.fail("V-common.batch_conversion-1", "batching.batch_conversion must have profile_id and no other key")
        if isinstance(conversion, dict) and "profile_id" in conversion and not _is_one_of(conversion["profile_id"], BATCH_CONVERSION_PROFILES):
            self.fail("V-common.batch_conversion-2", f"profile_id {conversion['profile_id']!r} is not one of {list(BATCH_CONVERSION_PROFILES)}")
        if not is_three:
            self.fail("V-common.batch_conversion-3", "batching.batch_conversion is valid only with batching.batch 3")

    # ---- common.input, pre.resize.*, pre.normalize ---------------------------------------

    def dtype_problem(self, dtype: Any, allowed: tuple[str, ...]) -> str | None:
        if not (isinstance(dtype, dict) and dtype):
            return "dtype must be a map of precision to element type"
        if not set(dtype) <= set(PRECISIONS):
            return f"the keys of dtype must be precision keys {list(PRECISIONS)}"
        if missing := sorted(self.declared_precisions & set(PRECISIONS) - set(dtype)):
            return f"dtype does not cover the precisions {missing} that precision_artifacts declares"
        if not all(_is_one_of(value, allowed) for value in dtype.values()):
            return f"each value of dtype must be one of {list(allowed)}"
        return None

    def check_input(self) -> None:
        if not isinstance(self.s.get("input"), dict):
            return
        rule, inp = "V-common.input-", self.input
        self.only(inp, _INPUT_KEYS, "input")
        if problem := self.dtype_problem(inp.get("dtype"), INPUT_DTYPES):
            self.fail(rule + "2", f"input: {problem}")
        if "color_format" in inp and not _is_one_of(inp["color_format"], ("rgb", "bgr")):
            self.fail(rule + "5", "input.color_format must be rgb or bgr")
        if "resize" not in inp:
            return
        if not isinstance(inp["resize"], dict):
            self.fail(rule + "3", "input.resize must be a mapping with method")
            return
        resize = self.resize
        self.only(resize, _RESIZE_KEYS, "input.resize")
        if not _is_one_of(resize.get("method"), RESIZE_METHODS):
            self.fail(rule + "3", f"input.resize.method must be one of {list(RESIZE_METHODS)}")
        if "interpolation" in resize and not _is_one_of(resize["interpolation"], INTERPOLATIONS):
            self.fail(rule + "3", f"input.resize.interpolation must be one of {list(INTERPOLATIONS)}")
        for where, holder in (("input.resize", resize), ("input.resize.crop_policy", _dict(resize.get("crop_policy")))):
            if "pad_value" in holder and _pad_values(holder["pad_value"]) is None:
                self.fail(rule + "4", f"{where}.pad_value must be a number or an array of 3 numbers")

    def resize_method(self) -> None:
        resize, method = self.resize, self.method
        has_target = {name: "target_size" in _dict(_dict(entry.get("input")).get("resize")) for name, entry in self.sizes.items()}
        without = sorted(str(name) for name, found in has_target.items() if not found)
        present = lambda *keys: [key for key in keys if key in resize]  # noqa: E731

        def target_and_keys(rule: str, *forbidden: str) -> None:
            if without:
                self.fail(rule, f"the sizes {without} must declare input.resize.target_size")
            if found := present(*forbidden):
                self.fail(rule, f"a {method} resize must not declare {found}")

        if method == "letterbox":
            rule = "V-pre.resize.letterbox-1"
            if not _is_one_of(resize.get("pad_position"), ("top_left", "center")):
                self.fail(rule, "a letterbox resize must declare pad_position: top_left or center")
            if not _is_one_of(resize.get("rounding"), ("half_even", "half_up")):
                self.fail(rule, "a letterbox resize must declare rounding: half_even or half_up")
            target_and_keys(rule, "crop_policy")
        elif method == "stretch":
            target_and_keys("V-pre.resize.stretch-1", "pad_value", "pad_position", "rounding", "crop_policy")
        elif method == "fit":
            if "pad_value" not in resize:
                self.fail("V-pre.resize.fit-1", "a fit resize must declare pad_value")
            target_and_keys("V-pre.resize.fit-1", "pad_position", "rounding", "crop_policy")
        elif method == "affine_crop":
            target_and_keys("V-pre.resize.affine_crop-3", "pad_value", "pad_position", "rounding")
        elif method == "none":
            rule = "V-pre.resize.none-1"
            if with_target := sorted(str(name) for name, found in has_target.items() if found):
                self.fail(rule, f"the sizes {with_target} must omit input.resize.target_size")
            if found := present("pad_value", "pad_position", "rounding", "crop_policy", "compute_dtype"):
                self.fail(rule, f"a none resize must not declare {found}")

        policy = _dict(resize.get("crop_policy"))
        if "crop_policy" in resize:
            rule = "V-pre.resize.affine_crop-1"
            self.only(policy, _CROP_POLICY_KEYS, "input.resize.crop_policy")
            if not isinstance(resize["crop_policy"], dict):
                self.fail(rule, "input.resize.crop_policy must be a mapping")
            if "expand_ratio" in policy and not (_is_number(policy["expand_ratio"]) and policy["expand_ratio"] > 0):
                self.fail(rule, "crop_policy.expand_ratio must be a positive float")
            if "maintain_aspect_ratio" in policy and not isinstance(policy["maintain_aspect_ratio"], bool):
                self.fail(rule, "crop_policy.maintain_aspect_ratio must be a boolean")
        if _is_one_of(self.keypoint.get("estimator_type"), TOP_DOWN_TYPES) and method != "affine_crop":
            self.fail("V-pre.resize.affine_crop-2", "a top-down keypoint detector must declare input.resize.method: affine_crop")

        if "compute_dtype" in resize and not _is_one_of(resize["compute_dtype"], COMPUTE_DTYPES):
            self.fail("V-pre.resize.interpolation-1", f"input.resize.compute_dtype must be one of {list(COMPUTE_DTYPES)}")
        if resize.get("compute_dtype", "uint8") == "uint8":
            for where, holder in (("input.resize", resize), ("input.resize.crop_policy", policy)):
                values = _pad_values(holder.get("pad_value")) or []
                if not all(float(value).is_integer() and 0 <= value <= 255 for value in values):
                    self.fail("V-pre.resize.interpolation-2", f"{where}.pad_value {holder['pad_value']!r}: with an 8-bit resize, each pad value must be an integer from 0 to 255")

    def normalization(self) -> None:
        if not isinstance(self.s.get("input"), dict):
            return
        rule, inp = "V-pre.normalize-", self.input
        normalization = inp.get("normalization")
        if "normalization" not in inp:
            self.fail(rule + "1", "input.normalization must be present; it has no default")
        elif isinstance(normalization, dict):
            if normalization.get("mode") != "custom" or set(normalization) - {"mode", "scale", "mean", "std"}:
                self.fail(rule + "1", "a custom normalization must have mode: custom and only the keys mode, scale, mean and std")
            for key in ("mean", "std"):
                value = normalization.get(key)
                if key in normalization and not (isinstance(value, list) and _pad_values(value) is not None):
                    self.fail(rule + "1", f"input.normalization.{key} must have 3 numbers")
            if "scale" in normalization and not (_is_number(normalization["scale"]) and normalization["scale"] > 0):
                self.fail(rule + "1", "input.normalization.scale must be positive")
        elif not _is_one_of(normalization, NORMALIZATION_MODES):
            self.fail(rule + "1", f"input.normalization must be one of {list(NORMALIZATION_MODES)} or a custom object")
        if "color_format" not in inp:
            self.fail(rule + "1", "input.color_format must be present; it has no default")

        overrides = inp.get("normalization_by_precision")
        if "normalization_by_precision" in inp and not (
            isinstance(overrides, dict)
            and set(overrides) <= set(PRECISIONS)
            and all(_is_one_of(value, NORMALIZATION_MODES) for value in overrides.values())
        ):
            self.fail(rule + "2", f"normalization_by_precision must map precision keys to one of {list(NORMALIZATION_MODES)}")
        for precision, dtype in _dict(inp.get("dtype")).items():
            if dtype != "uint8":
                continue
            if _dict(overrides).get(precision, normalization) != "none":
                self.fail(rule + "3", f"input.dtype.{precision} is uint8, so the normalization of {precision} must be none")
            elif self.resize.get("compute_dtype", "uint8") != "uint8":
                self.fail(rule + "3", f"input.dtype.{precision} is uint8, so input.resize.compute_dtype must be absent or uint8")

    # ---- common.outputs ------------------------------------------------------------------

    def check_outputs(self) -> None:
        rule = "V-common.outputs-"
        names = [output.get("name") for output in self.outputs if _is_text(output.get("name"))]
        if repeated := sorted({name for name in names if names.count(name) > 1}):
            self.fail(rule + "1", f"the output names {repeated} are not unique")
        for index, output in enumerate(self.outputs):
            where = f"outputs[{index}]"
            self.only(output, _OUTPUT_KEYS, where)
            if problem := self.dtype_problem(output.get("dtype"), OUTPUT_DTYPES):
                self.fail(rule + "2", f"{where}: {problem}")
            semantic = output.get("semantic")
            if not _is_one_of(semantic, DETECTION_SEMANTICS + KEYPOINT_SEMANTICS):
                self.fail(rule + "3", f"{where}.semantic must be one of {list(DETECTION_SEMANTICS + KEYPOINT_SEMANTICS)}")
            elif semantic in DETECTION_SEMANTICS and "object_detector" not in self.roles:
                self.fail(rule + "3", f"{where}.semantic {semantic} needs the role object_detector")
            elif semantic in KEYPOINT_SEMANTICS and "keypoint_detector" not in self.roles:
                self.fail(rule + "3", f"{where}.semantic {semantic} needs the role keypoint_detector")

    # ---- common.license ------------------------------------------------------------------

    def license(self) -> None:
        rule, block = "V-common.license-", self.s.get("license")
        if not isinstance(block, dict):
            self.fail(rule + "1", "the sidecar must have the license mapping")
            return
        data = block.get("training_data")
        unknown = _is_one_of(data, ("unknown",))
        allowed = {"model", "training_data"} | ({"training_data_unknown_reason"} if unknown else set())
        if not {"model", "training_data"} <= set(block) or set(block) - allowed:
            self.fail(rule + "1", "license must have model and training_data, and training_data_unknown_reason only when training_data is unknown")
        if "model" in block:
            self.license_object(block["model"], "license.model")
            if _dict(block["model"]).get("id") == "unknown":
                self.fail(rule + "5", "license.model.id must not be unknown")
        if "training_data" not in block:
            return
        if unknown:
            if not _is_text(block.get("training_data_unknown_reason")):
                self.fail(rule + "6", "training_data: unknown needs training_data_unknown_reason")
        elif not (isinstance(data, list) and data):
            self.fail(rule + "6", "license.training_data must be unknown or a non-empty array")
        for index, entry in enumerate(_list(data)):
            where = f"license.training_data[{index}]"
            good = (
                isinstance(entry, dict)
                and _is_text(entry.get("name"))
                and _is_one_of(entry.get("use"), ("pretraining", "training"))
                and "license" in entry
                and not set(entry) - {"name", "url", "use", "license"}
            )
            if not good:
                self.fail(rule + "7", f"{where} must have name, use (pretraining or training) and license; its only other key can be url")
            if "license" in _dict(entry):
                self.license_object(entry["license"], f"{where}.license")

    def license_object(self, value: Any, where: str) -> None:
        rule = "V-common.license-"
        if not (isinstance(value, dict) and _is_text(value.get("id")) and not set(value) - {"id", "url", "unknown_reason"}):
            self.fail(rule + "2", f"{where} must have a non-empty string id, and only the keys id, url and unknown_reason")
        if not (isinstance(value, dict) and _is_text(value.get("id"))):
            return
        if value["id"] == "unknown":
            if not _is_text(value.get("unknown_reason")):
                self.fail(rule + "4", f"{where}: id unknown needs unknown_reason")
            return
        if "unknown_reason" in value:
            self.fail(rule + "4", f"{where}: unknown_reason is valid only with id: unknown")
        if not is_spdx_expression(value["id"]):
            self.fail(rule + "3", f"{where}.id {value['id']!r} is not a valid SPDX license expression")
        elif has_license_ref(value["id"]) and not _is_text(value.get("url")):
            self.fail(rule + "3", f"{where}: a LicenseRef- id needs url")

    # ---- post.object.* -------------------------------------------------------------------

    def class_axis(self, logits: dict[Any, Any]) -> tuple[list[int], int] | None:
        """Return the shape of a `class_logits` output and its class axis, as a non-negative index."""
        shape, axis = _shape(logits.get("shape")), logits.get("class_axis", -1)
        if shape is None or not _is_int(axis) or not -len(shape) <= axis < len(shape) or axis % len(shape) == 0:
            return None
        return shape, axis % len(shape)

    def object_outputs(self) -> None:
        rule = "V-post.object.outputs-"
        scores, logits = self.with_semantic("scores"), self.with_semantic("class_logits")
        if not isinstance(self.object.get("decode"), dict):
            self.fail(rule + "1", "an object detector must declare object.decode")
        if len(self.primaries) != 1 or len(scores) > 1 or len(logits) > 1:
            self.fail(rule + "1", "an object detector must declare exactly one primary output (packed_detections or boxes), and at most one scores and one class_logits output")
        self.only(self.object, {"classes", "decode"}, "object")
        self.only(self.object_decode, _OBJECT_DECODE_KEYS, "object.decode")
        primary_shape = _shape(self.primary.get("shape")) if self.primary else None
        for output in self.outputs:
            name, semantic, shape = output.get("name"), output.get("semantic"), _shape(output.get("shape"))
            if semantic == "packed_detections":
                fields, packed = _texts(output.get("fields")), _dict(output.get("packed_keypoints"))
                if not fields:
                    self.fail(rule + "2", f"the packed_detections output {name!r} must declare fields")
                elif "offset" in packed:
                    if len(fields) != packed["offset"]:
                        self.fail(rule + "2", f"output {name!r}: len(fields) must equal packed_keypoints.offset")
                elif shape and shape[-1] != -1 and len(fields) != shape[-1]:
                    self.fail(rule + "2", f"output {name!r}: len(fields) {len(fields)} must equal shape[-1] {shape[-1]}")
            elif "fields" in output:
                self.fail(rule + "2", f"output {name!r}: fields is valid only on a packed_detections output")
            if semantic == "boxes" and shape and shape[-1] != 4:
                self.fail(rule + "3", f"the last dimension of the boxes output {name!r} must be 4")
            if semantic == "scores" and shape and primary_shape and shape != primary_shape[:-1]:
                self.fail(rule + "3", f"the shape of the scores output {name!r} must be the primary shape without its last dimension")
            if semantic == "class_logits":
                found = self.class_axis(output)
                if found is None:
                    self.fail(rule + "3", f"the class_logits output {name!r} needs a shape, and class_axis must be a valid axis that is not the batch axis")
                    continue
                shape, axis = found
                if shape[axis] == -1:
                    self.fail(rule + "3", f"the class dimension of {name!r} must be concrete")
                if self.primary and self.primary.get("semantic") == "boxes" and primary_shape and shape[:axis] + shape[axis + 1:] != primary_shape[:-1]:
                    self.fail(rule + "3", f"the non-class axes of {name!r} must equal the outer axes of the boxes output")
            if semantic in DETECTION_SEMANTICS and not all(_is_one_of(v, FLOAT_DTYPES) for v in _dict(output.get("dtype")).values()):
                self.fail(rule + "4", f"the dtype of the {semantic} output {name!r} must be a float type")

    def check_object_decode(self) -> None:
        rule, decode, primary = "V-post.object.decode-", self.object_decode, self.primary
        by_name = {output["name"]: output for output in self.outputs if _is_text(output.get("name"))}
        for key, semantics in (
            ("boxes_output", PRIMARY_SEMANTICS),
            ("scores_output", ("scores",)),
            ("class_logits_output", ("class_logits",)),
        ):
            if key in decode and not (_is_text(decode[key]) and _is_one_of(_dict(by_name.get(decode[key])).get("semantic"), semantics)):
                self.fail(rule + "1", f"object.decode.{key} {decode[key]!r} must name an output with the semantic {' or '.join(semantics)}")
        fields = _texts(primary.get("fields")) or [] if primary and primary.get("semantic") == "packed_detections" else []
        for key in ("score_field", "class_field"):
            if key in decode and not (_is_text(decode[key]) and decode[key] in fields):
                self.fail(rule + "2", f"object.decode.{key} {decode[key]!r} must be in the fields of a packed_detections primary output")
        if "score_field" in decode and "scores_output" in decode:
            self.fail(rule + "2", "score_field and scores_output must not both be present")
        if "class_field" in decode and "class_logits_output" in decode:
            self.fail(rule + "2", "class_field and class_logits_output must not both be present")
        selection = decode.get("selection")
        if primary and primary.get("semantic") == "packed_detections":
            if selection != "top_k" and "score_field" not in decode and "scores_output" not in decode:
                self.fail(rule + "3", "a packed_detections primary output needs score_field or scores_output")
        elif primary and "scores_output" not in decode and "class_logits_output" not in decode:
            self.fail(rule + "3", "a boxes primary output needs scores_output or class_logits_output")
        if not _is_one_of(selection, SELECTIONS):
            self.fail(rule + "4", f"object.decode.selection must be one of {list(SELECTIONS)}")
        for key, allowed in (("box_format", BOX_FORMATS), ("box_space", COORDINATE_SPACES), ("score_activation", SCORE_ACTIVATIONS)):
            if key in decode and not _is_one_of(decode[key], allowed):
                self.fail(rule + "5", f"object.decode.{key} must be one of {list(allowed)}")
        if "clamp_boxes" in decode and not isinstance(decode["clamp_boxes"], bool):
            self.fail(rule + "5", "object.decode.clamp_boxes must be a boolean")
        if "min_score" in decode and not _in_unit_range(decode["min_score"]):
            self.fail(rule + "8", "object.decode.min_score must be in [0, 1]")
        if "min_box_size" in decode and not (_is_number(decode["min_box_size"]) and decode["min_box_size"] >= 0):
            self.fail(rule + "8", "object.decode.min_box_size must be a non-negative number")

        classes = self.object.get("classes")
        names = [item for item in _list(classes) if isinstance(item, str)]
        good_items = isinstance(classes, list) and all(item is None or _is_text(item) for item in classes)
        if not (good_items and names and len(set(names)) == len(names)):
            self.fail(rule + "10", "object.classes must be a non-empty list of unique, non-empty names; null marks a gap, and one item or more must be a name")
        elif (count := self.class_count()) is not None and len(classes) != count:
            self.fail(rule + "10", f"object.classes has {len(classes)} items, but the class dimension of class_logits is {count}")
        if "class_field" not in decode and "class_logits_output" not in decode and isinstance(classes, list) and not (len(classes) == 1 and names):
            self.fail(rule + "9", "a sidecar with no class source must have exactly one name in object.classes")
        if "keep_classes" in decode:
            keep = _texts(decode["keep_classes"])
            if not (keep and len(set(keep)) == len(keep) and set(keep) <= set(names)):
                self.fail(rule + "11", "object.decode.keep_classes must be a non-empty list of unique names of object.classes")

    def class_count(self) -> int | None:
        logits = self.with_semantic("class_logits")
        found = self.class_axis(logits[0]) if len(logits) == 1 else None
        return None if found is None or found[0][found[1]] == -1 else found[0][found[1]]

    def selection(self) -> None:
        decode, selection, primary = self.object_decode, self.object_decode.get("selection"), self.primary
        present = lambda *keys: [key for key in keys if key in decode]  # noqa: E731
        if selection == "none":
            rule = "V-post.object.selection.none-1"
            if found := present("top_k", "nms", "class_logits_output"):
                self.fail(rule, f"selection: none must not have {found}")
            if "max_detections" in decode:
                rows = (_shape(_dict(primary).get("shape")) or [-1, -1])[1:2]
                if not _positive_int(decode["max_detections"]):
                    self.fail(rule, "object.decode.max_detections must be a positive integer")
                elif rows and rows[0] != -1 and rows[0] != decode["max_detections"]:
                    self.fail(rule, f"max_detections {decode['max_detections']} must equal the row dimension {rows[0]} of the primary output")
        elif selection == "top_k":
            rule = "V-post.object.selection.top_k-1"
            if not (primary and primary.get("semantic") == "boxes"):
                self.fail(rule, "selection: top_k needs a boxes primary output")
            if "class_logits_output" not in decode or not _positive_int(decode.get("top_k")):
                self.fail(rule, "selection: top_k needs class_logits_output and a positive integer top_k")
            if found := present("nms", "max_detections", "scores_output", "score_field"):
                self.fail(rule, f"selection: top_k must not have {found}")
        elif selection == "nms":
            rule, nms = "V-post.object.selection.nms-1", _dict(decode.get("nms"))
            self.only(nms, _NMS_KEYS, "object.decode.nms")
            if not (_in_unit_range(nms.get("iou_threshold")) and _in_unit_range(nms.get("score_threshold"))):
                self.fail(rule, "selection: nms needs nms with iou_threshold and score_threshold, each in [0, 1]")
            if found := present("class_logits_output", "top_k", "max_detections"):
                self.fail(rule, f"selection: nms must not have {found}")
            if "class_agnostic" in nms and not isinstance(nms["class_agnostic"], bool):
                self.fail(rule, "nms.class_agnostic must be a boolean")
            if "post_nms_top_k" in nms and not _positive_int(nms["post_nms_top_k"]):
                self.fail(rule, "nms.post_nms_top_k must be a positive integer")

    # ---- post.keypoint.* -----------------------------------------------------------------

    def keypoint_schema(self) -> None:
        rule, keypoint, decode = "V-post.keypoint.schema-", self.keypoint, self.keypoint_decode
        required = ("estimator_type", "geometry", "landmark_schema", "decode", "point_names", "skeletons")
        if missing := [key for key in required if key not in keypoint]:
            self.fail(rule + "1", f"a keypoint detector must declare keypoint, with {missing}")
        self.only(keypoint, _KEYPOINT_KEYS, "keypoint")
        self.only(decode, _KEYPOINT_DECODE_KEYS, "keypoint.decode")
        if "estimator_type" in keypoint and not _is_one_of(keypoint["estimator_type"], ESTIMATOR_TYPES):
            self.fail(rule + "3", f"keypoint.estimator_type must be one of {list(ESTIMATOR_TYPES)}")
        if "decode" in keypoint and not _is_one_of(decode.get("method"), DECODE_METHODS):
            self.fail(rule + "3", f"keypoint.decode.method must be one of {list(DECODE_METHODS)}")

        points = self.point_names
        if "point_names" in keypoint:
            if not points or len(set(points)) != len(points):
                self.fail(rule + "4", "keypoint.point_names must be a non-empty list of unique names")
            if bad := [name for name in points or [] if has_bad_point_character(name)]:
                self.fail(rule + "11", f"the point names {bad} contain `/` or a whitespace character")
        self.derived_names = set(self.derived_points())
        known = set(points or []) | self.derived_names

        skeletons = keypoint.get("skeletons")
        if "skeletons" in keypoint:
            entries = [entry for entry in _list(skeletons) if isinstance(entry, dict)]
            names = [entry.get("name") for entry in entries]
            well_formed = isinstance(skeletons, list) and len(entries) == len(skeletons) and all(
                set(entry) == {"name", "edges"} and _is_text(entry["name"]) and isinstance(entry["edges"], list)
                for entry in entries
            )
            if not well_formed or len(set(names)) != len(names):
                self.fail(rule + "5", "keypoint.skeletons must be a list of {name, edges} entries with unique names")
            for entry in entries:
                edges = [_edge(edge) for edge in _list(entry.get("edges"))]
                if any(edge is None or not edge <= known for edge in edges):
                    self.fail(rule + "5", f"each edge of the skeleton {entry.get('name')!r} must join two names of point_names or derived_points")

        geometry = keypoint.get("geometry")
        if "geometry" in keypoint and not _is_one_of(geometry, ("2d", "3d")):
            self.fail(rule + "9", "keypoint.geometry must be 2d or 3d")
        if geometry == "3d" and not _is_one_of(decode.get("depth_unit"), DEPTH_UNITS):
            self.fail(rule + "9", f"keypoint.geometry 3d needs keypoint.decode.depth_unit: one of {list(DEPTH_UNITS)}")
        if geometry != "3d" and "depth_unit" in decode:
            self.fail(rule + "9", "keypoint.decode.depth_unit is valid only with keypoint.geometry: 3d")

        if self.landmark_schemas is not None and "landmark_schema" in keypoint:
            name = keypoint["landmark_schema"]
            schema = self.landmark_schemas.get(name) if isinstance(name, str) else None
            if schema is None:
                self.fail(rule + "10", f"keypoint.landmark_schema {name!r} is not the name of a schema of the registry")
            elif list(schema.point_names) != points:
                self.fail(rule + "10", f"keypoint.point_names must equal the point names of the schema {name!r}, in the same order")

        if "coordinate_space" in decode and not (decode.get("method") == "coordinate" and _is_one_of(decode["coordinate_space"], COORDINATE_SPACES)):
            self.fail("V-post.keypoint.decode.coordinate-1", f"keypoint.decode.coordinate_space is valid only with method: coordinate, and must be one of {list(COORDINATE_SPACES)}")

    def derived_points(self) -> dict[str, Any]:
        """Check V-post.keypoint.schema-6 and return the derived points."""
        rule, derived = "V-post.keypoint.schema-6", self.keypoint.get("derived_points")
        if "derived_points" not in self.keypoint:
            return {}
        if not isinstance(derived, dict):
            self.fail(rule, "keypoint.derived_points must be a map of derived point name to derivation")
            return {}
        try:
            expanded = expand_derived_points(derived)
        except ValueError as exc:
            self.fail(rule, f"keypoint.derived_points: {exc}")
            return {}
        points = set(self.point_names or [])
        for name, derivation in expanded.items():
            sources = source_names(derivation)
            if not _is_text(name) or name in points:
                self.fail(rule, f"the derived point name {name!r} must be a string that is not in keypoint.point_names")
            if sources is None:
                self.fail(rule, f"the derivation of {name!r} must be a name, a list of names or a name-to-number map that sums to 1")
            elif unknown := sorted(set(sources) - points):
                self.fail(rule, f"the derivation of {name!r} names {unknown}, which are not in keypoint.point_names")
        return expanded

    def keypoint_outputs(self) -> None:
        keypoint, decode = self.keypoint, self.keypoint_decode
        count = lambda semantic: len(self.with_semantic(semantic))  # noqa: E731
        packed = [output for output in self.outputs if "packed_keypoints" in output]
        method, bottom_up = decode.get("method"), keypoint.get("estimator_type") == "bottom_up"
        rule = "V-post.keypoint.schema-7"
        if method == "simcc":
            if count("simcc_x") != 1 or count("simcc_y") != 1:
                self.fail(rule, "a simcc decoder must declare exactly one simcc_x output and exactly one simcc_y output")
            if keypoint.get("geometry") != "2d":
                self.fail(rule, "a simcc decoder must have keypoint.geometry: 2d")
        elif method == "coordinate" and bottom_up:
            if len(self.primaries) != 1 or count("instance_keypoints") + len(packed) != 1:
                self.fail(rule, "a bottom-up coordinate decoder must declare one primary detection output, and either one instance_keypoints output or packed_keypoints")
        elif method == "coordinate" and count("keypoint_coordinates") != 1:
            self.fail(rule, "a single-person coordinate decoder must declare exactly one keypoint_coordinates output")

        points = self.point_names or []
        primary_shape = _shape(self.primary.get("shape")) if self.primary else None
        for output in self.outputs:
            name, shape = output.get("name"), _shape(output.get("shape"))
            if "keypoint_count" in output and output["keypoint_count"] != len(points):
                self.fail("V-post.keypoint.schema-8", f"output {name!r}: keypoint_count must equal len(keypoint.point_names) {len(points)}")
            if output.get("semantic") == "instance_keypoints":
                rule = "V-post.keypoint.bottom_up-1"
                if not (_is_int(output.get("keypoint_axis")) and output["keypoint_axis"] == 2):
                    self.fail(rule, f"the instance_keypoints output {name!r} must declare keypoint_axis: 2")
                if shape and primary_shape and (len(shape) < 2 or len(primary_shape) < 2 or shape[1] != primary_shape[1]):
                    self.fail(rule, f"the instance axis of {name!r} must equal the row axis of the primary detection output")
        for output in packed:
            self.packed_keypoints(output, points)

    def packed_keypoints(self, output: dict[Any, Any], points: list[str]) -> None:
        packed, name = output["packed_keypoints"], output.get("name")
        fail = lambda message: self.fail("V-post.keypoint.bottom_up-2", f"output {name!r}: {message}")  # noqa: E731
        if output.get("semantic") != "packed_detections":
            fail("packed_keypoints is valid only on a packed_detections output")
        if set(self.roles) != set(ROLES) or self.keypoint.get("estimator_type") != "bottom_up" or self.keypoint_decode.get("method") != "coordinate":
            fail("packed keypoints need both roles, estimator_type: bottom_up and keypoint.decode.method: coordinate")
        if "coordinate_space" in self.keypoint_decode:
            fail("keypoint.decode.coordinate_space must not be present; packed keypoints use object.decode.box_space")
        if not (isinstance(packed, dict) and set(packed) == {"offset", "components"}):
            fail("packed_keypoints must have exactly offset and components")
            return
        offset, components = packed["offset"], _texts(packed["components"])
        fields, shape = _texts(output.get("fields")) or [], _shape(output.get("shape"))
        if not (_is_int(offset) and offset == len(fields)):
            fail("packed_keypoints.offset must equal len(fields)")
        good = components and set(components) <= set(PACKED_COMPONENTS) and len(set(components)) == len(components)
        if not (good and {"x", "y"} <= set(components)):
            fail(f"packed_keypoints.components must be a list of unique values from {list(PACKED_COMPONENTS)}, with x and y")
            return
        if ("z" in components) != (self.keypoint.get("geometry") == "3d"):
            fail("packed_keypoints.components must contain z if and only if keypoint.geometry is 3d")
        if _is_int(offset) and shape and shape[-1] != -1 and offset + len(points) * len(components) != shape[-1]:
            fail("offset + len(point_names) * len(components) must equal shape[-1]")

    def overlay(self) -> None:
        rule, keypoint = "V-post.keypoint.overlay-", self.keypoint
        if "overlay" not in keypoint:
            return
        overlay = _dict(keypoint["overlay"])
        if not isinstance(keypoint["overlay"], dict):
            self.fail(rule + "2", "keypoint.overlay must be a mapping")
        self.only(overlay, _OVERLAY_KEYS, "keypoint.overlay")
        named = {
            entry["name"]: {_edge(edge) for edge in _list(entry.get("edges"))}
            for entry in _list(keypoint.get("skeletons"))
            if isinstance(entry, dict) and _is_text(entry.get("name"))
        }
        known = set(self.point_names or []) | self.derived_names
        selected: set[frozenset[str] | None] = next(iter(named.values()), set())
        if "skeleton" in overlay:
            skeleton = overlay["skeleton"]
            inline = {_edge(edge) for edge in skeleton} if isinstance(skeleton, list) else None
            if isinstance(skeleton, str) and skeleton in named:
                selected = named[skeleton]
            elif inline is not None and all(edge is not None and edge <= known for edge in inline):
                selected = inline
            else:
                self.fail(rule + "1", "keypoint.overlay.skeleton must name an entry of keypoint.skeletons, or be an edge list of declared points")
        if "keypoint_color" in overlay and not _is_color(overlay["keypoint_color"]):
            self.fail(rule + "5", "keypoint.overlay.keypoint_color must be a length-3 array")
        if "parts" not in overlay:
            return
        parts = overlay["parts"]
        if not isinstance(parts, dict):
            self.fail(rule + "2", "keypoint.overlay.parts must be a map of part name to part")
            return
        defaults = 0
        for name, part in parts.items():
            where = f"keypoint.overlay.parts.{name}"
            if not isinstance(part, dict):
                self.fail(rule + "2", f"{where} must be a mapping with edge_color")
                continue
            self.only(part, _OVERLAY_PART_KEYS, where)
            defaults += "edges" not in part and "prefix" not in part
            if "edge_color" not in part or ("edges" in part and "prefix" in part) or ("prefix" in part and not _is_text(part["prefix"])):
                self.fail(rule + "2", f"{where} must declare edge_color, and use edges or prefix, but not both")
            if "edge_thickness" in part and not _positive_int(part["edge_thickness"]):
                self.fail(rule + "3", f"{where}.edge_thickness must be a positive integer")
            if "edges" in part and not (isinstance(part["edges"], list) and all(_edge(e) is not None and _edge(e) in selected for e in part["edges"])):
                self.fail(rule + "4", f"each edge of {where}.edges must be an edge of the selected skeleton")
            for key in ("edge_color", "keypoint_color"):
                if key in part and not _is_color(part[key]):
                    self.fail(rule + "5", f"{where}.{key} must be a length-3 array")
        if defaults > 1:
            self.fail(rule + "2", "keypoint.overlay.parts can have at most one part with neither edges nor prefix")


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX64.fullmatch(value))


def _is_color(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(_is_number(item) for item in value)
