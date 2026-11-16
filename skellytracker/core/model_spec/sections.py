"""The sections of the sidecar spec, and the capability check of a resolved sidecar.

`SECTIONS` holds the ID, the kind and the selectors of each section file of the spec, in the order
of the section map. A doc test compares it with the front matter of the section files.
`IMPLEMENTED_SECTIONS` holds the sections that the package runs. The spec loader does the full work
of a `format`, `common` or `schema` section. A `preprocessor` or `postprocessor` section goes in
`IMPLEMENTED_SECTIONS` in the commit that adds its processing module.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, NamedTuple

from skellytracker.core.model_spec.sidecar_normalize import applies, normalize


class Section(NamedTuple):
    id: str
    kind: str
    selectors: tuple[str, ...]


SECTIONS: tuple[Section, ...] = (
    Section("format.file_layout", "format", ()),
    Section("format.composition", "format", ()),
    Section("format.versioning", "format", ()),
    Section("common.identity", "common", ()),
    Section("common.sizes_and_artifacts", "common", ()),
    Section("common.batching", "common", ()),
    Section("common.batch_conversion", "common", ("batching.batch_conversion",)),
    Section("common.input", "common", ()),
    Section("common.outputs", "common", ()),
    Section("common.license", "common", ()),
    Section("pre.resize.letterbox", "preprocessor", ("input.resize.method=letterbox",)),
    Section("pre.resize.stretch", "preprocessor", ("input.resize.method=stretch",)),
    Section("pre.resize.fit", "preprocessor", ("input.resize.method=fit",)),
    Section("pre.resize.none", "preprocessor", ("input.resize.method=none",)),
    Section("pre.resize.affine_crop", "preprocessor", ("input.resize.method=affine_crop",)),
    Section("pre.resize.interpolation", "preprocessor", ("input.resize.method=letterbox", "input.resize.method=stretch", "input.resize.method=fit", "input.resize.method=affine_crop")),
    Section("pre.normalize", "preprocessor", ("input.normalization=none", "input.normalization=unit_float", "input.normalization=imagenet", "input.normalization.mode=custom")),
    Section("post.object.outputs", "postprocessor", ("outputs[].semantic=packed_detections", "outputs[].semantic=boxes", "outputs[].semantic=scores", "outputs[].semantic=class_logits")),
    Section("post.object.decode", "postprocessor", ("role=object_detector",)),
    Section("post.object.selection.none", "postprocessor", ("object.decode.selection=none",)),
    Section("post.object.selection.top_k", "postprocessor", ("object.decode.selection=top_k",)),
    Section("post.object.selection.nms", "postprocessor", ("object.decode.selection=nms",)),
    Section("post.keypoint.schema", "schema", ("role=keypoint_detector",)),
    Section("post.keypoint.landmark_schema", "schema", ("role=keypoint_detector",)),
    Section("post.keypoint.canonical_mapping", "schema", ("role=keypoint_detector",)),
    Section("post.keypoint.decode.simcc", "postprocessor", ("keypoint.decode.method=simcc", "outputs[].semantic=simcc_x", "outputs[].semantic=simcc_y")),
    Section("post.keypoint.decode.coordinate", "postprocessor", ("keypoint.decode.method=coordinate", "outputs[].semantic=keypoint_coordinates")),
    Section("post.keypoint.bottom_up", "postprocessor", ("keypoint.estimator_type=bottom_up", "outputs[].semantic=instance_keypoints", "outputs[].packed_keypoints")),
    Section("post.keypoint.overlay", "schema", ("keypoint.overlay",)),
    Section("post.unprojection", "postprocessor", ("role=object_detector", "role=keypoint_detector")),
)

IMPLEMENTED_SECTIONS: frozenset[str] = frozenset(
    section.id for section in SECTIONS if section.kind in {"format", "common", "schema"}
)


def applicable_sections(resolved: Mapping[str, Any]) -> tuple[str, ...]:
    """Return the IDs of the sections that apply to a resolved sidecar, in the order of `SECTIONS`."""
    normalized = normalize(resolved)
    return tuple(section.id for section in SECTIONS if applies(section.kind, section.selectors, normalized))


def unimplemented_sections(resolved: Mapping[str, Any]) -> tuple[str, ...]:
    """Return the IDs of the sections that a resolved sidecar uses and the package does not run.

    Implements: format.versioning

    This is the capability check of a sidecar. An empty result means that the package runs each
    section that the sidecar uses.
    """
    return tuple(section for section in applicable_sections(resolved) if section not in IMPLEMENTED_SECTIONS)
