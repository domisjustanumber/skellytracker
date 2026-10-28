"""The hand-over tool `tools/intake_bundle.py` packs, lists and verifies bundles."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import intake_bundle as ib
import numpy as np
import pytest
import yaml

REPO_ROOT = Path(ib.__file__).resolve().parents[1]
HEAD = subprocess.run(  # noqa: S603
    ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],  # noqa: S607
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()
SOURCE = "a" * 40


def proposal_fields(name: str = "box-clamp", contributor: str = "ultralytics-exporter", **extra) -> dict:
    return {
        "bundle_format": 1,
        "kind": "proposal",
        "name": name,
        "contributor": contributor,
        "source_commit": SOURCE,
        "spec_commit": HEAD,
        "sections": ["post.det.selection.nms"],
        "change_class": "vnext",
        "base": None,
        "depends_on": [],
        "contributes_to": None,
        "related": [],
        "external": [],
        **extra,
    }


def model_fields(**extra) -> dict:
    return {
        "bundle_format": 1,
        "kind": "model",
        "name": "yolo26",
        "contributor": "ultralytics-exporter",
        "source_commit": SOURCE,
        "spec_commit": HEAD,
        "sections": ["post.det.selection.nms"],
        "related": [],
        "verdict": "describes",
        "batch_conversion": "not applicable",
        "batch_conversion_reason": None,
        "external": [],
        **extra,
    }


def payload(tmp_path: Path, files: dict[str, str | bytes]) -> Path:
    source = tmp_path / "payload"
    for rel, data in files.items():
        path = source / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return source


def respond(root: Path, bundle: str, number: int, **fields) -> None:
    response = {
        "answers_version": 1,
        "date": "2026-10-28",
        "state": "recorded",
        "findings": [],
        "batch_conversion": None,
        "waiting_on": [],
        "records": [],
        "decision": None,
        "subject": None,
        "changes": [],
        **fields,
    }
    folder = root / bundle / "responses"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"r{number}.yaml").write_text(json.dumps(response), encoding="utf-8")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "intakes"


def test_pack_writes_lf_text_hashes_and_a_yaml_readable_manifest(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "﻿line 1\r\nline 2\r\n", "data.npy": b"\x93NUMPY\0\r\n"})
    version_dir = ib.pack(source, proposal_fields(), root, cwd=tmp_path, today="2026-10-28")
    assert version_dir == root / "proposal-box-clamp@ultralytics-exporter" / "v1"
    assert (version_dir / "proposal.md").read_bytes() == b"line 1\nline 2\n"
    assert (version_dir / "data.npy").read_bytes() == b"\x93NUMPY\0\r\n"
    manifest = yaml.safe_load((version_dir / "manifest.yaml").read_text(encoding="utf-8"))
    assert manifest == json.loads((version_dir / "manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["version"] == 1
    assert manifest["created"] == "2026-10-28"
    assert {f["path"]: f["bytes"] for f in manifest["files"]} == {"data.npy": 9, "proposal.md": 14}
    assert ib.manifest_problems(manifest) == []
    again = ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    assert again.name == "v2"


def test_pack_adds_the_sha256_of_an_external_file(tmp_path: Path) -> None:
    root = tmp_path / "freemocap" / "skellytracker" / "intakes"
    model = tmp_path / "Exporter" / "m_b3_fp32.onnx"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"onnx")
    item = {"path": "../../Exporter/m_b3_fp32.onnx", "role": "artifact", "size": "n", "batch": 3,
            "precision": "fp32", "published": True}
    source = payload(tmp_path, {"intake.md": "intake\n"})
    version_dir = ib.pack(source, model_fields(external=[item]), root, cwd=tmp_path)
    manifest = ib.read_manifest(version_dir)
    assert manifest["external"][0]["sha256"] == ib.sha256(b"onnx")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"change_class": "minor"}, "change_class"),
        ({"version": 3}, "unknown key version"),
        ({"spec_commit": "abc"}, "spec_commit"),
        ({"contributor": "Ultralytics-Exporter"}, "contributor"),
    ],
)
def test_pack_refuses_a_bad_fields_file(tmp_path: Path, root: Path, change: dict, message: str) -> None:
    source = payload(tmp_path, {"proposal.md": "text\n"})
    with pytest.raises(ib.BundleError, match=message):
        ib.pack(source, proposal_fields(**change), root, cwd=tmp_path)
    assert not root.exists()


def test_pack_needs_a_reason_only_for_a_batch_check_to_run(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"intake.md": "text\n"})
    with pytest.raises(ib.BundleError, match="batch_conversion_reason"):
        ib.pack(source, model_fields(batch_conversion="to run"), root, cwd=tmp_path)
    with pytest.raises(ib.BundleError, match="batch_conversion_reason"):
        ib.pack(source, model_fields(batch_conversion_reason="no-signal"), root, cwd=tmp_path)
    ib.pack(source, model_fields(batch_conversion="to run", batch_conversion_reason="no-signal"), root, cwd=tmp_path)


def test_pack_stops_on_private_data(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "see /ho" + "me/someone/repo\n"})
    with pytest.raises(ib.BundleError, match="private data"):
        ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    assert not root.exists()


def test_list_gives_states_owners_reverse_links_and_can_delete(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "text\n"})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    ib.pack(source, proposal_fields(contributor="roboflow-exporter", base="proposal-box-clamp@ultralytics-exporter"), root, cwd=tmp_path)
    ib.pack(source, proposal_fields(name="old", contributor="roboflow-exporter"), root, cwd=tmp_path)
    (root / "proposal-draft@roboflow-exporter" / "v1").mkdir(parents=True)
    respond(root, "proposal-box-clamp@ultralytics-exporter", 1)
    respond(root, "proposal-old@roboflow-exporter", 1, state="closed")
    respond(root, "proposal-old@roboflow-exporter", 2, state="closed", findings=["deferred: wait for the release"])
    lines = ib.list_lines(root)
    assert "proposal-box-clamp@ultralytics-exporter v1 recorded" in lines
    assert "  needed by: proposal-box-clamp@roboflow-exporter" in lines
    assert "proposal-old@roboflow-exporter v1 closed (can delete)" in lines
    assert "  deferred: wait for the release" in lines
    assert "proposal-draft@roboflow-exporter - in progress" in lines
    assert lines[-1] == "  post.det.selection.nms: ultralytics-exporter"


def test_a_good_bundle_verifies(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "See [the spec](../../README.md).\n"})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    assert ib.verify("proposal-box-clamp@ultralytics-exporter", root) == []


def test_verify_finds_changed_bytes_text_form_plans_links_and_size(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {
        "proposal.md": "text\n",
        "notes.md": "From plans/x.md. See [gone](../../no-such-file.md).\n",
        "vectors/post.det.selection.nms.yaml": "cases: []\n" + "#" * ib.VECTOR_LIMIT,
    })
    version_dir = ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    (version_dir / "proposal.md").write_bytes(b"text\r\n")
    findings = ib.verify("proposal-box-clamp@ultralytics-exporter", root)
    assert "proposal.md: the hash or the size does not match the manifest" in findings
    assert "proposal.md: a text file must be UTF-8 with no BOM and LF line ends" in findings
    assert "notes.md:1: cites a plans/ path" in findings
    assert any("the link ../../no-such-file.md does not resolve" in f for f in findings)
    assert "vectors/post.det.selection.nms.yaml: a vector file must be 256 KiB or smaller" in findings


def test_verify_finds_an_unknown_spec_commit(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "text\n"})
    ib.pack(source, proposal_fields(spec_commit="0" * 40), root, cwd=tmp_path)
    findings = ib.verify("proposal-box-clamp@ultralytics-exporter", root)
    assert findings == ["spec_commit not found in this checkout; pack again on the current checkout"]


def test_verify_checks_the_owner_and_the_contribution_cases(tmp_path: Path, root: Path) -> None:
    owner_case = "cases:\n  - {id: one, input: 1, expect: 2}\n"
    owner = payload(tmp_path / "o", {"proposal.md": "text\n", "vectors/post.det.selection.nms.yaml": owner_case})
    ib.pack(owner, proposal_fields(), root, cwd=tmp_path)
    respond(root, "proposal-box-clamp@ultralytics-exporter", 1)
    rival = payload(tmp_path / "r", {"proposal.md": "text\n"})
    ib.pack(rival, proposal_fields(name="other-clamp", contributor="roboflow-exporter"), root, cwd=tmp_path)
    findings = ib.verify("proposal-other-clamp@roboflow-exporter", root)
    assert findings == [
        "the section post.det.selection.nms has the owner ultralytics-exporter: "
        "send a contribution or a follow-up"
    ]
    other_case = "cases:\n  - {id: one, input: 1, expect: 3}\n  - {id: two, input: 2, expect: 4}\n"
    contribution = payload(tmp_path / "c", {"evidence.md": "text\n", "vectors/post.det.selection.nms.yaml": other_case})
    ib.pack(contribution, proposal_fields(contributor="openmmlab-exporter", contributes_to="box-clamp"), root, cwd=tmp_path)
    findings = ib.verify("proposal-box-clamp@openmmlab-exporter", root)
    assert findings == [
        "vectors/post.det.selection.nms.yaml: the case one differs from the owner case with the same id"
    ]


def test_verify_checks_the_model_payload_schemas(tmp_path: Path, root: Path) -> None:
    runs = {"exporter": "Ultralytics-Exporter", "commit": SOURCE, "runs": [
        {"section": "post.det.selection.nms", "function": "a.py::f", "vectors_sha256": "b" * 64,
         "cases": {"one": "pass"}, "result": "maybe"}]}
    provenance = {"examples": {"detectors/x.yaml": {"exporter": "E", "kind": "export"}}}
    source = payload(tmp_path, {
        "intake.md": "text\n",
        "vector-runs.yaml": json.dumps(runs),
        "example/provenance.yaml": json.dumps(provenance),
    })
    ib.pack(source, model_fields(), root, cwd=tmp_path)
    findings = ib.verify("model-yolo26@ultralytics-exporter", root)
    assert findings[0] == "vector-runs.yaml runs[1].result must be pass, fail or no vectors"
    assert findings[1].startswith("example/provenance.yaml examples[detectors/x.yaml] must have the keys")
    assert len(findings) == 2


def test_responses_are_json_that_yaml_also_reads(tmp_path: Path, root: Path) -> None:
    respond(root, "proposal-box-clamp@ultralytics-exporter", 1, state="rejected", resolution={"reason": "no"})
    text = (root / "proposal-box-clamp@ultralytics-exporter" / "responses" / "r1.yaml").read_text(encoding="utf-8")
    assert yaml.safe_load(text) == json.loads(text)
    assert ib.response_problems(json.loads(text)) == []
    bad = {**json.loads(text), "state": "resolved-otherwise", "decision": "ADR-AB79"}
    problems = ib.response_problems(bad)
    assert "decision must be the bare ID, with no ADR- prefix" in problems
    assert "resolution needs the key goals" in problems


def test_each_sub_command_takes_root_after_its_name(root: Path, capsys: pytest.CaptureFixture) -> None:
    assert ib.main(["list", "--root", str(root)]) == 0
    assert capsys.readouterr().out == "no bundles\n"


# --------------------------------------------------------------------------------------------
# batch: the batch-conversion check. The graph builder copies the reshape model of
# skellytracker/tests/test_batch_conversion.py and adds a bias, a dynamic form and an empty form.
# --------------------------------------------------------------------------------------------

ITEMS = np.arange(12, dtype=np.float32).reshape(4, 3)


def onnx_file(
    path: Path, batch: int | str, *, bias: float = 0.0, empty: bool = False, ir_version: int | None = None
) -> Path:
    """x[N, 3] -> Reshape([N, 3]) -> Add(bias) -> y[N, 3], or y[N, 0] with `empty`."""
    onnx = pytest.importorskip("onnx")
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
                "precision": "fp32", "published": batch == ib.SOURCE_BATCH,
            })
        if items is not None:
            (out / "inputs").mkdir(parents=True, exist_ok=True)
            np.save(out / "inputs" / "n.npy", items)
        return root, model_fields(external=external), out

    return make


def test_batch_converts_down_and_up_and_writes_the_fragment(family) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, 2: {}, 3: {}, 4: {}})
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("converts", None)
    assert [t["target"] for t in report["tuples"]] == [1, 2, 4]
    upward = report["tuples"][2]
    assert upward["v3"]["result"] == "pass"
    assert upward["v5"]["result"] == "pass"
    assert upward["v5"]["B"]["outputs"]["y"]["rows"] == 4
    assert yaml.safe_load((out / "conversion.yaml").read_text(encoding="utf-8")) == {
        "batching": {"batch_conversion": {"profile_id": "static-batch-v1", "source_batch_size": 3}}
    }
    assert json.loads((out / "report.json").read_text(encoding="utf-8")) == json.loads(json.dumps(report))
    assert not (out / "residual-diff.json").exists()


def test_batch_does_not_convert_a_batch_dependent_export(family) -> None:  # noqa: ANN001
    batches = {1: {"bias": 1.0}, 2: {"bias": 1.0}, 3: {}, 4: {"bias": 1.0}, "dynamic": {"bias": 1.0}}
    root, fields, out = family(batches)
    report = ib.batch_check(fields, out, root=root)
    assert report["batch_conversion"] == "does not convert"
    assert {t["v5"]["result"] for t in report["tuples"]} == {"fail"}
    assert (out / "residual-diff.json").is_file()
    assert not (out / "conversion.yaml").exists()
    dynamic = report["dynamic_check"][0]
    assert dynamic["result"] == "fail"
    assert dynamic["static"]["b3/A"]["pass"] is False


@pytest.mark.parametrize("gone", [3, 4])
def test_batch_needs_each_verification_batch(family, gone: int) -> None:  # noqa: ANN001
    root, fields, out = family({b: {} for b in (1, 2, 3, 4) if b != gone})
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "missing-verification-batch")
    assert report["v0"]["missing"] == [["n", "fp32", gone]]
    assert report["tuples"] == []


def test_batch_gives_to_run_when_the_runtime_cannot_load_a_file(family) -> None:  # noqa: ANN001
    onnx = pytest.importorskip("onnx")
    root, fields, out = family({1: {}, 2: {"ir_version": onnx.IR_VERSION + 1}, 3: {}, 4: {}})
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "host-runtime-cannot-load")
    assert list(report["v0b"]) == ["../../Exporter/m_b2_fp32.onnx"]


def test_batch_gives_no_signal_when_every_output_is_empty(family) -> None:  # noqa: ANN001
    root, fields, out = family({b: {"empty": True} for b in (1, 2, 3, 4)})
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "no-signal")


def test_batch_checks_a_dynamic_export_against_itself(family) -> None:  # noqa: ANN001
    root, fields, out = family({"dynamic": {}})
    report = ib.batch_check(fields, out, root=root)
    assert report["batch_conversion"] == "not applicable"
    check = report["dynamic_check"][0]
    assert check["result"] == "pass"
    assert check["static"] == {}
    assert check["self"] == {"b2/A/y": "pass", "b3/A/y": "pass", "b2/B/y": "pass", "b3/B/y": "pass"}


@pytest.mark.parametrize(
    ("items", "message"),
    [(ITEMS[:3], "must hold 4 items"), (np.stack([ITEMS[0]] * 4), "more than once"), (None, "input B not found")],
)
def test_batch_needs_input_b_with_four_different_items(family, items, message: str) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, 2: {}, 3: {}, 4: {}}, items=items)
    with pytest.raises(ib.BundleError, match=message):
        ib.batch_check(fields, out, root=root)


def test_batch_runs_only_in_the_venv_of_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(ib.sys, "prefix", str(tmp_path))
    assert ib.main(["batch", "--fields", str(tmp_path / "f.json"), "--out", str(tmp_path / "batch")]) == 1
    assert "batch runs only in the .venv of the checkout" in capsys.readouterr().err


def converts_bundle(tmp_path: Path, published: tuple, sidecar_source: int | None, conversion: bool) -> Path:
    """Pack a `converts` model bundle with b1 to b4 and return its intakes folder."""
    root = tmp_path / "freemocap" / "skellytracker" / "intakes"
    external = []
    for batch in (1, 2, 3, 4):
        model = tmp_path / "Exporter" / f"m_b{batch}_fp32.onnx"
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_bytes(b"onnx")
        external.append({
            "path": f"../../Exporter/{model.name}", "role": "artifact", "size": "n", "batch": batch,
            "precision": "fp32", "published": batch in published,
        })
    entry = {
        "exporter": "E", "exporter_path": "x.yaml", "kind": "export", "exporter_layout_path": "x.yaml",
        "tracked": True, "commit": SOURCE, "source": {"package": "e", "version": "0.1.0"},
    }
    batching: dict = {"batch_axis": 0}
    if sidecar_source:
        batching["batch_conversion"] = {"profile_id": "static-batch-v1", "source_batch_size": sidecar_source}
    files = {
        "intake.md": "text\n",
        "example/provenance.yaml": json.dumps({"examples": {"detectors/x.yaml": entry}}),
        "example/detectors/x.yaml": json.dumps({"batching": batching}),
    }
    if conversion:
        files["batch/conversion.yaml"] = json.dumps({"batching": {"batch_conversion": ib.PROFILE}})
    fields = model_fields(batch_conversion="converts", external=external)
    ib.pack(payload(tmp_path, files), fields, root, cwd=tmp_path)
    return root


SIDECAR_FINDING = (
    "publish rule: example/detectors/x.yaml must have batching.batch_conversion.source_batch_size: 3 "
    "if and only if the published batch is 3"
)


def test_verify_passes_a_b3_publish(tmp_path: Path) -> None:
    root = converts_bundle(tmp_path, (3,), 3, conversion=True)
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == []


def test_verify_checks_the_publish_rule(tmp_path: Path) -> None:
    root = converts_bundle(tmp_path, (1, 3), 3, conversion=False)
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == [
        "publish rule: n fp32 must have exactly one published file, not 2",
        "publish rule: each published file must have the batch 3, or each one dynamic, not ['1', '3']",
        SIDECAR_FINDING,
    ]
    root = converts_bundle(tmp_path / "b", (3,), None, conversion=False)
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == [
        SIDECAR_FINDING,
        "publish rule: batch/conversion.yaml must have source_batch_size: 3",
    ]


def test_verify_finds_a_published_dynamic_export_that_failed_the_dynamic_check(tmp_path: Path) -> None:
    root = tmp_path / "freemocap" / "skellytracker" / "intakes"
    model = tmp_path / "Exporter" / "m_fp32.onnx"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"onnx")
    item = {
        "path": "../../Exporter/m_fp32.onnx", "role": "artifact", "size": "n", "batch": "dynamic",
        "precision": "fp32", "published": True,
    }
    report = {"dynamic_check": [{"size": "n", "precision": "fp32", "result": "fail"}]}
    source = payload(tmp_path, {"intake.md": "text\n", "batch/report.json": json.dumps(report)})
    ib.pack(source, model_fields(external=[item]), root, cwd=tmp_path)
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == [
        "n fp32: do not publish the dynamic export; publish b3 or fix the export"
    ]
