"""The gate tool `tools/intake_gate.py` runs the bundle checks that need the package or the ONNX stack."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import intake_bundle as ib
import intake_gate as gate
import numpy as np
import pytest
import yaml
from test_intake_bundle import YOLOX_SIDECAR, model_fields, pack_pipeline, pipeline_file

PACKAGE_STACK = ("skellytracker", "onnx", "onnxruntime")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "intakes"


TOOLS = Path(ib.__file__).resolve().parent
REPO = TOOLS.parent
# The tools that move to the specs repository with the specs, and the spec code that they load by path.
MOVING = (
    TOOLS / "intake_bundle.py",
    TOOLS / "make_vectors.py",
    TOOLS / "vector_form.py",
    TOOLS / "sidecar_trace.py",
    TOOLS / "sidecar_refs.py",
    TOOLS / "make_pipeline_schema.py",
    *sorted((TOOLS / "vector_formulas").glob("*.py")),
    *sorted((REPO / "specs" / "model-sidecar" / "reference").glob("*.py")),
    *sorted((REPO / "specs" / "pipeline" / "reference").glob("*.py")),
)
# The tests that move with the tools, and the conftest.py that they load. Each one runs in the
# specs repository, where the package is not installed. A test of the package stays here, in a
# file `test_package_<subject>.py`. A moving test can never import such a file.
TESTS = TOOLS / "tests"
MOVING_TESTS = tuple(
    TESTS / name
    for name in (
        "conftest.py",
        "test_changelog_revision.py",
        "test_examples.py",
        "test_intake_bundle.py",
        "test_land_fill.py",
        "test_pipeline_changelog.py",
        "test_pipeline_schema.py",
        "test_proposal_records.py",
        "test_retired_names.py",
        "test_sidecar_refs.py",
        "test_sidecar_trace.py",
        "test_traceability.py",
        "test_vectors.py",
    )
)
DYNAMIC_CALLS = ("import_module", "__import__", "spec_from_file_location", "find_spec", "importorskip")
# Each dynamic import call of the moving set: (file, function that holds the call). A new one needs a review.
KNOWN_DYNAMIC = {
    # Loads `<folder>/<section_module>.py` of a given folder. The callers give a reference folder or
    # the formula folder of the checkout, or the bundle reference folder of `fill` (ADR-AD33, item 5).
    ("tools/make_vectors.py", "load_reference"),
    # Loads the fixed file specs/model-sidecar/reference/sidecar_normalize.py of the checkout.
    ("tools/sidecar_trace.py", "_load_normalizer"),
    # Finds a top-level module name on the paths. It loads and runs nothing.
    ("tools/intake_bundle.py", "reference_problems"),
}


def _imports(path: Path) -> tuple[set[str], list[tuple[str, str]]]:
    """Return the module names that a file imports at any depth, and its dynamic import calls.

    A name of an `import_module`, `__import__` or `importorskip` call with a literal string counts
    as an import. An `importorskip` call with a literal string is not a dynamic import call.
    """
    names: set[str] = set()
    dynamic: list[tuple[str, str]] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.add(node.module or "")
        elif isinstance(node, ast.Call):
            callee = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if callee not in DYNAMIC_CALLS:
                continue
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                names.add(node.args[0].value)
                if callee == "importorskip":
                    continue  # an import of a named module, not a load of a file
            owner = min(
                (f for f in functions if f.lineno <= node.lineno <= (f.end_lineno or f.lineno)),
                key=lambda f: (f.end_lineno or f.lineno) - f.lineno,
                default=None,
            )
            dynamic.append((path.relative_to(REPO).as_posix(), owner.name if owner else "<module>"))
    return names, dynamic


def _chain() -> tuple[dict[Path, set[str]], list[tuple[str, str]]]:
    """Return the imports of each file of the import chain of `MOVING` and `MOVING_TESTS`, and the dynamic imports.

    A name is a local module when `<folder of the file>/<name>.py` or `tools/<name>.py` exists. The
    walk follows each local module.
    """
    seen: dict[Path, set[str]] = {}
    dynamic: list[tuple[str, str]] = []
    todo = [*MOVING, *MOVING_TESTS]
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        seen[path], calls = _imports(path)
        dynamic += calls
        for name in seen[path]:
            top = name.split(".")[0]
            todo += [p for p in (path.parent / f"{top}.py", TOOLS / f"{top}.py") if p.is_file()][:1]
    return seen, dynamic


def test_the_moving_tools_import_no_package_and_no_onnx_stack() -> None:
    """The moving tools and tests and their whole import chain must not import skellytracker, onnx or onnxruntime.

    These tools and their tests move to the specs repository with the specs, and the specs
    repository must not depend on the package. The rule applies to an import inside a function
    too, to each local module that a file imports, and to `import_module`, `__import__` or
    `pytest.importorskip` with a literal name. The checks that need these modules stay here:
    `tools/intake_gate.py`, `tools/sidecar_trace_package.py` and the tests `test_package_*.py`.
    """
    seen, _ = _chain()
    assert TOOLS / "check_private_data.py" in seen  # the walk follows the local modules
    assert TESTS / "test_intake_bundle.py" in seen and TESTS / "conftest.py" in seen
    found = [
        f"{path.relative_to(REPO).as_posix()}: {name}"
        for path, names in seen.items()
        for name in sorted(names)
        if name.split(".")[0] in PACKAGE_STACK
    ]
    assert found == []
    assert not [p for p in seen if p.name in ("intake_gate.py", "sidecar_trace_package.py")]


def test_a_moving_test_imports_only_moving_tests() -> None:
    """A test of the import chain that is not in `MOVING_TESTS` stays here, so a moving test must not import it."""
    seen, _ = _chain()
    staying = sorted(p.name for p in seen if p.parent == TESTS and p not in MOVING_TESTS)
    assert staying == []


def test_each_test_file_is_moving_or_staying() -> None:
    """A new test file of `tools/tests/` needs a place: `MOVING_TESTS`, or the reviewed list `STAYING_TESTS`."""
    assert {p.name for p in TESTS.glob("*.py")} == {p.name for p in MOVING_TESTS} | STAYING_TESTS
    assert not {p.name for p in MOVING_TESTS} & STAYING_TESTS


# The tests that stay in skellytracker: a test of a staying tool, or a test that needs the package.
STAYING_TESTS = {
    "test_bootstrap_kit.py",
    "test_camera_media.py",
    "test_certify_eps.py",
    "test_certify_hardware.py",
    "test_certify_platform.py",
    "test_check_ai_attribution.py",
    "test_check_dist_onnx.py",
    "test_check_ste_tokens.py",
    "test_decision_log.py",
    "test_dependency_pins.py",
    "test_docs_site.py",
    "test_ep_catalog.py",
    "test_graphify_hooks.py",
    "test_intake_gate.py",
    "test_landmark_schemas.py",
    "test_links.py",
    "test_onnx_stack.py",
    "test_package_examples.py",
    "test_package_sidecar_trace.py",
    "test_package_traceability.py",
    "test_package_vectors.py",
    "test_package_verified_against.py",
    "test_pipeline_node_catalog.py",
    "test_pipeline_package_schema.py",
    "test_private_data.py",
    "test_private_data_allowed_url.py",
    "test_run_checks.py",
    "test_sidecar_normalize.py",
}


def test_the_gate_takes_the_intakes_folder_and_the_patch_scope_of_its_own_checkout() -> None:
    """`tools/intake_bundle.py` has no default root (ADR-2DJ8, item 7). The gate stays in this checkout."""
    assert not hasattr(ib, "DEFAULT_ROOT")
    assert gate.DEFAULT_ROOT == REPO / "intakes"
    assert gate.PACKAGE_FOLDER == ib.PATCH_SCOPE == "skellytracker/"
    assert (REPO / gate.PACKAGE_FOLDER / "__init__.py").is_file()


def test_each_dynamic_import_of_the_moving_tools_is_known() -> None:
    """A dynamic import can load any file. Each one in the import chain of `MOVING` is reviewed (ADR-AD33)."""
    _, dynamic = _chain()
    assert set(dynamic) == KNOWN_DYNAMIC


# --------------------------------------------------------------------------------------------
# batch: the batch-conversion check. The graph builder copies the reshape model of
# skellytracker/tests/test_batch_conversion.py and adds a bias, a dynamic form and an empty form.
# --------------------------------------------------------------------------------------------

ITEMS = np.arange(18, dtype=np.float32).reshape(6, 3)


def onnx_file(
    path: Path, batch: int | str, *, bias: float = 0.0, empty: bool = False, ir_version: int | None = None
) -> Path:
    """x[N, 3] -> Reshape([N, 3]) -> Add(bias) -> y[N, 3], or y[N, 0] with `empty`."""
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    dim0 = "N" if batch == "dynamic" else batch
    lead = -1 if batch == "dynamic" else batch
    initializers = [
        numpy_helper.from_array(np.array([lead, 3], dtype=np.int64), name="shape"),
        numpy_helper.from_array(np.array(bias, dtype=np.float32), name="bias"),
    ]
    nodes = [helper.make_node("Reshape", ["x", "shape"], ["r"]), helper.make_node("Add", ["r", "bias"], ["a"])]
    if empty:
        for name, value in (("starts", 0), ("ends", 0), ("axes", 1)):
            initializers.append(numpy_helper.from_array(np.array([value], dtype=np.int64), name=name))
        nodes.append(helper.make_node("Slice", ["a", "starts", "ends", "axes"], ["y"]))
    else:
        nodes.append(helper.make_node("Identity", ["a"], ["y"]))
    graph = helper.make_graph(
        nodes,
        "fixture",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [dim0, 3])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [dim0, 0 if empty else 3])],
        initializers,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    if ir_version is not None:
        model.ir_version = ir_version
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, path)
    return path


@pytest.fixture
def family(tmp_path: Path):  # noqa: ANN201
    """Return a function that writes ONNX files and gives (root, fields, out) for batch_check."""
    pytest.importorskip("onnxruntime")
    root = tmp_path / "freemocap" / "skellytracker" / "intakes"
    out = tmp_path / "payload" / "batch"

    def make(batches: dict, items: np.ndarray | None = ITEMS) -> tuple[Path, dict, Path]:
        external = []
        for batch, options in batches.items():
            name = f"m_b{batch}_fp32.onnx"
            onnx_file(tmp_path / "Exporter" / name, batch, **options)
            external.append({
                "path": f"../../Exporter/{name}", "role": "artifact", "size": "n", "batch": batch,
                "precision": "fp32", "published": batch == gate.SOURCE_BATCH,
            })
        if items is not None:
            (out / "inputs").mkdir(parents=True, exist_ok=True)
            np.save(out / "inputs" / "n.npy", items)
        return root, model_fields(external=external, batch_forced=None, batch_forced_reason=None), out

    return make


def test_batch_converts_down_and_up_and_writes_the_fragment(family) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}})
    report = gate.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("converts", None)
    assert [t["target"] for t in report["tuples"]] == [1, 2, 6]
    upward = report["tuples"][2]
    assert upward["v3"]["result"] == "pass"
    assert upward["v5"]["result"] == "pass"
    assert upward["v5"]["B"]["outputs"]["y"]["rows"] == 6
    assert yaml.safe_load((out / "conversion.yaml").read_text(encoding="utf-8")) == {
        "batching": {"batch_conversion": {"profile_id": "static-batch-v1"}}
    }
    assert json.loads((out / "report.json").read_text(encoding="utf-8")) == json.loads(json.dumps(report))
    assert not (out / "residual-diff.json").exists()


def test_batch_does_not_convert_a_batch_dependent_export(family) -> None:  # noqa: ANN001
    batches = {1: {"bias": 1.0}, 2: {"bias": 1.0}, 3: {}, 6: {"bias": 1.0}, "dynamic": {"bias": 1.0}}
    root, fields, out = family(batches)
    report = gate.batch_check(fields, out, root=root)
    assert report["batch_conversion"] == "does not convert"
    assert {t["v5"]["result"] for t in report["tuples"]} == {"fail"}
    assert (out / "residual-diff.json").is_file()
    assert not (out / "conversion.yaml").exists()
    dynamic = report["dynamic_check"][0]
    assert dynamic["result"] == "fail"
    assert dynamic["static"]["b3/A"]["pass"] is False


@pytest.mark.parametrize("gone", [(3,), (6,), (1, 2, 6)])
def test_batch_needs_each_verification_batch(family, gone: tuple) -> None:  # noqa: ANN001
    """Also a b3-only family: V0 does not skip it (ADR-JB5J, audit finding C15)."""
    root, fields, out = family({b: {} for b in (1, 2, 3, 6) if b not in gone})
    report = gate.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "missing-verification-batch")
    assert report["v0"]["missing"] == [["n", "fp32", b] for b in gone]
    assert report["tuples"] == []


def test_batch_gives_to_run_for_a_family_with_no_file(family) -> None:  # noqa: ANN001
    """An empty `external` list is not a dynamic-only family (ADR-JB5J, item 3)."""
    root, fields, out = family({})
    report = gate.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "missing-verification-batch")


def test_batch_skips_the_check_of_a_forced_fallback(family) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}})
    fields |= {"batch_forced": 1, "batch_forced_reason": "the user forces b1"}
    report = gate.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["v0"]) == ("not applicable", {"result": "not applicable", "missing": []})


def test_batch_gives_to_run_when_the_runtime_cannot_load_a_file(family) -> None:  # noqa: ANN001
    import onnx
    root, fields, out = family({1: {}, 2: {"ir_version": onnx.IR_VERSION + 1}, 3: {}, 6: {}})
    report = gate.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "host-runtime-cannot-load")
    assert list(report["v0b"]) == ["../../Exporter/m_b2_fp32.onnx"]


def test_batch_gives_no_signal_when_every_output_is_empty(family) -> None:  # noqa: ANN001
    root, fields, out = family({b: {"empty": True} for b in (1, 2, 3, 6)})
    report = gate.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "no-signal")


def test_batch_fails_v6_on_a_dynamic_file_with_other_output_names(family, tmp_path: Path) -> None:  # noqa: ANN001
    import onnx
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}, "dynamic": {}})
    path = tmp_path / "Exporter" / "m_bdynamic_fp32.onnx"
    model = onnx.load(str(path))
    model.graph.node[-1].output[0] = "z"
    model.graph.output[0].name = "z"
    onnx.save(model, str(path))
    report = gate.batch_check(fields, out, root=root)
    assert report["dynamic_check"][0]["result"] == "fail"


def test_batch_gives_no_signal_when_v6_compares_nothing(family) -> None:  # noqa: ANN001
    root, fields, out = family({"dynamic": {"empty": True}})
    check = gate.batch_check(fields, out, root=root)["dynamic_check"][0]
    assert (check["result"], check["reason"]) == ("to run", "no-signal")


def reshape_by_constant(path: Path, batch: int | str) -> Path:
    """x[B, 3] -> Reshape([3B]) -> Sin -> Reshape([B, 3]): the [3B] constant hides the batch."""
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    dim0 = "N" if batch == "dynamic" else batch
    flat = -1 if batch == "dynamic" else 3 * batch
    lead = -1 if batch == "dynamic" else batch
    graph = helper.make_graph(
        [
            helper.make_node("Reshape", ["x", "flat"], ["f"]),
            helper.make_node("Sin", ["f"], ["s"]),
            helper.make_node("Reshape", ["s", "back"], ["y"]),
        ],
        "fixture",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [dim0, 3])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [dim0, 3])],
        [
            numpy_helper.from_array(np.array([flat], dtype=np.int64), name="flat"),
            numpy_helper.from_array(np.array([lead, 3], dtype=np.int64), name="back"),
        ],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, path)
    return path


def test_batch_gives_does_not_convert_when_the_converted_graph_does_not_run(family, tmp_path: Path) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}})
    for batch in (1, 2, 3, 6):
        reshape_by_constant(tmp_path / "Exporter" / f"m_b{batch}_fp32.onnx", batch)
    (out / "conversion.yaml").write_text("old\n", encoding="utf-8")
    report = gate.batch_check(fields, out, root=root)
    assert report["batch_conversion"] == "does not convert"
    assert not (out / "conversion.yaml").exists()


def test_batch_takes_a_dynamic_non_batch_dim_from_input_b(family, tmp_path: Path) -> None:  # noqa: ANN001
    import onnx
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}, "dynamic": {}})
    path = tmp_path / "Exporter" / "m_bdynamic_fp32.onnx"
    model = onnx.load(str(path))
    model.graph.input[0].type.tensor_type.shape.dim[1].dim_param = "C"
    onnx.save(model, str(path))
    report = gate.batch_check(fields, out, root=root)
    assert report["batch_conversion"] == "converts"
    assert report["dynamic_check"][0]["result"] == "pass"
    assert (out / "report.json").is_file()


def test_batch_checks_a_dynamic_export_against_itself(family) -> None:  # noqa: ANN001
    """A dynamic-only family with no_static_reason needs no batch_forced: V0 gives `not applicable` (ADR-JB5J)."""
    root, fields, out = family({"dynamic": {}})
    fields |= {"no_static_reason": "the upstream export fixes a dynamic batch"}
    report = gate.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["v0"]) == ("not applicable", {"result": "not applicable", "missing": []})
    check = report["dynamic_check"][0]
    assert check["result"] == "pass"
    assert check["static"] == {}
    assert check["self"] == {"b2/A/y": "pass", "b3/A/y": "pass", "b2/B/y": "pass", "b3/B/y": "pass"}


def test_batch_checks_a_forced_dynamic_export_against_the_static_files_that_exist(family) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, "dynamic": {}})
    fields |= {"batch_forced": "dynamic", "batch_forced_reason": "the user forces dynamic"}
    check = gate.batch_check(fields, out, root=root)["dynamic_check"][0]
    assert (check["result"], sorted(check["static"])) == ("pass", ["b1/A", "b1/B"])


def test_batch_runs_a_dynamic_only_family_without_a_reason(family) -> None:  # noqa: ANN001
    """Without no_static_reason or batch_forced, V0 of a dynamic-only family is `to run` (ADR-JB5J, item 3)."""
    root, fields, out = family({"dynamic": {}})
    report = gate.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "missing-verification-batch")


def test_batch_gives_v6_to_run_without_input_b(family) -> None:  # noqa: ANN001
    root, fields, out = family({"dynamic": {}}, items=None)
    fields |= {"no_static_reason": "the upstream export fixes a dynamic batch"}
    report = gate.batch_check(fields, out, root=root)
    check = report["dynamic_check"][0]
    assert (report["batch_conversion"], check["result"]) == ("not applicable", "to run")
    assert "input B not found" in check["reason"]


@pytest.mark.parametrize(
    ("items", "message"),
    [(ITEMS[:3], "must hold 6 items"), (np.stack([ITEMS[0]] * 6), "more than once"), (None, "input B not found")],
)
def test_batch_needs_input_b_with_six_different_items(family, items, message: str) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}}, items=items)
    with pytest.raises(gate.BundleError, match=message):
        gate.batch_check(fields, out, root=root)


def test_batch_runs_only_in_the_venv_of_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(gate.sys, "prefix", str(tmp_path))
    assert gate.main(["batch", "--fields", str(tmp_path / "f.json"), "--out", str(tmp_path / "batch")]) == 1
    assert "batch runs only in the .venv of the checkout" in capsys.readouterr().err


def tiny_model(path: Path, domain: str = "", location: str | None = None) -> Path:
    """y = Relu(x), or y = x + w with the external data of w at `location`."""
    import onnx
    from onnx import TensorProto, helper

    nodes = [helper.make_node("Relu", ["x"], ["y"], domain=domain)]
    initializers = []
    if location is not None:
        weight = helper.make_tensor("w", TensorProto.FLOAT, [1], [1.0])
        weight.ClearField("float_data")
        weight.data_location = TensorProto.EXTERNAL
        weight.external_data.add(key="location", value=location)
        initializers.append(weight)
        nodes = [helper.make_node("Add", ["x", "w"], ["y"])]
    graph = helper.make_graph(
        nodes, "tiny", [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1])], initializers,
    )
    opsets = [helper.make_opsetid("", 17)] + ([helper.make_opsetid(domain, 1)] if domain else [])
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(helper.make_model(graph, opset_imports=opsets), str(path))
    return path


def test_the_onnx_check_passes_a_plain_model_and_a_local_external_file(tmp_path: Path) -> None:
    assert gate.onnx_problems(tiny_model(tmp_path / "m.onnx")) == []
    assert gate.onnx_problems(tiny_model(tmp_path / "e.onnx", location="e.onnx.data")) == []
    assert gate.onnx_problems(tiny_model(tmp_path / "s.onnx", domain="com.microsoft")) == []


@pytest.mark.parametrize(
    ("options", "finding"),
    [
        ({"domain": "my.custom"}, "the opset domain 'my.custom' is not built into onnxruntime"),
        ({"domain": "my.custom"}, "has the domain 'my.custom', which onnxruntime does not build in"),
        ({"location": "../secret.bin"}, "external data outside the folder of the model: '../secret.bin'"),
        ({"location": "/etc/passwd"}, "external data outside the folder of the model: '/etc/passwd'"),
        ({"location": "C:\\Windows\\win.ini"}, "external data outside the folder of the model"),
        ({"location": "a/..\\..\\b"}, "external data outside the folder of the model"),
    ],
)
def test_the_onnx_check_refuses_a_custom_domain_and_external_data_outside_the_folder(
    tmp_path: Path, options: dict, finding: str
) -> None:
    findings = gate.onnx_problems(tiny_model(tmp_path / "m.onnx", **options))
    assert any(finding in f for f in findings), findings


def external(tensor, location: str):  # noqa: ANN001, ANN201
    from onnx import TensorProto

    tensor.ClearField("float_data")
    tensor.ClearField("int64_data")
    tensor.data_location = TensorProto.EXTERNAL
    tensor.external_data.add(key="location", value=location)
    return tensor


@pytest.mark.parametrize("kind", ["function domain", "function external", "sparse attribute"])
def test_the_onnx_check_refuses_a_local_function_and_a_sparse_attribute(tmp_path: Path, kind: str) -> None:
    import onnx
    from onnx import TensorProto, helper

    value = external(helper.make_tensor("c", TensorProto.FLOAT, [1], [1.0]), "../secret.bin")
    functions, nodes = [], [helper.make_node("Relu", ["x"], ["y"])]
    if kind == "sparse attribute":
        values = external(helper.make_tensor("v", TensorProto.FLOAT, [1], [1.0]), "../secret.bin")
        sparse = helper.make_sparse_tensor(values, helper.make_tensor("i", TensorProto.INT64, [1], [0]), [1])
        nodes = [helper.make_node("Constant", [], ["y"], sparse_value=sparse)]
    else:
        body = (
            [helper.make_node("Relu", ["a"], ["b"], domain="my.custom")]
            if kind == "function domain"
            else [helper.make_node("Constant", [], ["b"], value=value)]
        )
        functions = [helper.make_function("com.microsoft", "F", ["a"], ["b"], body, [helper.make_opsetid("", 17)])]
        nodes = [helper.make_node("F", ["x"], ["y"], domain="com.microsoft")]
    graph = helper.make_graph(
        nodes, "tiny", [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1])],
    )
    opsets = [helper.make_opsetid("", 17), helper.make_opsetid("com.microsoft", 1)]
    onnx.save(helper.make_model(graph, opset_imports=opsets, functions=functions), str(tmp_path / "m.onnx"))
    finding = "'my.custom'" if kind == "function domain" else "external data outside the folder of the model: '../secret.bin'"
    assert any(finding in f for f in gate.onnx_problems(tmp_path / "m.onnx")), kind


def test_the_onnx_check_refuses_a_file_that_onnx_cannot_read(tmp_path: Path) -> None:
    (tmp_path / "m.onnx").write_bytes(b"\xff not a model")
    assert gate.onnx_problems(tmp_path / "m.onnx")[0].startswith("onnx cannot read the file")


def test_batch_refuses_a_model_before_any_run(family, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}})
    tiny_model(tmp_path / "Exporter" / "m_b2_fp32.onnx", domain="my.custom")

    def no_run(*_args: object) -> None:
        raise AssertionError("batch ran a model")

    monkeypatch.setattr(gate, "_load_problem", no_run)
    monkeypatch.setattr(gate._Runner, "session", no_run)
    with pytest.raises(gate.BundleError, match=r"batch does not run \.\./\.\./Exporter/m_b2_fp32\.onnx: .*my\.custom"):
        gate.batch_check(fields, out, root=root)
    assert not (out / "report.json").exists()


def test_a_valid_pipeline_file_passes_the_load_checks(tmp_path: Path, root: Path, capsys: pytest.CaptureFixture) -> None:
    pack_pipeline(tmp_path, root, pipeline_file(gate.sha256(YOLOX_SIDECAR.read_bytes())))
    findings = gate.verify("pipeline-yolox-boxes@openmmlab-exporter", root)
    assert not [f for f in findings if "load checks" in f], findings
    assert "load checks" not in capsys.readouterr().err  # the checks that need the sidecars did run


@pytest.mark.parametrize(
    ("old", "new", "rule"),
    [
        ('schema_version: "2.0.0"', 'schema_version: "9.9.9"', "V-pipeline.file-1"),  # a structural rule of the loader
        ("size: m", "size: zz", "V-node.onnx_model-4"),  # a rule that needs the sidecar
        ("boxes: person.boxes", "wholebody: person.keypoints", "V-node.onnx_model-2"),
    ],
)
def test_verify_runs_the_load_checks_of_the_package(tmp_path: Path, root: Path, old: str, new: str, rule: str) -> None:
    text = pipeline_file(gate.sha256(YOLOX_SIDECAR.read_bytes()))
    assert old in text
    pack_pipeline(tmp_path, root, text.replace(old, new))
    findings = gate.verify("pipeline-yolox-boxes@openmmlab-exporter", root)
    assert any(f.startswith(f"yolox-boxes.pipeline.yaml: the load checks refuse it: {rule}") for f in findings), findings


def test_the_sidecar_load_checks_do_not_run_for_a_key_with_no_package_sidecar(
    tmp_path: Path, root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(gate, "_package_keys", lambda repo, yaml: set())
    pack_pipeline(tmp_path, root, pipeline_file(gate.sha256(YOLOX_SIDECAR.read_bytes())).replace("size: m", "size: zz"))
    findings = gate.verify("pipeline-yolox-boxes@openmmlab-exporter", root)
    assert not [f for f in findings if "load checks" in f], findings
    assert "the load checks that need the sidecars did not run" in capsys.readouterr().err


def test_each_tracked_parity_folder_passes_the_parity_check() -> None:
    """The reference files of the landed models (ADR-2DJ8, item 6). With no folder yet, the test checks nothing."""
    for folder in sorted((gate.REPO_ROOT / "skellytracker/tests/sidecar/fixtures/parity").glob("*/")):
        assert ib.parity_problems(folder, yaml) == [], folder.name
