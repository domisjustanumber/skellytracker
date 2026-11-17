"""The entry point of the spec loader: read, resolve and validate one sidecar file.

    resolve_sidecar_composition(path, sidecar_root)   # bytes, $ref and hashes -> one tree
      -> check_schema_version()                       # a version that this release implements
      -> check_sidecar()                              # the V- rules of the spec
      -> SidecarModel.model_validate()                # the typed model
"""
from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from skellytracker.core.model_spec.errors import (
    Failure,
    SidecarParseError,
    SidecarSchemaVersionError,
    SidecarValidationError,
)
from skellytracker.core.model_spec.landmark_schemas import load_landmark_schema_registry
from skellytracker.core.model_spec.model import SidecarModel
from skellytracker.core.model_spec.resolution import lexical_path, resolve_sidecar_composition
from skellytracker.core.model_spec.rules import check_sidecar
from skellytracker.core.model_spec.versioning import check_schema_version

FIELD_TYPE = "field-type"
"""The rule name of a field with a wrong type. The Fields tables give the types, with no rule ID."""

_EXAMPLES_FOLDER = ("specs", "model-sidecar", "examples")


def is_in_examples(path: Path) -> bool:
    """Return True when `path` is under a folder `specs/model-sidecar/examples/`."""
    parts, size = lexical_path(path).parts, len(_EXAMPLES_FOLDER)
    return any(parts[i : i + size] == _EXAMPLES_FOLDER for i in range(len(parts) - size + 1))


def load_sidecar(path: Path | str, sidecar_root: Path | str, user_root: Path | str | None = None) -> SidecarModel:
    """Load the sidecar at `path` and return its typed model.

    Implements: format.file_layout
    Implements: format.versioning
    Implements: common.identity

    `sidecar_root` is the sidecar root that holds the file. Each `$ref` target must stay inside it.
    `user_root` is the user root of the catalog. The landmark schema registry reads the package root
    and this root.

    Raise `SidecarParseError` or `SidecarRefError` when a file of the tree is not valid,
    `SidecarSchemaVersionError` when this release does not implement the `schema_version`, and
    `SidecarValidationError` when the sidecar fails a rule of the spec. `rules` of each error holds
    the rule IDs. This function does not read an ONNX file.
    """
    path, root = lexical_path(path), lexical_path(sidecar_root)
    resolved = resolve_sidecar_composition(path, root)
    if not isinstance(resolved, dict):
        raise SidecarParseError("the top level of a sidecar must be a mapping", path)
    if failure := check_schema_version(resolved.get("schema_version")):
        raise SidecarSchemaVersionError(str(failure), path, (failure.rule,))
    registry = load_landmark_schema_registry(None if user_root is None else Path(user_root))
    failures = check_sidecar(
        resolved,
        relative_path=path.relative_to(root).as_posix(),
        landmark_schemas=registry,
        in_examples=is_in_examples(path),
    )
    if failures:
        raise SidecarValidationError(failures, file_path=path)
    try:
        model = SidecarModel.model_validate(resolved)
    except ValidationError as exc:
        failures = [
            Failure(FIELD_TYPE, f"{'.'.join(map(str, error['loc']))}: {error['msg']}") for error in exc.errors()
        ]
        raise SidecarValidationError(failures, file_path=path) from exc
    if model.keypoint is not None:
        # V-post.keypoint.schema-10 passed, so the schema exists and has the point names in order.
        schema = registry[model.keypoint.landmark_schema]
        model._point_groups = tuple(group.name for group in schema.groups for _ in group.points)
    return model
