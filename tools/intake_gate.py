#!/usr/bin/env python3
"""Run the checks of the bundle gate that need the skellytracker package or the ONNX stack.

`tools/intake_bundle.py` packs, lists, verifies and records the hand-over bundles in `intakes/`.
It moves to the specs repository with the specs, and the specs repository must not depend on the
package. So it imports no skellytracker, onnx or onnxruntime. This tool holds the checks that need
them. It stays in this repository, as the part of the acceptance gate that this repository runs.

Usage::

    uv run python -B tools/intake_gate.py verify BUNDLE [--root INTAKES]
    uv run python -B tools/intake_gate.py batch --fields FILE --out DIR [--inputs DIR] [--root INTAKES]

`verify` gives the findings of `intake_bundle.verify` (the format checks), then the findings of the
load checks of the package on the pipeline file of a `pipeline` bundle (ADR-ZYS9, item 7; ADR-271H,
item 3). The load checks run only when the format checks give no finding for the pipeline file.
They run no ONNX file and no file of the bundle (ADR-AD33). `batch` is the batch-conversion check
(`specs/model-sidecar/model-addition-workflow/batch-conversion-check.md`). It imports onnx,
onnxruntime and the skellytracker converter, so it runs only in the `.venv` of this checkout.
`--fields` is a fields file or a manifest. No sub-command writes a response file: the
skellytracker session writes them.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
import tempfile
from pathlib import Path, PureWindowsPath

import intake_bundle
from intake_bundle import (
    PROFILE,
    SOURCE_BATCH,
    VERIFICATION_BATCHES,
    BundleError,
    _git,
    _sidecars,
    _unique_yaml,
    bundles,
    manifest_problems,
    sha256,
)

# This tool stays in the repository that holds the hand-over folder and the package. So it can
# take its default `--root` from its own place. `tools/intake_bundle.py` has no default root.
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "intakes"
# The package sidecar root and the package folder of this repository, relative to the checkout.
# `verify` gives them to `intake_bundle.verify`, which names no folder of this repository.
PACKAGE_SIDECARS = "skellytracker/core/model_zoo/detectors"
PACKAGE_FOLDER = "skellytracker/"  # the one folder that a patch of a bundle can change
TARGETS = (1, 2, 6)
DYNAMIC_BATCHES = (1, 2, 3)
TOLERANCE = {"fp32": 1e-5, "fp16": 1e-3}
INPUT_B_ITEMS = 6


# --------------------------------------------------------------------------------------------
# The load checks of the package for a pipeline bundle (imports skellytracker)
# --------------------------------------------------------------------------------------------


def _pipeline_load_problems(path: Path, rel: str, data: dict, repo: Path, yaml) -> list[str]:  # noqa: ANN001
    """Return the findings of the load checks of the package for a pipeline file (ADR-ZYS9, item 7; ADR-271H, item 3).

    Safety boundary (ADR-AD33): the pipeline file is data. The loader of the package reads it with a
    safe YAML load. The node types are a closed set. The checks read only the package sidecars of
    this checkout, with an empty user root. They open no session and run no ONNX file and no file
    of a bundle. An ONNX file that is absent is a start check, not a load check: it gives no finding.
    """
    from skellytracker.core.pipelines._runtime.resolve import resolve
    from skellytracker.core.pipelines.loading import load_pipeline_file

    try:
        config = load_pipeline_file(path)
    except ValueError as exc:
        return [f"{rel}: the load checks refuse it: {' '.join(str(exc).split())[:400]}"]
    keys = [str(node["params"]["key"]) for node in data["nodes"] if node.get("type") == "onnx_model"]
    package = _package_keys(repo, yaml)
    if absent := sorted(set(keys) - package):
        # No text tells what `verify` does for a sidecar that is only in a `depends_on` bundle or in
        # the spec examples. The tool prints the fact and gives no finding.
        print(f"note: {rel}: the load checks that need the sidecars did not run: no package sidecar has the key {absent}", file=sys.stderr)
        return []
    with tempfile.TemporaryDirectory() as empty:
        try:
            resolve(config, Path(empty))
        except ValueError as exc:
            return [f"{rel}: the load checks refuse it: {' '.join(str(exc).split())[:400]}"]
    return []


def _package_keys(repo: Path, yaml) -> set[str]:  # noqa: ANN001
    """Return the key `<model_id>@<source.name>` of each sidecar in the package sidecar root."""
    keys = set()
    for path in sorted((repo / PACKAGE_SIDECARS).rglob("*.yaml")):
        keys |= {f"{path.stem}@{name}" for name in _sidecars(path.stem, [path.parent], yaml)}
    return keys

def load_findings(
    name: str, findings: list[str], root: Path = DEFAULT_ROOT, repo: Path = REPO_ROOT, overlay: Path | None = None
) -> list[str]:
    """Return the findings of the load checks for the pipeline file of the bundle `name`.

    `findings` are the findings of the format checks. A bundle that is not a `pipeline` bundle, a
    bad manifest, a missing pipeline file and a format finding for that file give no load check.
    """
    found = bundles(root, repo)
    if overlay is not None:
        found.update(bundles(overlay, repo))
    info = found.get(name)
    if info is None or info["version"] is None or info["state"] == "unreadable manifest":
        return []
    manifest = info["manifest"]
    if manifest_problems(manifest) or manifest["kind"] != "pipeline":
        return []
    rel = f"{manifest['name']}.pipeline.yaml"
    path = info["dir"] / f"v{info['version']}" / rel
    if not path.is_file() or any(f.startswith(f"{rel}: ") for f in findings):
        return []
    import yaml

    data = _unique_yaml(path.read_text(encoding="utf-8"), yaml)
    return _pipeline_load_problems(path, rel, data, repo, yaml)


def verify(name: str, root: Path = DEFAULT_ROOT, repo: Path = REPO_ROOT, overlay: Path | None = None) -> list[str]:
    """Return the findings of `intake_bundle.verify`, then the findings of the package load checks.

    `intake_bundle.verify` gets the package sidecars of `repo` (`PACKAGE_SIDECARS`), so its pipeline
    check also finds a landed package sidecar. It also gets the package folder (`PACKAGE_FOLDER`),
    the one folder that a patch can change.
    """
    findings = intake_bundle.verify(
        name, root, repo, overlay, package_sidecars=repo / PACKAGE_SIDECARS, patch_scope=PACKAGE_FOLDER
    )
    return findings + load_findings(name, findings, root, repo, overlay)


# --------------------------------------------------------------------------------------------
# batch (imports onnx, onnxruntime and skellytracker: run it in the .venv of this checkout)
# --------------------------------------------------------------------------------------------


def _facts(model) -> dict:  # noqa: ANN001
    """Return the graph facts that the V1 report compares."""
    graph = model.graph

    def dims(items) -> dict:  # noqa: ANN001
        return {v.name: [d.dim_param or d.dim_value for d in v.type.tensor_type.shape.dim] for v in items}

    counts: dict[str, int] = {}
    for node in graph.node:
        counts[node.op_type] = counts.get(node.op_type, 0) + 1
    return {
        "ir_version": model.ir_version,
        "opset_import": {o.domain or "ai.onnx": o.version for o in model.opset_import},
        "producer": f"{model.producer_name} {model.producer_version}".strip(),
        "inputs": dims(graph.input),
        "outputs": dims(graph.output),
        "value_info": dims(graph.value_info),
        "initializers": {t.name: sha256(t.SerializeToString()) for t in graph.initializer},
        "metadata": {p.key: p.value for p in model.metadata_props},
        "node_counts": counts,
    }


def graph_diff(path_a: Path, path_b: Path) -> dict:
    """Return each fact of the V1 report that differs, as {fact: [a, b]} or {fact: {name: [a, b]}}."""
    import onnx

    a, b = (_facts(onnx.load(str(p), load_external_data=False)) for p in (path_a, path_b))
    diff: dict = {}
    for key in a:
        if isinstance(a[key], dict):
            names = sorted(set(a[key]) | set(b[key]))
            changed = {n: [a[key].get(n), b[key].get(n)] for n in names if a[key].get(n) != b[key].get(n)}
            if changed:
                diff[key] = changed
        elif a[key] != b[key]:
            diff[key] = [a[key], b[key]]
    return diff


def _diff_counts(diff: dict) -> dict:
    return {key: len(value) if isinstance(value, dict) else 1 for key, value in diff.items()}


# The operator domains that onnxruntime builds in: the domains of
# `onnxruntime.capi.onnxruntime_pybind11_state.get_all_operator_schema()` of onnxruntime 1.27.0
# (CPU), and "ai.onnx", the other name of "".
ORT_DOMAINS = frozenset({"", "ai.onnx", "ai.onnx.ml", "com.microsoft", "com.microsoft.nchwc", "com.ms.internal.nhwc"})


def _sparse(items) -> list:  # noqa: ANN001
    return [t for s in items for t in (s.values, s.indices)]


def _attribute_tensors(attributes) -> list:  # noqa: ANN001
    return [t for a in attributes for t in (a.t, *a.tensors, *_sparse([a.sparse_tensor, *a.sparse_tensors]))]


def _graph_problems(graph, folder: Path, nodes=None, tensors=None) -> list[str]:  # noqa: ANN001
    """Return the node domains and the external data locations of `graph` and its subgraphs that `batch` refuses.

    For a model-local function, `nodes` and `tensors` give its nodes and the tensors of its attributes.
    """
    from onnx import TensorProto

    found = []
    if nodes is None:
        nodes, tensors = graph.node, [*graph.initializer, *_sparse(graph.sparse_initializer)]
    tensors = list(tensors)
    for node in nodes:
        if node.domain not in ORT_DOMAINS:
            found.append(f"the node {node.name or node.op_type} has the domain {node.domain!r}, which onnxruntime does not build in")
        tensors += _attribute_tensors(node.attribute)
        for attribute in node.attribute:
            found += [p for g in (attribute.g, *attribute.graphs) for p in _graph_problems(g, folder)]
    for tensor in tensors:
        if tensor.data_location != TensorProto.EXTERNAL:
            continue
        location = next((e.value for e in tensor.external_data if e.key == "location"), "")
        target = (folder / location).resolve()
        if not location or location.startswith(("/", "\\")) or PureWindowsPath(location).drive or Path(location).is_absolute() or ".." in location or not target.is_relative_to(folder):
            found.append(f"the tensor {tensor.name} has external data outside the folder of the model: {location!r}")
    return found


def onnx_problems(path: Path) -> list[str]:
    """Return why `batch` refuses an ONNX file (ADR-AD33, item 4). It reads the file with onnx only and runs nothing.

    `batch` refuses an operator domain that onnxruntime does not build in (`ORT_DOMAINS`), and
    external data with an absolute location, a `..` or a location outside the folder of the model.
    It checks the graph, its subgraphs, the model-local functions, the initializers and the dense
    and sparse tensors of each attribute.
    """
    import onnx

    try:
        model = onnx.load(str(path), load_external_data=False)
    except Exception as exc:  # noqa: BLE001  # any file that onnx cannot read is refused
        return [f"onnx cannot read the file: {type(exc).__name__}"]
    opsets = [*model.opset_import, *(o for f in model.functions for o in f.opset_import)]
    found = [f"the opset domain {o.domain!r} is not built into onnxruntime" for o in opsets if o.domain not in ORT_DOMAINS]
    folder = path.parent.resolve()
    for function in model.functions:  # model-local functions: their nodes and their attribute defaults
        found += _graph_problems(None, folder, function.node, _attribute_tensors(function.attribute_proto))
    return list(dict.fromkeys(found + _graph_problems(model.graph, folder)))


def _load_problem(path: Path) -> str | None:
    """V0b: return why the onnx and onnxruntime of this environment cannot load the file, or None."""
    import onnx
    os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")  # ADR-BZ7X
    import onnxruntime

    model = onnx.load(str(path), load_external_data=False)
    if model.ir_version > onnx.IR_VERSION:
        return f"ir_version {model.ir_version} is above {onnx.IR_VERSION} of onnx {onnx.__version__}"
    schemas = onnx.defs.get_all_schemas_with_history()
    for opset in model.opset_import:
        if opset.domain in ("", "ai.onnx"):
            top = onnx.defs.onnx_opset_version()
        else:
            top = max((s.since_version for s in schemas if s.domain == opset.domain), default=None)
        if top is not None and opset.version > top:
            return f"opset {opset.domain or 'ai.onnx'} {opset.version} is above {top} of onnx {onnx.__version__}"
    try:
        onnxruntime.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    except Exception as exc:  # noqa: BLE001  # any refusal of the runtime is the reason
        return f"onnxruntime {onnxruntime.__version__}: {exc}"
    return None


class _Runner:
    """Run ONNX files on the CPU, with the inputs of V5 and V6."""

    DTYPES = {"tensor(float)": "float32", "tensor(float16)": "float16", "tensor(uint8)": "uint8"}

    def __init__(self) -> None:
        import numpy
        os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")  # ADR-BZ7X
        import onnxruntime

        self.np, self.ort, self.sessions = numpy, onnxruntime, {}

    def session(self, path: Path):  # noqa: ANN201
        if path not in self.sessions:
            self.sessions[path] = self.ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        return self.sessions[path]

    @staticmethod
    def batched(item, batch: int) -> bool:  # noqa: ANN001
        """An input has a batch axis when dim 0 is symbolic or equals the batch of the graph."""
        dims = list(item.shape)
        return bool(dims) and (not isinstance(dims[0], int) or dims[0] == batch)

    def _shape(self, item, batch: int, rest: tuple | None = None) -> list[int]:  # noqa: ANN001
        """Return the feed shape. `rest` (the dims of input B after dim 0) fills a symbolic dim of the first input."""
        dims = list(item.shape)
        if not self.batched(item, batch):
            shape = dims
        else:
            tail = dims[1:]
            if rest is not None and len(rest) == len(tail):
                tail = [d if isinstance(d, int) else int(r) for d, r in zip(tail, rest, strict=True)]
            shape = [batch, *tail]
        if not all(isinstance(d, int) for d in shape):
            raise BundleError(f"input {item.name} has a dynamic dim other than dim 0: {item.shape}")
        return shape

    def _dtype(self, item) -> str:  # noqa: ANN001
        if item.type not in self.DTYPES:
            raise BundleError(f"input {item.name} has the type {item.type}: batch takes float, float16 or uint8")
        return self.DTYPES[item.type]

    def input_a(self, path: Path, batch: int, rest: tuple | None = None) -> dict:
        """Input A: seed 42; float inputs uniform in [0, 1), uint8 inputs integers in [0, 256)."""
        rng = self.np.random.default_rng(42)
        feeds = {}
        for index, item in enumerate(self.session(path).get_inputs()):
            shape, dtype = self._shape(item, batch, rest if index == 0 else None), self._dtype(item)
            if dtype == "uint8":
                feeds[item.name] = rng.integers(0, 256, shape, dtype=self.np.uint8)
            else:
                feeds[item.name] = rng.random(shape).astype(dtype)
        return feeds

    def input_b(self, path: Path, items, batch: int) -> dict:  # noqa: ANN001
        """Input B: the first `batch` items feed the first input. Other inputs take input A."""
        feeds = self.input_a(path, batch, items.shape[1:])
        first = self.session(path).get_inputs()[0]
        dtype = self._dtype(first)
        data = items[:batch]
        if dtype == "float16" and data.dtype == self.np.float32:
            data = data.astype(self.np.float16)
        if data.dtype != self.np.dtype(dtype) or list(data.shape) != self._shape(first, batch, items.shape[1:]):
            raise BundleError(f"input B {data.dtype} {list(data.shape)} does not fit the input {first.name}")
        feeds[first.name] = data
        return feeds

    def run(self, path: Path, feeds: dict) -> dict:
        session = self.session(path)
        names = [o.name for o in session.get_outputs()]
        return dict(zip(names, session.run(names, feeds), strict=True))

    def compare(self, got: dict, want: dict, tolerance: float) -> dict:
        """Compare two runs with the V5 rules. A run with only empty outputs is `empty`."""
        np = self.np
        result: dict = {"pass": list(got) == list(want), "outputs": {}, "empty": False}
        if not result["pass"]:
            result["error"] = f"output names {list(got)} and {list(want)} differ"
            return result
        for name, x in got.items():
            y = want[name]
            entry: dict = {"shape": list(x.shape), "rows": int(x.shape[0]) if x.ndim else None}
            if x.dtype != y.dtype or x.shape != y.shape:
                entry["error"] = f"{x.dtype} {list(x.shape)} against {y.dtype} {list(y.shape)}"
                result["pass"] = False
            elif x.size:
                a, b = x.astype(np.float64), y.astype(np.float64)
                gap = np.abs(a - b)
                entry["max_abs"] = float(np.nanmax(gap, initial=0.0))
                entry["max_rel"] = float(np.nanmax(gap / np.maximum(np.abs(b), np.finfo(np.float64).tiny), initial=0.0))
                if not np.allclose(a, b, rtol=tolerance, atol=tolerance, equal_nan=True):
                    result["pass"] = False
            result["outputs"][name] = entry
        result["empty"] = all(x.size == 0 for x in got.values()) and all(y.size == 0 for y in want.values())
        return result


def _input_items(inputs: Path, size: object, cache: dict):  # noqa: ANN202
    """Return the input B items of one size: `inputs/<size>.npy`, INPUT_B_ITEMS different items."""
    if size not in cache:
        import numpy as np

        path = inputs / f"{size}.npy"
        if not path.is_file():
            raise BundleError(f"input B not found: {path.name} (write {INPUT_B_ITEMS} preprocessed images)")
        items = np.load(path, allow_pickle=False)
        if items.ndim < 1 or items.shape[0] != INPUT_B_ITEMS:
            raise BundleError(f"{path.name} must hold {INPUT_B_ITEMS} items, not shape {list(items.shape)}")
        if len(np.unique(items.reshape(INPUT_B_ITEMS, -1), axis=0)) != INPUT_B_ITEMS:
            raise BundleError(f"{path.name} holds one item more than once")
        cache[size] = items
    return cache[size]


def batch_check(
    fields: dict, out: Path, inputs: Path | None = None, root: Path = DEFAULT_ROOT, repo: Path = REPO_ROOT
) -> dict:
    """Run the batch-conversion check (V0 to V6) and write its files to `out`. Return the report."""
    import tempfile

    import numpy
    import onnx
    os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")  # ADR-BZ7X
    import onnxruntime

    from skellytracker.core.sessions.batch_conversion import model_batch_convert

    inputs = inputs or out / "inputs"
    # Remove the outputs of an earlier run first, so that a stop never leaves old evidence.
    out.mkdir(parents=True, exist_ok=True)
    for name in ("report.json", "differences.json", "conversion.yaml", "residual-diff.json"):
        (out / name).unlink(missing_ok=True)
    files: dict[tuple, Path] = {}
    names: dict[Path, str] = {}
    digests: dict[Path, str] = {}
    for item in fields.get("external") or []:
        key = (item["size"], item["precision"], item["batch"])
        if key in files:
            raise BundleError(f"two external files for size {key[0]}, precision {key[1]}, batch {key[2]}")
        if item["precision"] not in TOLERANCE:
            raise BundleError(f"precision {item['precision']} has no tolerance: use one of {list(TOLERANCE)}")
        path = (root.parent / item["path"]).resolve()
        if not path.is_file():
            raise BundleError(f"external file not found: {item['path']}")
        digests[path] = sha256(path.read_bytes())
        if item.get("sha256") not in (None, digests[path]):
            raise BundleError(f"external file does not match its sha256: {item['path']}")
        problems = onnx_problems(path)  # before any run (ADR-AD33, item 4)
        if problems:
            raise BundleError(f"batch does not run {item['path']}: " + "; ".join(problems))
        files[key], names[path] = path, item["path"]

    def clean(text: str) -> str:
        # Keep absolute paths out of the report: pack refuses them as private data.
        for path, name in names.items():
            text = text.replace(str(path), name)
        return text

    pairs = sorted({(s, p) for s, p, _ in files}, key=str)
    static = [k for k in files if k[2] != "dynamic"]

    # V0: applicability, for the whole family.
    missing = [
        [s, p, b] for s, p in pairs for b in VERIFICATION_BATCHES if (s, p, b) not in files
    ]
    # ADR-JB5J: a recorded batch_forced, or a dynamic-only family with no_static_reason, skips the check.
    # A b3-only or empty family is `to run`.
    if files and not static and fields.get("no_static_reason"):
        v0 = "not applicable"
    elif missing or not files:
        v0 = "not applicable" if fields.get("batch_forced") is not None else "missing-verification-batch"
    else:
        v0 = "pass"

    # V0b: can this environment load each file?
    v0b = {names[path]: problem for path in files.values() if (problem := _load_problem(path))}
    v0b = {name: clean(problem) for name, problem in v0b.items()}
    loadable = {path for path in files.values() if names[path] not in v0b}

    runner = _Runner()
    items: dict = {}
    reasons: list[str] = []
    empty: dict[tuple, list[bool]] = {pair: [] for pair in pairs}
    differences: dict = {}
    residuals: dict = {}
    tuples: list[dict] = []
    if v0 == "missing-verification-batch":
        reasons.append("missing-verification-batch")
    if v0b and v0 != "not applicable":
        reasons.append("host-runtime-cannot-load")

    with tempfile.TemporaryDirectory() as scratch:
        if v0 == "pass" and not v0b:
            for (size, precision), target in ((pair, n) for pair in pairs for n in TARGETS):
                source, native = files[(size, precision, SOURCE_BATCH)], files[(size, precision, target)]
                label = f"{size}/{precision}/b{SOURCE_BATCH}-to-b{target}"
                differences[label] = graph_diff(source, native)  # V1
                record: dict = {
                    "size": size, "precision": precision, "target": target,
                    "source": {"file": names[source], "sha256": digests[source]},
                    "native": {"file": names[native], "sha256": digests[native]},
                    "v1_counts": _diff_counts(differences[label]),
                }
                converted = Path(scratch) / f"{len(tuples)}.onnx"
                try:  # V3
                    # shortcut: the package converter still needs source_batch_size; drop it when M8 of
                    # specs/sidecar-implementation-plan.md changes the converter.
                    profile = {**PROFILE, "source_batch_size": SOURCE_BATCH}
                    summary = model_batch_convert(source, converted, target_batch=target, batch_conversion=profile)
                    record["v3"] = {"result": "pass", "summary": dataclasses.asdict(summary)}
                except Exception as exc:  # noqa: BLE001  # any refusal of the converter is a V3 failure
                    record["v3"] = {"result": "fail", "error": clean(str(exc))}
                    residuals[label] = {}
                    tuples.append(record)
                    continue
                residual = graph_diff(converted, native)  # V4
                record["v4_counts"] = _diff_counts(residual)
                tolerance = TOLERANCE[precision]
                batch_items = _input_items(inputs, size, items)
                try:  # V5: input A and input B on the native file
                    runs = {
                        "A": runner.input_a(native, target, batch_items.shape[1:]),
                        "B": runner.input_b(native, batch_items, target),
                    }
                    want = {k: runner.run(native, f) for k, f in runs.items()}
                except BundleError:
                    raise
                except Exception as exc:  # noqa: BLE001  # the native file does not run: not proof of a failure
                    record["v5"] = {"result": "to run", "error": clean(str(exc))}
                    reasons.append("host-runtime-cannot-load")
                    tuples.append(record)
                    continue
                record["v5"] = {}
                for k, f in runs.items():
                    try:
                        got = runner.run(converted, f)
                    except Exception as exc:  # noqa: BLE001  # a converted file that does not run fails V5
                        record["v5"][k] = {"pass": False, "outputs": {}, "empty": False, "error": clean(str(exc))}
                        continue
                    record["v5"][k] = runner.compare(got, want[k], tolerance)
                empty[(size, precision)] += [r["empty"] for r in record["v5"].values()]
                record["v5"]["result"] = "pass" if all(r["pass"] for r in record["v5"].values()) else "fail"
                if record["v5"]["result"] == "fail":
                    residuals[label] = residual
                tuples.append(record)

    # V6: the dynamic check. It gates only the publication of the dynamic file.
    dynamic_check = []
    for size, precision in pairs:
        path = files.get((size, precision, "dynamic"))
        if path is None:
            continue
        check: dict = {"size": size, "precision": precision, "file": names[path], "static": {}, "self": {}}
        dynamic_check.append(check)
        tolerance = TOLERANCE[precision]
        # (a) compares with each static file of the pair that exists at the batches 1, 2 and 3.
        need = {n: files[(size, precision, n)] for n in DYNAMIC_BATCHES if (size, precision, n) in files}
        if path not in loadable or any(n not in loadable for n in need.values()):
            check["result"], check["reason"] = "to run", "host-runtime-cannot-load"
            continue
        passed, compared = True, 0
        try:
            batch_items = _input_items(inputs, size, items)
            rest = batch_items.shape[1:]
            for n, native in need.items():  # (a) against the static natives
                for k, feeds in (
                    ("A", runner.input_a(native, n, rest)),
                    ("B", runner.input_b(native, batch_items, n)),
                ):
                    result = runner.compare(runner.run(path, feeds), runner.run(native, feeds), tolerance)
                    check["static"][f"b{n}/{k}"] = result
                    empty[(size, precision)].append(result["empty"])
                    compared += not result["empty"]
                    passed &= result["pass"]
            three = max(DYNAMIC_BATCHES)
            sliced = {i.name for i in runner.session(path).get_inputs() if runner.batched(i, three)}
            for k, feeds in (  # (b) self-consistency on three different items
                ("A", runner.input_a(path, three, rest)),
                ("B", runner.input_b(path, batch_items, three)),
            ):
                def part(start: int, stop: int, feeds: dict = feeds, sliced: set = sliced) -> dict:
                    return {i: v[start:stop] if i in sliced else v for i, v in feeds.items()}

                single = [runner.run(path, part(r, r + 1)) for r in range(three)]
                for n in DYNAMIC_BATCHES[1:]:
                    outputs = runner.run(path, part(0, n))
                    for name, value in outputs.items():
                        if value.ndim == 0 or value.shape[0] != n or any(s[name].shape[:1] != (1,) for s in single):
                            check["self"][f"b{n}/{k}/{name}"] = "no check"
                            continue
                        rows = [
                            runner.compare({name: value[r : r + 1]}, {name: single[r][name]}, tolerance)
                            for r in range(n)
                        ]
                        check["self"][f"b{n}/{k}/{name}"] = "pass" if all(r["pass"] for r in rows) else "fail"
                        empty[(size, precision)] += [r["empty"] for r in rows]
                        compared += not all(r["empty"] for r in rows)
                        passed &= all(r["pass"] for r in rows)
        except BundleError as exc:  # the tool cannot feed this file; it gates only the dynamic publication
            check["result"], check["reason"] = "to run", clean(str(exc))
            continue
        except Exception as exc:  # noqa: BLE001  # a dynamic file that does not run fails the check
            check["result"], check["error"] = "fail", clean(str(exc))
            continue
        if not passed:
            check["result"] = "fail"
        elif not compared:
            check["result"], check["reason"] = "to run", "no-signal"
        else:
            check["result"] = "pass"

    if v0 != "not applicable" and not reasons:
        reasons += ["no-signal" for pair, flags in empty.items() if flags and all(flags)][:1]
    if v0 == "not applicable":
        verdict, reason = "not applicable", None
    elif reasons:
        verdict, reason = "to run", reasons[0]
    elif any(t["v3"]["result"] == "fail" or t.get("v5", {}).get("result") == "fail" for t in tuples):
        verdict, reason = "does not convert", None
    else:
        verdict, reason = "converts", None

    commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    report = {
        "tool": "tools/intake_gate.py batch",
        "skellytracker_commit": commit,
        "versions": {
            "python": sys.version.split()[0],
            "numpy": numpy.__version__,
            "onnx": onnx.__version__,
            "onnxruntime": onnxruntime.__version__,
        },
        "profile_id": PROFILE["profile_id"],
        "S": SOURCE_BATCH,
        "v0": {"result": v0, "missing": missing if v0 != "not applicable" else []},
        "v0b": v0b,
        "tuples": tuples,
        "dynamic_check": dynamic_check,
        "batch_conversion": verdict,
        "batch_conversion_reason": reason,
    }
    def write(name: str, data: object) -> None:
        text = json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n"
        (out / name).write_bytes(text.encode("utf-8"))

    write("report.json", report)
    write("differences.json", differences)
    if verdict == "converts":
        write("conversion.yaml", {"batching": {"batch_conversion": PROFILE}})
    elif verdict == "does not convert":
        write("residual-diff.json", residuals)
    return report


def checkout_environment_problem(repo: Path = REPO_ROOT) -> str | None:
    """Return why `batch` must not run in this interpreter, or None.

    uv only warns about a wrong `--project` path and then runs in another environment.
    """
    if Path(sys.prefix).resolve() != (repo / ".venv").resolve():
        return f"batch runs only in the .venv of the checkout that holds this script ({repo.name}/.venv)"
    return None


# --------------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    # Each sub-command takes --root after its name, as the usage of the module docstring shows.
    root = argparse.ArgumentParser(add_help=False)
    root.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="the intakes folder")
    commands = parser.add_subparsers(dest="command", required=True)
    verify_parser = commands.add_parser(
        "verify", parents=[root], help="run the format checks and the package load checks of a bundle"
    )
    verify_parser.add_argument("bundle")
    batch_parser = commands.add_parser("batch", parents=[root], help="run the batch-conversion check")
    batch_parser.add_argument("--fields", type=Path, required=True, help="a fields file or a manifest")
    batch_parser.add_argument("--out", type=Path, required=True, help="the batch/ folder to write")
    batch_parser.add_argument("--inputs", type=Path, help="the folder of input B (default: OUT/inputs)")
    args = parser.parse_args(argv)
    try:
        if args.command == "batch":
            problem = checkout_environment_problem()
            if problem:
                raise BundleError(problem)
            fields = json.loads(args.fields.read_text(encoding="utf-8"))
            report = batch_check(fields, args.out, args.inputs, args.root)
            print(f"batch_conversion: {report['batch_conversion']}")
            print(f"batch_conversion_reason: {report['batch_conversion_reason']}")
            for check in report["dynamic_check"]:
                print(f"dynamic check {check['size']} {check['precision']}: {check['result']}")
        else:
            findings = verify(args.bundle, args.root)
            print("findings:")
            for finding in findings:
                print(f"  - {json.dumps(finding, ensure_ascii=False)}")
            return 1 if findings else 0
    except BundleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
