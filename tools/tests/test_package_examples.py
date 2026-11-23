"""The spec's reference examples resolve and pass the rules of the spec with the package loader.

The spec loader `skellytracker/core/model_spec/` resolves and validates each example:
`load_sidecar` checks each V- rule of the spec, except the bytes of the ONNX files. The other
checks of this file read the resolved example. The last check scans the files of the package for
the placeholder hash.

This test stays in skellytracker: it imports the package. The checks of the examples that need no
package are in `tools/tests/test_examples.py`, which moves to the specs repository with the spec.
This file uses the helpers of that file. That file must never import this file.
"""

import functools
import re
from pathlib import Path
from typing import Any

import pytest
import sidecar_refs
from test_examples import (
    EXAMPLES_ROOT,
    REPO_ROOT,
    example_key,
    example_paths,
    placeholder_holders,
    placeholder_scan_paths,
    unknown_keys,
)

from skellytracker.core.model_spec import load_sidecar, resolve_sidecar_composition


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_resolves(path: Path) -> None:
    resolved = resolve_sidecar_composition(path, EXAMPLES_ROOT)
    assert resolved["model_id"] == path.stem
    assert resolved["schema_version"] == "2.0.0"


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_passes_the_rules_of_the_spec(path: Path) -> None:
    """The spec loader validates the example: each V- rule, except the bytes of the ONNX files.

    The landmark schema registry is the package registry (V-post.keypoint.schema-10).
    """
    sidecar = load_sidecar(path, EXAMPLES_ROOT)
    assert sidecar.model_id == path.stem


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_has_one_batch_field(path: Path) -> None:
    """One `batching.batch`, and `batching.batch_conversion` only with batch 3 (ADR-JAA4, item 1).

    The key check does not find `batch_artifacts`: its Removed stub heading still names it.
    """
    resolved = resolve_sidecar_composition(path, EXAMPLES_ROOT)
    batching = resolved["batching"]
    batch = batching["batch"]
    assert not isinstance(batch, bool) and batch in (3, 1, "dynamic"), batching
    assert set(batching) <= {"batch", "batch_conversion"}, batching
    conversion = batching.get("batch_conversion")
    assert (batch == 3) == (conversion is not None), batching
    assert conversion in (None, {"profile_id": "static-batch-v1"}), batching
    for size, entry in resolved["sizes"].items():
        assert "batch_artifacts" not in entry["onnx"], size


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_gives_output_shapes_in_each_size(path: Path) -> None:
    """`onnx.output_shapes` of each size: one entry for each output, in order (ADR-JAA4, item 2).

    An entry has the dims of `outputs[i].shape`. Each fixed dim of that shape is equal or -1 in the
    entry. Dim 0 is `batching.batch`, or -1 for `dynamic`.
    """
    resolved = resolve_sidecar_composition(path, EXAMPLES_ROOT)
    outputs, batch = resolved["outputs"], resolved["batching"]["batch"]
    for size, entry in resolved["sizes"].items():
        shapes = entry["onnx"].get("output_shapes")
        assert isinstance(shapes, list) and len(shapes) == len(outputs), size
        for output, shape in zip(outputs, shapes, strict=True):
            where = (size, output["name"])
            assert isinstance(shape, list) and shape, where
            assert shape[0] == (-1 if batch == "dynamic" else batch), where
            family = output.get("shape")
            if family is None:
                continue
            assert len(shape) == len(family), where
            assert all(f == -1 or d in (f, -1) for f, d in zip(family, shape, strict=True)), where


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_the_hash_tool_finds_the_artifacts_of_each_size(path: Path) -> None:
    """`sidecar_refs` scans each `precision_artifacts` entry. A moved key hides an artifact from the hash check."""
    scanned = {
        artifact.filename
        for file in sidecar_refs.files(path, EXAMPLES_ROOT)
        for artifact in sidecar_refs._scan(file.read_text(encoding="utf-8")).artifacts
    }
    for size, entry in resolve_sidecar_composition(path, EXAMPLES_ROOT)["sizes"].items():
        names = {artifact["filename"] for artifact in entry["onnx"]["precision_artifacts"].values()}
        assert names and names <= scanned, (size, sorted(names - scanned))


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_has_only_keys_that_the_spec_defines(path: Path) -> None:
    """A key that the spec does not define is invalid (V-format.composition-5, ADR-0QKK)."""
    assert not unknown_keys(resolve_sidecar_composition(path, EXAMPLES_ROOT))


@pytest.mark.parametrize(
    ("where", "key"),
    [
        (("input", "resize"), "preserve_aspect_ratio"),
        (("object", "decode"), "requires_nms"),
        (("object", "decode"), "may_include_non_person_classes"),
        (("input",), "layout"),
        (("input", "resize"), "supports_dynamic_size"),
        (("outputs", 0), "rank"),
        (("sizes", "m", "onnx", "precision_artifacts", "fp32"), "input_dtype"),
        (("keypoint", "decode"), "is_3d"),
        (("keypoint",), "canonical_mapping"),
        # keypoint.groups (ADR-23F5) is now a name of score_map.groups. The path-aware validator
        # checks it: V-format.composition-5 in skellytracker/tests/model_spec/test_model_validation.py.
    ],
)
def test_the_key_check_finds_a_deleted_key(where: tuple[str | int, ...], key: str) -> None:
    sidecar = resolve_sidecar_composition(example_paths()[0], EXAMPLES_ROOT)

    def step(node: Any, name: str | int) -> Any:
        return node[name] if isinstance(name, int) else node.setdefault(name, {})

    functools.reduce(step, where, sidecar)[key] = True
    assert unknown_keys(sidecar) == [key]


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_declares_its_normalization(path: Path) -> None:
    """`input.normalization` is required (ADR-0QKK)."""
    assert "normalization" in resolve_sidecar_composition(path, EXAMPLES_ROOT)["input"]


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_keypoint_example_declares_its_geometry(path: Path) -> None:
    """`keypoint.geometry` is required at the keypoint level (ADR-90CE)."""
    keypoint = resolve_sidecar_composition(path, EXAMPLES_ROOT).get("keypoint")
    assert keypoint is None or keypoint.get("geometry") in {"2d", "3d"}


TOKENS = r"[a-z0-9]+(-[a-z0-9]+)*"  # the pattern of {family} and {variant} (V-common.identity-7)


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_follows_the_storage_layout(path: Path) -> None:
    """The folder and the keypoint detector id (V-common.identity-7, V-common.identity-8)."""
    parts = path.relative_to(EXAMPLES_ROOT / "detectors").parts
    if parts[0] == "object_detectors":
        assert len(parts) == 3, parts
        return
    assert parts[0] == "keypoint_detectors"
    assert len(parts) == 4, parts
    family, group = parts[1], parts[2]
    model_id = resolve_sidecar_composition(path, EXAMPLES_ROOT)["model_id"]
    assert re.fullmatch(TOKENS, family), parts
    assert model_id == f"{family}-{group}" or (
        model_id.startswith(f"{family}-{group}-")
        and re.fullmatch(TOKENS, model_id.removeprefix(f"{family}-{group}-"))
    ), (model_id, parts)
    keypoint_set = re.fullmatch(r"[a-z]+([1-9][0-9]*)", group)
    assert group in {"hand", "face", "body", "wholebody"} or keypoint_set, parts
    if keypoint_set:
        points = resolve_sidecar_composition(path, EXAMPLES_ROOT)["keypoint"]["point_names"]
        assert int(keypoint_set.group(1)) == len(points), (group, len(points))


PACKAGE = ("skellytracker",)


def test_the_placeholder_scan_reads_the_package_sidecars() -> None:
    shown = {p.relative_to(REPO_ROOT).as_posix() for p in placeholder_scan_paths(PACKAGE)}
    assert (
        "skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml"
        in shown
    )


def test_no_file_of_the_package_holds_the_placeholder() -> None:
    """The placeholder hash is valid only under `specs/model-sidecar/examples/` (V-common.sizes_and_artifacts-11)."""
    holders = placeholder_holders(PACKAGE)
    assert not holders, holders
