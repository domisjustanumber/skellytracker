"""The hand-over tool `tools/intake_bundle.py` packs, lists and verifies bundles."""

from __future__ import annotations

import json
import re
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
        "batch_forced": "dynamic",
        "batch_forced_reason": "the exporter makes only a dynamic export",
        "no_static_reason": None,
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


@pytest.fixture(autouse=True)
def no_tracked_owners(monkeypatch: pytest.MonkeyPatch) -> None:
    """The tracked records of this repo own real sections, which the test bundles also use.

    So the owner checks of `list` and `verify` see no tracked record of this repo. A test that
    gives a fake repo still gets the owners of its records.
    """
    real = ib.owners
    monkeypatch.setattr(ib, "owners", lambda found, repo=None: real(found, None if repo == ib.REPO_ROOT else repo))


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
    assert manifest["spec_version"] == ib.spec_version()
    assert ib.manifest_problems(manifest) == []
    again = ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    assert again.name == "v2"
    assert ib.read_manifest(again)["created"] == "2026-10-28"  # the created of version 1 (ADR-ZXD7)


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
        ({"change_class": "vnext"}, "unknown key change_class"),  # ADR-NB5F
        ({"version": 3}, "unknown key version"),
        ({"spec_version": "2.0.0"}, "unknown key spec_version"),  # pack writes it (ADR-ZXD7)
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
        "notes.md": "From plans/x.md.\n",
        "vectors/post.det.selection.nms.yaml": "cases: []\n" + "#" * ib.VECTOR_LIMIT,
    })
    version_dir = ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    (version_dir / "proposal.md").write_bytes(b"text\r\n")
    (version_dir / "notes.md").write_bytes(b"From plans/x.md. See [gone](../../no-such-file.md).\n")
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


def test_verify_finds_a_file_that_proposal_md_names_and_the_bundle_lacks(tmp_path: Path, root: Path) -> None:
    text = (
        "Code: `reference/post_det_selection_nms.py`.\n"
        "Target: `specs/model-sidecar/reference/x.py`, `vectors/<section ID>.yaml`.\n"
    )
    source = payload(tmp_path, {"proposal.md": text})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    findings = ib.verify("proposal-box-clamp@ultralytics-exporter", root)
    assert findings == ["reference/post_det_selection_nms.py: proposal.md names this file, but the bundle does not have it"]


NMS_VECTORS = REPO_ROOT / "specs" / "model-sidecar" / "vectors" / "post.det.selection.nms.yaml"


def nms_vectors(*cases: dict) -> str:
    """The landed nms vector file with `cases` in place of its cases."""
    data = yaml.safe_load(NMS_VECTORS.read_text(encoding="utf-8"))
    return yaml.safe_dump({**data, "cases": list(cases)}, sort_keys=False)


def nms_case(number: int, **changes) -> dict:
    case = yaml.safe_load(NMS_VECTORS.read_text(encoding="utf-8"))["cases"][number]
    return {**case, **changes}


def test_verify_checks_the_form_of_each_bundle_vector_file(tmp_path: Path, root: Path) -> None:
    rel = "vectors/post.det.selection.nms.yaml"
    good = payload(tmp_path / "g", {"proposal.md": "text\n", rel: nms_vectors(nms_case(0))})
    ib.pack(good, proposal_fields(), root, cwd=tmp_path)
    assert ib.verify("proposal-box-clamp@ultralytics-exporter", root) == []
    shared = nms_case(0)
    shared["input"] = {**shared["input"], "iou_threshold": 0.5}
    bad = payload(tmp_path / "b", {"proposal.md": "text\n", rel: nms_vectors(shared)})
    ib.pack(bad, proposal_fields(name="bad"), root, cwd=tmp_path)
    assert ib.verify("proposal-bad@ultralytics-exporter", root) == [
        f"{rel}: suppress-overlap-and-threshold: params and input share the keys ['iou_threshold']"
    ]


def test_verify_runs_the_bundle_reference_and_the_rules_of_part_2_4(tmp_path: Path, root: Path) -> None:
    rel = "vectors/post.det.clamp.yaml"
    vectors = {
        "section": "post.det.clamp",
        "tolerance": 0,
        "unverified": "only the proposal text",
        "cases": [
            {"id": "a", "params": {}, "input": {"x": 1}, "expect": {"y": 1}},
            {"id": "b", "function": "other", "params": {}, "input": {"x": 1}, "expect": {"y": 1}},
            {"id": "c", "checks": ["refused"], "params": {}, "input": {"x": -1},
             "expect": {"error": "V-post.det.clamp-1"}},
            {"id": "d", "checks": ["refused"], "params": {}, "input": {"x": -2},
             "expect": {"error": "V-post.det.clamp-2"}},
        ],
    }
    source = payload(tmp_path, {
        "proposal.md": "### 2.4 Validation rules\n\n- [ ] `V-post.det.clamp-1`: x must be 0 or more.\n",
        "reference/post_det_clamp.py": "def run(params, input):\n    return {'y': input['x']}\n",
        rel: json.dumps(vectors),
    })
    ib.pack(source, proposal_fields(sections=["post.det.clamp"]), root, cwd=tmp_path)
    assert ib.verify("proposal-box-clamp@ultralytics-exporter", root) == [
        f"{rel}: b: no function other in post_det_clamp",
        f"{rel}: d: V-post.det.clamp-2 is not a defined rule ID",
    ]


def test_verify_checks_the_owner_and_the_contribution_cases(tmp_path: Path, root: Path) -> None:
    owner_case = nms_vectors(nms_case(0, id="one"), nms_case(1, id="three"))
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
    beyond = nms_case(0, id="one")
    beyond["expect"] = {**beyond["expect"], "scores": [0.9, 0.7001]}
    other_params = nms_case(1, id="three")  # the same expect, other params
    other_params["params"] = {**other_params["params"], "iou_threshold": 0.4}
    other_case = nms_vectors(beyond, nms_case(2, id="two"), other_params)
    contribution = payload(tmp_path / "c", {"evidence.md": "text\n", "vectors/post.det.selection.nms.yaml": other_case})
    ib.pack(contribution, proposal_fields(contributor="openmmlab-exporter", contributes_to="box-clamp"), root, cwd=tmp_path)
    findings = ib.verify("proposal-box-clamp@openmmlab-exporter", root)
    assert findings == [
        "vectors/post.det.selection.nms.yaml: the case one differs from the owner case with the same id",
        "vectors/post.det.selection.nms.yaml: the case three differs from the owner case with the same id",
    ]


def test_a_contribution_uses_the_reference_and_the_part_2_4_rules_of_its_owner(tmp_path: Path, root: Path) -> None:
    rel = "vectors/post.det.clamp.yaml"

    def vectors(*cases: dict) -> str:
        return json.dumps({"section": "post.det.clamp", "tolerance": 0, "unverified": "the proposal text", "cases": list(cases)})

    owner = payload(tmp_path / "o", {
        "proposal.md": "### 2.4 Validation rules\n\n- [ ] `V-post.det.clamp-1`: x must be 0 or more.\n",
        "reference/post_det_clamp.py": "def run(params, input):\n    return {'y': input['x']}\n",
        rel: vectors({"id": "a", "params": {}, "input": {"x": 1}, "expect": {"y": 1}}),
    })
    ib.pack(owner, proposal_fields(sections=["post.det.clamp"]), root, cwd=tmp_path)
    contribution = payload(tmp_path / "c", {"evidence.md": "text\n", rel: vectors(
        {"id": "b", "params": {}, "input": {"x": 2}, "expect": {"y": 2}},
        {"id": "c", "checks": ["refused"], "params": {}, "input": {"x": -1}, "expect": {"error": "V-post.det.clamp-1"}},
    )})
    ib.pack(contribution, proposal_fields(sections=["post.det.clamp"], contributor="openmmlab-exporter",
                                          contributes_to="box-clamp"), root, cwd=tmp_path)
    assert ib.verify("proposal-box-clamp@openmmlab-exporter", root) == []


def test_a_contribution_case_within_the_tolerance_or_with_its_own_verified_against_is_equal(
    tmp_path: Path, root: Path
) -> None:
    owner = payload(tmp_path / "o", {"proposal.md": "text\n", "vectors/post.det.selection.nms.yaml": nms_vectors(nms_case(0))})
    ib.pack(owner, proposal_fields(), root, cwd=tmp_path)
    within = nms_case(0, verified_against=[{"OpenMMLab-Exporter": "ref/nms.py::run"}])
    within["expect"] = {**within["expect"], "scores": [0.900004, 0.7]}  # tolerance 0.00001
    landed = nms_case(1, verified_against=[{"OpenMMLab-Exporter": "ref/nms.py::run"}])  # the landed case
    contribution = payload(tmp_path / "c", {
        "evidence.md": "text\n", "vectors/post.det.selection.nms.yaml": nms_vectors(within, landed),
    })
    ib.pack(contribution, proposal_fields(contributor="openmmlab-exporter", contributes_to="box-clamp"), root, cwd=tmp_path)
    assert ib.verify("proposal-box-clamp@openmmlab-exporter", root) == []


def test_verify_checks_the_model_payload_schemas(tmp_path: Path, root: Path) -> None:
    landed = (REPO_ROOT / "specs" / "model-sidecar" / "vectors" / "post.det.selection.nms.yaml").read_bytes()
    runs = {"exporter": "Ultralytics-Exporter", "commit": SOURCE, "runs": [
        {"section": "post.det.selection.nms", "function": "a.py::f", "vectors_sha256": ib.sha256(landed),
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


def test_verify_finds_a_stale_vector_run_and_unreadable_payload_files(tmp_path: Path, root: Path) -> None:
    runs = {"exporter": "E", "commit": SOURCE, "runs": [
        {"section": "post.det.selection.nms", "function": "a.py::f", "vectors_sha256": "b" * 64,
         "cases": [], "result": "pass"}]}
    source = payload(tmp_path, {
        "intake.md": "text\n",
        "vector-runs.yaml": json.dumps(runs),
        "example/provenance.yaml": "examples: [unclosed\n",
        "batch/report.json": "{not json",
    })
    item = {"path": "../../Exporter/m.onnx", "role": "artifact", "size": "n", "batch": "dynamic",
            "precision": "fp32", "published": True}
    model = tmp_path / "Exporter" / "m.onnx"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"x")
    intakes = tmp_path / "freemocap" / "skellytracker" / "intakes"
    ib.pack(source, model_fields(external=[item]), intakes, cwd=tmp_path)
    findings = ib.verify("model-yolo26@ultralytics-exporter", intakes)
    assert "vector-runs.yaml runs[1].cases must be a mapping" in findings
    assert any("vectors_sha256 is not the hash of the landed vector file" in f for f in findings)
    assert "example/provenance.yaml: not valid YAML/JSON" in findings
    assert "batch/report.json: not valid YAML/JSON" in findings


def test_a_bad_manifest_does_not_stop_list_or_verify(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "text\n"})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    for name, text in (("bad", '{"kind": "model",'), ("list", "[1]")):
        version_dir = ib.pack(source, proposal_fields(name=name), root, cwd=tmp_path)
        (version_dir / "manifest.yaml").write_text(text, encoding="utf-8")
    lines = ib.list_lines(root)
    assert "proposal-bad@ultralytics-exporter v1 unreadable manifest" in lines
    assert "proposal-list@ultralytics-exporter v1 unreadable manifest" in lines
    assert "proposal-box-clamp@ultralytics-exporter v1 submitted" in lines
    assert ib.verify("proposal-bad@ultralytics-exporter", root) == [
        "manifest: v1/manifest.yaml is not a JSON mapping"
    ]
    assert ib.manifest_problems([1]) == ["the manifest is not a mapping"]


@pytest.mark.parametrize(
    ("files", "message"),
    [({"proposal.md": b"a\rb\n"}, "lone CR"), ({"proposal.md": b"x\n", "m.onnx": b"x"}, "do not copy ONNX")],
)
def test_pack_refuses_a_lone_cr_and_an_onnx_file(tmp_path: Path, root: Path, files: dict, message: str) -> None:
    with pytest.raises(ib.BundleError, match=message):
        ib.pack(payload(tmp_path, files), proposal_fields(), root, cwd=tmp_path)
    assert not root.exists()


def test_pack_and_verify_check_the_anchor_of_each_link(tmp_path: Path, root: Path) -> None:
    good = (
        "# Gap\n\nSee [the gap](#gap), [the map](../../README.md#section-map) and [notes](notes.md#notes).\n\n"
        "```markdown\n[Proposed heading](#not-yet)\n```\n"
    )
    bad = "See [new](#no-such-heading) and [new](../../common/identity.md#no-such-heading).\n"
    with pytest.raises(ib.BundleError) as refused:
        ib.pack(payload(tmp_path, {"proposal.md": good + bad, "notes.md": "# Notes\n"}), proposal_fields(), root, cwd=tmp_path)
    assert str(refused.value).count("names a heading that does not exist") == 2
    version_dir = ib.pack(
        payload(tmp_path / "ok", {"proposal.md": good, "notes.md": "# Notes\n"}), proposal_fields(), root, cwd=tmp_path
    )
    assert not [f for f in ib.verify("proposal-box-clamp@ultralytics-exporter", root) if "link" in f]
    (version_dir / "proposal.md").write_bytes((good + bad).encode("utf-8"))
    findings = ib.verify("proposal-box-clamp@ultralytics-exporter", root)
    assert "proposal.md:8: the link #no-such-heading names a heading that does not exist" in findings
    assert any("../../common/identity.md#no-such-heading names a heading" in f for f in findings)


@pytest.mark.parametrize("rel", ["reference/__pycache__/m.cpython-314.pyc", "reference/m.pyc", "m.pyo"])
def test_pack_and_verify_refuse_a_compiled_file(tmp_path: Path, root: Path, rel: str) -> None:
    message = f"{rel}: do not put compiled files in a bundle; run Python with -B"
    with pytest.raises(ib.BundleError, match=re.escape(message)):
        ib.pack(payload(tmp_path, {"proposal.md": b"x\n", rel: b"\x00"}), proposal_fields(), root, cwd=tmp_path)
    # A version that lists the file, as an older pack wrote it.
    version_dir = ib.pack(payload(tmp_path / "ok", {"proposal.md": b"x\n"}), proposal_fields(), root, cwd=tmp_path)
    (version_dir / rel).parent.mkdir(parents=True, exist_ok=True)
    (version_dir / rel).write_bytes(b"\x00")
    manifest = json.loads((version_dir / "manifest.yaml").read_text(encoding="utf-8"))
    manifest["files"].append({"path": rel, "sha256": ib.sha256(b"\x00"), "bytes": 1})
    (version_dir / "manifest.yaml").write_text(json.dumps(manifest), encoding="utf-8")
    assert message in ib.verify("proposal-box-clamp@ultralytics-exporter", root)


@pytest.mark.parametrize("path", ["C:/Windows/win.ini", "C:x"])
def test_a_manifest_file_path_must_not_be_a_drive_path(path: str) -> None:
    manifest = {**proposal_fields(), "version": 1, "created": "2026-10-29",
                "files": [{"path": path, "sha256": "a" * 64, "bytes": 1}]}
    assert "files[1].path must be relative, with '/' and no '..'" in ib.manifest_problems(manifest)


def test_external_paths_take_a_sibling_layout_and_stay_outside_the_repo(tmp_path: Path) -> None:
    root = tmp_path / "skellytracker" / "intakes"
    model = tmp_path / "Exporter" / "m.onnx"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"onnx")
    item = {"path": "../Exporter/m.onnx", "role": "artifact", "size": "n", "batch": 3,
            "precision": "fp32", "published": True}
    source = payload(tmp_path, {"intake.md": "intake\n"})
    ib.pack(source, model_fields(external=[item]), root, cwd=tmp_path)
    inside = tmp_path / "skellytracker" / "m.onnx"
    inside.write_bytes(b"onnx")
    with pytest.raises(ib.BundleError, match="outside the skellytracker repo"):
        ib.pack(source, model_fields(external=[{**item, "path": "../skellytracker/m.onnx"}]), root, cwd=tmp_path)


def test_pack_refuses_a_new_version_of_a_finished_proposal_but_not_of_a_model(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "text\n", "intake.md": "text\n"})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    respond(root, "proposal-box-clamp@ultralytics-exporter", 1, state="accepted")
    respond(root, "proposal-box-clamp@ultralytics-exporter", 2, state="needs-contributor")
    with pytest.raises(ib.BundleError, match="is accepted: write a new bundle with a new slug"):
        ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    ib.pack(source, model_fields(), root, cwd=tmp_path)
    respond(root, "model-yolo26@ultralytics-exporter", 1, state="landed")
    assert ib.pack(source, model_fields(), root, cwd=tmp_path).name == "v2"


def test_list_marks_new_versions_sections_and_keeps_sibling_contributions_apart(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "text\n", "evidence.md": "text\n"})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    respond(root, "proposal-box-clamp@ultralytics-exporter", 1)
    ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    for contributor in ("aa-exporter", "bb-exporter"):
        ib.pack(source, proposal_fields(contributor=contributor, contributes_to="box-clamp"), root, cwd=tmp_path)
    respond(root, "proposal-box-clamp@aa-exporter", 1, state="closed")
    lines = ib.list_lines(root)
    assert "proposal-box-clamp@ultralytics-exporter v2 recorded (new version)" in lines
    assert "  sections: post.det.selection.nms" in lines
    assert "proposal-box-clamp@aa-exporter v1 closed (can delete)" in lines
    assert not any("needed by: proposal-box-clamp@bb-exporter" in line for line in lines)


def test_list_keeps_a_resolved_otherwise_bundle_with_a_not_met_goal(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "text\n", "intake.md": "text\n"})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    resolution = {"by": ["AB12"], "sections": ["x"], "contributor_action": "x",
                  "goals": [{"goal": "g", "met_by": "x h", "status": "not-met"}]}
    respond(root, "proposal-box-clamp@ultralytics-exporter", 1, state="resolved-otherwise", resolution=resolution)
    assert "proposal-box-clamp@ultralytics-exporter v1 resolved-otherwise" in ib.list_lines(root)
    ib.pack(source, model_fields(), root, cwd=tmp_path)
    respond(root, "model-yolo26@ultralytics-exporter", 1, state="waiting",
            waiting_on=["proposal-box-clamp@ultralytics-exporter"])
    lines = ib.list_lines(root)
    assert "  needed by: model-yolo26@ultralytics-exporter" in lines


def test_a_section_owner_keeps_its_role_after_a_later_finding(tmp_path: Path, root: Path) -> None:
    source = payload(tmp_path, {"proposal.md": "text\n"})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path)
    respond(root, "proposal-box-clamp@ultralytics-exporter", 1)
    respond(root, "proposal-box-clamp@ultralytics-exporter", 2, state="needs-contributor")
    ib.pack(source, proposal_fields(name="other-clamp", contributor="roboflow-exporter"), root, cwd=tmp_path)
    findings = ib.verify("proposal-other-clamp@roboflow-exporter", root)
    assert any("has the owner ultralytics-exporter" in f for f in findings)


def fake_repo(tmp_path: Path, changelog: str = "### 2.0.0\n") -> Path:
    """A synthetic checkout with only a changelog. `record` adds proposal records and their entries."""
    repo = tmp_path / "repo"
    (repo / "specs" / "model-sidecar").mkdir(parents=True)
    (repo / "specs" / "model-sidecar" / "changelog.md").write_text(changelog, encoding="utf-8")
    return repo


def record(repo: Path, status: str, created: str = "2026-10-28", **fields) -> None:
    """Add the record `proposals/<name>/` and its spec-log entry `AB12-<name>.md`."""
    manifest = {**proposal_fields(**fields), "version": 1, "created": created, "spec_version": "2.0.0"}
    folder = repo / "specs" / "model-sidecar" / "proposals" / manifest["name"]
    folder.mkdir(parents=True)
    (folder / "manifest.yaml").write_text(json.dumps(manifest), encoding="utf-8")
    entries = repo / "specs" / "model-sidecar" / "decisions" / "entries"
    entries.mkdir(parents=True, exist_ok=True)
    text = f"# AB12 - A proposal\n\n**Status:** {status}, 2026-11-03 (user; PR: pending).\n"
    (entries / f"AB12-{manifest['name']}.md").write_text(text, encoding="utf-8")


def test_spec_version_is_the_newest_version_heading(tmp_path: Path) -> None:
    text = "## Revisions\n\n### 9.1.0\n\n- Pre-release 10.0.0-rc.1: row 3.\n\n### 10.0.0\n\n### Scope of this revision\n"
    assert ib.spec_version(fake_repo(tmp_path, text)) == "10.0.0"
    assert ib.spec_version(fake_repo(tmp_path / "x", "## Revisions\n")) is None


def test_pack_needs_a_version_heading(tmp_path: Path, root: Path) -> None:
    with pytest.raises(ib.BundleError, match="no version heading"):
        ib.pack(payload(tmp_path, {"proposal.md": "x\n"}), proposal_fields(), root, cwd=tmp_path,
                repo=fake_repo(tmp_path, "# Changelog\n"))


def test_verify_finds_a_spec_version_that_is_not_a_heading_or_is_old_and_a_missing_one(
    tmp_path: Path, root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = payload(tmp_path, {"proposal.md": "text\n"})
    version_dir = ib.pack(source, proposal_fields(), root, cwd=tmp_path, repo=fake_repo(tmp_path, "### 1.9.0\n"))
    assert ib.read_manifest(version_dir)["spec_version"] == "1.9.0"
    assert ib.list_lines(root)[1:3] == ["  sections: post.det.selection.nms", "  spec_version: 1.9.0"]
    assert ib.verify("proposal-box-clamp@ultralytics-exporter", root) == [
        "spec_version 1.9.0 is not a version heading of the changelog of this checkout; pack a new version"
    ]
    with monkeypatch.context() as patch:
        patch.setattr(ib, "version_headings", lambda repo=None: ["1.9.0", "2.0.0"])
        assert ib.verify("proposal-box-clamp@ultralytics-exporter", root) == [
            "the checkout has the newer spec version 2.0.0 (spec_version 1.9.0); read its changes and pack a new version"
        ]
    manifest = ib.read_manifest(version_dir)
    del manifest["spec_version"]
    (version_dir / "manifest.yaml").write_text(json.dumps(manifest), encoding="utf-8")
    assert ib.verify("proposal-box-clamp@ultralytics-exporter", root) == [
        "manifest: missing key spec_version; pack a new version"
    ]


def test_a_tracked_record_keeps_the_section_owner_after_the_bundle_is_deleted(tmp_path: Path, root: Path) -> None:
    repo = fake_repo(tmp_path)
    record(repo, "proposed")
    found = ib.bundles(root, repo)
    assert ib.owners(found, repo) == {"post.det.selection.nms": "ultralytics-exporter"}
    entry = repo / "specs" / "model-sidecar" / "decisions" / "entries" / "AB12-box-clamp.md"
    for status, owned in (("accepted", True), ("absorbed into [x](x.md)", True), ("superseded by [CD34](x.md)", False),
                          ("rejected", False)):
        entry.write_text(f"**Status:** {status}, 2026-11-03.\n", encoding="utf-8")
        assert bool(ib.owners(found, repo)) is owned, status
    entry.unlink()
    assert ib.owners(found, repo) == {}  # a record with no entry owns nothing; the record test finds it


def test_the_owner_has_the_earlier_created_then_the_slug_that_sorts_first(tmp_path: Path) -> None:
    repo = fake_repo(tmp_path)
    record(repo, "proposed", "2026-10-02", name="zeta", contributor="aa-exporter")
    record(repo, "accepted", "2026-10-01", name="omega", contributor="bb-exporter", sections=["pre.resize.fit"])
    record(repo, "proposed", "2026-10-01", name="beta", contributor="cc-exporter")
    record(repo, "proposed", "2026-10-01", name="gamma", contributor="dd-exporter")
    assert ib.owners({}, repo) == {"post.det.selection.nms": "cc-exporter", "pre.resize.fit": "bb-exporter"}


def test_the_entry_status_gives_the_state_and_a_response_must_agree(tmp_path: Path, root: Path) -> None:
    repo = fake_repo(tmp_path)
    source = payload(tmp_path, {"proposal.md": "text\n"})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path, repo=repo)
    name = "proposal-box-clamp@ultralytics-exporter"
    respond(root, name, 1, state="recorded")
    record(repo, "rejected")
    assert f"{name} v1 rejected (can delete)" in ib.list_lines(root, repo)
    assert (
        "responses: the latest state recorded does not agree with the entry status rejected; "
        "the session writes a response rejected or resolved-otherwise"
    ) in ib.verify(name, root, repo)
    with pytest.raises(ib.BundleError, match="is rejected"):
        ib.pack(source, proposal_fields(), root, cwd=tmp_path, repo=repo)
    entry = repo / "specs" / "model-sidecar" / "decisions" / "entries" / "AB12-box-clamp.md"
    entry.write_text("**Status:** proposed, 2026-11-03.\n", encoding="utf-8")
    assert f"{name} v1 recorded" in ib.list_lines(root, repo)
    assert not any(f.startswith("responses:") for f in ib.verify(name, root, repo))
    assert ib.pack(source, proposal_fields(), root, cwd=tmp_path, repo=repo).name == "v2"
    entry.write_text("**Status:** absorbed into [x](x.md).\n", encoding="utf-8")
    assert f"{name} v2 landed (new version) (can delete)" in ib.list_lines(root, repo)


def test_answers_version_must_name_an_existing_version(tmp_path: Path, root: Path) -> None:
    repo = fake_repo(tmp_path)
    source = payload(tmp_path, {"proposal.md": "text\n"})
    ib.pack(source, proposal_fields(), root, cwd=tmp_path, repo=repo)
    name = "proposal-box-clamp@ultralytics-exporter"
    finding = (
        "responses: the latest response gives answers_version 2, but the current version is v1; "
        "answers_version is the version that the response answers"
    )
    respond(root, name, 1, state="needs-contributor", answers_version=2)
    assert finding in ib.verify(name, root, repo)
    respond(root, name, 2, state="needs-contributor", answers_version=1)
    assert not any(f.startswith("responses: the latest response gives") for f in ib.verify(name, root, repo))
    assert ib.pack(source, proposal_fields(), root, cwd=tmp_path, repo=repo).name == "v2"
    assert f"{name} v2 needs-contributor (new version)" in ib.list_lines(root, repo)


def test_each_record_folder_has_exactly_one_entry() -> None:
    assert {slug: len(paths) for slug, paths in ib.record_entries().items() if len(paths) != 1} == {}


def test_each_new_inventory_example_names_its_bundle() -> None:
    inventory = yaml.safe_load((REPO_ROOT / "specs" / "model-sidecar" / "inventory.yaml").read_text(encoding="utf-8"))
    without = {key for key, entry in inventory["examples"].items() if "bundle" not in entry}
    assert without <= ib.NO_BUNDLE_EXAMPLES


def test_responses_are_json_that_yaml_also_reads(tmp_path: Path, root: Path) -> None:
    respond(root, "proposal-box-clamp@ultralytics-exporter", 1, state="rejected", resolution={"reason": "no"})
    text = (root / "proposal-box-clamp@ultralytics-exporter" / "responses" / "r1.yaml").read_text(encoding="utf-8")
    assert yaml.safe_load(text) == json.loads(text)
    assert ib.response_problems(json.loads(text)) == []
    bad = {**json.loads(text), "state": "resolved-otherwise", "decision": "ADR-AB79"}
    problems = ib.response_problems(bad)
    assert "decision must be the bare ID, with no ADR- prefix" in problems
    assert "resolution needs the key goals" in problems
    resolution = {"by": ["AB12"], "sections": ["x"], "goals": [{"status": "met"}], "contributor_action": "x"}
    assert "each resolution goal needs goal, met_by and status met or not-met" in ib.response_problems(
        {**bad, "decision": None, "resolution": resolution}
    )


def test_each_sub_command_takes_root_after_its_name(root: Path, capsys: pytest.CaptureFixture) -> None:
    assert ib.main(["list", "--root", str(root)]) == 0
    assert capsys.readouterr().out == "no bundles\n"


# --------------------------------------------------------------------------------------------
# batch: the batch-conversion check. The graph builder copies the reshape model of
# skellytracker/tests/test_batch_conversion.py and adds a bias, a dynamic form and an empty form.
# --------------------------------------------------------------------------------------------

ITEMS = np.arange(18, dtype=np.float32).reshape(6, 3)


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
        return root, model_fields(external=external, batch_forced=None, batch_forced_reason=None), out

    return make


def test_batch_converts_down_and_up_and_writes_the_fragment(family) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}})
    report = ib.batch_check(fields, out, root=root)
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
    report = ib.batch_check(fields, out, root=root)
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
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "missing-verification-batch")
    assert report["v0"]["missing"] == [["n", "fp32", b] for b in gone]
    assert report["tuples"] == []


def test_batch_gives_to_run_for_a_family_with_no_file(family) -> None:  # noqa: ANN001
    """An empty `external` list is not a dynamic-only family (ADR-JB5J, item 3)."""
    root, fields, out = family({})
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "missing-verification-batch")


def test_batch_skips_the_check_of_a_forced_fallback(family) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}})
    fields |= {"batch_forced": 1, "batch_forced_reason": "the user forces b1"}
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["v0"]) == ("not applicable", {"result": "not applicable", "missing": []})


def test_batch_gives_to_run_when_the_runtime_cannot_load_a_file(family) -> None:  # noqa: ANN001
    onnx = pytest.importorskip("onnx")
    root, fields, out = family({1: {}, 2: {"ir_version": onnx.IR_VERSION + 1}, 3: {}, 6: {}})
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "host-runtime-cannot-load")
    assert list(report["v0b"]) == ["../../Exporter/m_b2_fp32.onnx"]


def test_batch_gives_no_signal_when_every_output_is_empty(family) -> None:  # noqa: ANN001
    root, fields, out = family({b: {"empty": True} for b in (1, 2, 3, 6)})
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "no-signal")


def test_batch_fails_v6_on_a_dynamic_file_with_other_output_names(family, tmp_path: Path) -> None:  # noqa: ANN001
    onnx = pytest.importorskip("onnx")
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}, "dynamic": {}})
    path = tmp_path / "Exporter" / "m_bdynamic_fp32.onnx"
    model = onnx.load(str(path))
    model.graph.node[-1].output[0] = "z"
    model.graph.output[0].name = "z"
    onnx.save(model, str(path))
    report = ib.batch_check(fields, out, root=root)
    assert report["dynamic_check"][0]["result"] == "fail"


def test_batch_gives_no_signal_when_v6_compares_nothing(family) -> None:  # noqa: ANN001
    root, fields, out = family({"dynamic": {"empty": True}})
    check = ib.batch_check(fields, out, root=root)["dynamic_check"][0]
    assert (check["result"], check["reason"]) == ("to run", "no-signal")


def reshape_by_constant(path: Path, batch: int | str) -> Path:
    """x[B, 3] -> Reshape([3B]) -> Sin -> Reshape([B, 3]): the [3B] constant hides the batch."""
    onnx = pytest.importorskip("onnx")
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
    report = ib.batch_check(fields, out, root=root)
    assert report["batch_conversion"] == "does not convert"
    assert not (out / "conversion.yaml").exists()


def test_batch_takes_a_dynamic_non_batch_dim_from_input_b(family, tmp_path: Path) -> None:  # noqa: ANN001
    onnx = pytest.importorskip("onnx")
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}, "dynamic": {}})
    path = tmp_path / "Exporter" / "m_bdynamic_fp32.onnx"
    model = onnx.load(str(path))
    model.graph.input[0].type.tensor_type.shape.dim[1].dim_param = "C"
    onnx.save(model, str(path))
    report = ib.batch_check(fields, out, root=root)
    assert report["batch_conversion"] == "converts"
    assert report["dynamic_check"][0]["result"] == "pass"
    assert (out / "report.json").is_file()


def test_batch_checks_a_dynamic_export_against_itself(family) -> None:  # noqa: ANN001
    """A dynamic-only family with no_static_reason needs no batch_forced: V0 gives `not applicable` (ADR-JB5J)."""
    root, fields, out = family({"dynamic": {}})
    fields |= {"no_static_reason": "the upstream export fixes a dynamic batch"}
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["v0"]) == ("not applicable", {"result": "not applicable", "missing": []})
    check = report["dynamic_check"][0]
    assert check["result"] == "pass"
    assert check["static"] == {}
    assert check["self"] == {"b2/A/y": "pass", "b3/A/y": "pass", "b2/B/y": "pass", "b3/B/y": "pass"}


def test_batch_checks_a_forced_dynamic_export_against_the_static_files_that_exist(family) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, "dynamic": {}})
    fields |= {"batch_forced": "dynamic", "batch_forced_reason": "the user forces dynamic"}
    check = ib.batch_check(fields, out, root=root)["dynamic_check"][0]
    assert (check["result"], sorted(check["static"])) == ("pass", ["b1/A", "b1/B"])


def test_batch_runs_a_dynamic_only_family_without_a_reason(family) -> None:  # noqa: ANN001
    """Without no_static_reason or batch_forced, V0 of a dynamic-only family is `to run` (ADR-JB5J, item 3)."""
    root, fields, out = family({"dynamic": {}})
    report = ib.batch_check(fields, out, root=root)
    assert (report["batch_conversion"], report["batch_conversion_reason"]) == ("to run", "missing-verification-batch")


def test_batch_gives_v6_to_run_without_input_b(family) -> None:  # noqa: ANN001
    root, fields, out = family({"dynamic": {}}, items=None)
    fields |= {"no_static_reason": "the upstream export fixes a dynamic batch"}
    report = ib.batch_check(fields, out, root=root)
    check = report["dynamic_check"][0]
    assert (report["batch_conversion"], check["result"]) == ("not applicable", "to run")
    assert "input B not found" in check["reason"]


@pytest.mark.parametrize(
    ("items", "message"),
    [(ITEMS[:3], "must hold 6 items"), (np.stack([ITEMS[0]] * 6), "more than once"), (None, "input B not found")],
)
def test_batch_needs_input_b_with_six_different_items(family, items, message: str) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}}, items=items)
    with pytest.raises(ib.BundleError, match=message):
        ib.batch_check(fields, out, root=root)


def test_batch_runs_only_in_the_venv_of_the_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(ib.sys, "prefix", str(tmp_path))
    assert ib.main(["batch", "--fields", str(tmp_path / "f.json"), "--out", str(tmp_path / "batch")]) == 1
    assert "batch runs only in the .venv of the checkout" in capsys.readouterr().err


def converts_bundle(
    tmp_path: Path, published: tuple, sidecar_source: int | None, conversion: bool, sizes: dict | None = None,
    batches: tuple = (1, 2, 3, 6), profile: dict = ib.PROFILE, **fields,
) -> Path:
    """Pack a model bundle (by default `converts`) with the given batches and return its intakes folder."""
    root = tmp_path / "freemocap" / "skellytracker" / "intakes"
    external = []
    for batch in batches:
        model = tmp_path / "Exporter" / f"m_b{batch}_fp32.onnx"
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_bytes(b"onnx")
        external.append({
            "path": f"../../Exporter/{model.name}", "role": "artifact", "size": "n", "batch": batch,
            "precision": "fp32", "published": batch in published,
        })
    entry = {
        "exporter": "E", "exporter_path": "x.yaml", "kind": "export", "exporter_layout_path": "x.yaml",
        "tracked": True, "commit": SOURCE,
    }
    batching: dict = {"batch": sidecar_source or 1}
    if sidecar_source:
        batching["batch_conversion"] = profile
    files = {
        "intake.md": "text\n",
        "example/provenance.yaml": json.dumps({"examples": {"detectors/x.yaml": entry}}),
        "example/detectors/x.yaml": json.dumps({"batching": batching} | ({"sizes": sizes} if sizes else {})),
    }
    if conversion:
        files["batch/conversion.yaml"] = json.dumps({"batching": {"batch_conversion": profile}})
    fields = {"batch_conversion": "converts", "batch_forced": None, "batch_forced_reason": None} | fields
    ib.pack(payload(tmp_path, files), model_fields(external=external, **fields), root, cwd=tmp_path)
    return root


SIDECAR_FINDING = (
    "publish rule: example/detectors/x.yaml must have batching.batch_conversion "
    "if and only if the published batch is 3"
)


def test_verify_passes_a_b3_publish(tmp_path: Path) -> None:
    root = converts_bundle(tmp_path, (3,), 3, conversion=True)
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == []


def test_verify_checks_the_publish_rule(tmp_path: Path) -> None:
    root = converts_bundle(tmp_path, (1, 3), 3, conversion=False)
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == [
        "publish rule: n fp32 must have exactly one published file, not 2",
        "publish rule: each published file must have one batch form (3, 1 or dynamic), not ['1', '3']",
        SIDECAR_FINDING,
    ]
    root = converts_bundle(tmp_path / "b", (3,), None, conversion=False)
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == [
        SIDECAR_FINDING,
        "publish rule: example/detectors/x.yaml must have batching.batch: 3",
        "publish rule: batch/conversion.yaml must have batching.batch_conversion: {'profile_id': 'static-batch-v1'}",
    ]


def test_verify_refuses_the_removed_source_batch_size(tmp_path: Path) -> None:
    old = {"profile_id": "static-batch-v1", "source_batch_size": 3}  # the form before ADR-JAA4
    root = converts_bundle(tmp_path, (3,), 3, conversion=True, profile=old)
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == [
        f"publish rule: example/detectors/x.yaml must have batching.batch_conversion: {ib.PROFILE}",
        f"publish rule: batch/conversion.yaml must have batching.batch_conversion: {ib.PROFILE}",
    ]


UNVERIFIABLE = (
    "publish rule: the batch form {} is not allowed with batch_conversion 'to run' and batch_forced None; "
    "export the verification batches 1, 2, 3 and 6, or set batch_forced"
)


@pytest.mark.parametrize(
    ("published", "fields", "batches", "finding"),
    [
        ((1,), {"batch_conversion": "does not convert"}, (1, 2, 3, 6), None),
        ((3,), {"batch_conversion": "does not convert"}, (1, 2, 3, 6),
         "publish rule: the batch form 3 is not allowed with batch_conversion 'does not convert' and batch_forced None"),
        ((1,), {"batch_conversion": "converts"}, (1, 2, 3, 6),
         "publish rule: the batch form 1 is not allowed with batch_conversion 'converts' and batch_forced None"),
        ((1,), {"batch_conversion": "converts", "batch_forced": 1, "batch_forced_reason": "user choice"}, (1, 2, 3, 6),
         None),
        ((1,), {"batch_conversion": "not applicable", "batch_forced": 1, "batch_forced_reason": "user choice"}, (1,),
         None),
        (("dynamic",), {"batch_conversion": "not applicable", "no_static_reason": "the upstream export fixes a dynamic batch"}, ("dynamic",),
         "n fp32: the dynamic check has no batch/report.json; do not publish the dynamic export; "
         "publish another batch form or fix the export"),
        ((3,), {"batch_conversion": "to run", "batch_conversion_reason": "missing-verification-batch"}, (3,),
         (UNVERIFIABLE.format(3),
          "publish rule: a b3 publish needs the verification batches: ['n/fp32/b1', 'n/fp32/b2', 'n/fp32/b6']")),
        ((1,), {"batch_conversion": "to run", "batch_conversion_reason": "missing-verification-batch"}, (1,),
         UNVERIFIABLE.format(1)),
        ((1,), {"batch_conversion": "to run", "batch_conversion_reason": "no-signal"}, (1, 2, 3, 6), None),
        ((), {"batch_conversion": "converts"}, (1, 2, 3, 6),
         "publish rule: n fp32 must have exactly one published file, not 0"),
        ((), {"batch_conversion": "converts", "verdict": "pending"}, (1, 2, 3, 6), None),
    ],
)
def test_verify_checks_the_publish_rule_for_every_verdict(
    tmp_path: Path, published: tuple, fields: dict, batches: tuple, finding: str | tuple | None
) -> None:
    source = 3 if published == (3,) else None
    root = converts_bundle(tmp_path, published, source, conversion=False, batches=batches, **fields)
    findings = ib.verify("model-yolo26@ultralytics-exporter", root)
    assert findings == (list(finding) if isinstance(finding, tuple) else [finding] if finding else []), findings


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"batch_forced": None, "batch_forced_reason": None}, "batch_conversion 'not applicable' needs batch_forced"),
        ({"batch_forced": None, "batch_forced_reason": None, "external": [{"batch": 1}]},
         "batch_conversion 'not applicable' needs batch_forced"),
        ({"batch_forced": 2}, "batch_forced must be null, 1 or 'dynamic'"),
        ({"batch_forced": True}, "batch_forced must be null, 1 or 'dynamic'"),
        ({"batch_forced_reason": ""}, "batch_forced_reason must give the reason"),
        ({"batch_forced": None}, "batch_forced_reason must be null unless batch_forced is set"),
        ({"batch_conversion": "to run", "batch_conversion_reason": "missing-verification-batch"},
         "batch_conversion_reason 'missing-verification-batch' is not possible with batch_forced"),
        ({"batch_forced": None, "batch_forced_reason": None, "external": [{"batch": "dynamic"}], "no_static_reason": "the upstream export fixes a dynamic batch",
          "batch_conversion": "to run", "batch_conversion_reason": "missing-verification-batch"},
         "or with only dynamic external files and no_static_reason"),
        ({"batch_forced": None, "batch_forced_reason": None, "external": [{"batch": "dynamic"}]},
         "only dynamic external files need no_static_reason"),
        ({"no_static_reason": "the upstream export fixes a dynamic batch"}, "no_static_reason must be null unless each external file is dynamic"),
        ({"batch_forced": None, "batch_forced_reason": None, "external": [{"batch": 1}], "no_static_reason": "x"},
         "no_static_reason must be null unless each external file is dynamic"),
        ({"external": [{"batch": "dynamic"}], "no_static_reason": "x"},
         "no_static_reason must be null unless each external file is dynamic and batch_forced is null"),
        ({"batch_forced": None, "batch_forced_reason": None, "external": [{"batch": "dynamic"}],
          "no_static_reason": " "}, "no_static_reason must be null or give the reason"),
    ],
)
def test_pack_checks_the_forced_batch_form(tmp_path: Path, root: Path, change: dict, message: str) -> None:
    with pytest.raises(ib.BundleError, match=re.escape(message)):
        ib.pack(payload(tmp_path, {"intake.md": "text\n"}), model_fields(**change), root, cwd=tmp_path)


def test_verify_finds_a_precision_that_the_sidecar_does_not_give(tmp_path: Path) -> None:
    root = converts_bundle(tmp_path, (3,), 3, conversion=True, sizes={"nano": {"onnx": {
        "precision_artifacts": {"fp16": {"filename": "m_b3_fp32.onnx"}}}}})
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == [
        "precision mismatch: m_b3_fp32.onnx is batch 3 fp32 in the manifest but not in example/detectors/x.yaml"
    ]


@pytest.mark.parametrize(
    ("report", "state"),
    [
        (None, "has no batch/report.json"),
        ({"dynamic_check": [{"size": "n", "precision": "fp32", "result": "to run", "reason": "no-signal"}]},
         "is to run (no-signal)"),
    ],
)
def test_verify_needs_a_passed_dynamic_check_for_a_published_dynamic_file(
    tmp_path: Path, report: dict | None, state: str
) -> None:
    root = tmp_path / "freemocap" / "skellytracker" / "intakes"
    model = tmp_path / "Exporter" / "m_fp32.onnx"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"onnx")
    item = {"path": "../../Exporter/m_fp32.onnx", "role": "artifact", "size": "n", "batch": "dynamic",
            "precision": "fp32", "published": True}
    files = {"intake.md": "text\n"} | ({"batch/report.json": json.dumps(report)} if report else {})
    ib.pack(payload(tmp_path, files), model_fields(external=[item]), root, cwd=tmp_path)
    assert ib.verify("model-yolo26@ultralytics-exporter", root) == [
        f"n fp32: the dynamic check {state}; do not publish the dynamic export; publish another batch form or fix the export"
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
        "n fp32: the dynamic check is fail; do not publish the dynamic export; publish another batch form or fix the export"
    ]


@pytest.mark.parametrize(
    ("template", "name", "fields"),
    [("model-intake.md", "intake.md", model_fields), ("change-proposal.md", "proposal.md", proposal_fields)],
)
def test_an_unchanged_template_has_no_plans_path_and_no_broken_link(
    tmp_path: Path, root: Path, template: str, name: str, fields
) -> None:  # noqa: ANN001
    text = (REPO_ROOT / "specs" / "model-sidecar" / "templates" / template).read_bytes()
    ib.pack(payload(tmp_path, {name: text}), fields(), root, cwd=tmp_path)
    manifest = fields()
    findings = ib.verify(f"{manifest['kind']}-{manifest['name']}@{manifest['contributor']}", root)
    assert [f for f in findings if "plans/" in f or "does not resolve" in f] == []


# --------------------------------------------------------------------------------------------
# Bundles are untrusted input (ADR-AD33): the static check of a reference module and the ONNX check
# --------------------------------------------------------------------------------------------

CLEAN_MODULE = '''"""A clean reference module."""
from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np
import pre_resize_letterbox

LIMIT = 2 ** 8
NAMES: tuple = ("a", "b")


class Box:
    """A box."""

    size: int = 0

    def area(self) -> int:
        return self.size * self.size


def run(params: dict, input: dict) -> dict[str, Any]:
    scale = pre_resize_letterbox.run(params, input)["scale"]
    data = np.asarray(input["x"], dtype=np.float32).flags.writeable
    return {"y": math.floor(scale), "w": getattr(np, "float32"), "d": data, "c": cv2.INTER_LINEAR}


def inverse(params, input):
    return {"x": input["y"]}
'''


def reference_findings(tmp_path: Path, text: str, name: str = "post_det_clamp.py") -> list[str]:
    path = tmp_path / "check" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return ib.reference_problems(path)[0]


def test_the_static_check_passes_a_clean_module_and_finds_its_functions(tmp_path: Path) -> None:
    path = tmp_path / "post_det_clamp.py"
    path.write_text(CLEAN_MODULE, encoding="utf-8")
    assert ib.reference_problems(path) == ([], ["run", "inverse"])


@pytest.mark.parametrize(
    ("text", "finding"),
    [
        ("import os\n", "line 1: imports os: not NumPy"),
        ("import os as numpy\n", "line 1: imports os: not NumPy"),
        ("import importlib.util\n", "imports importlib.util"),
        ("from importlib import import_module\n", "imports importlib"),
        ("from . import post_det_decode\n", "line 1: a relative import"),
        ("from pre_resize_fit import run\n", "line 1: from pre_resize_fit import: import the section module"),
        ("import onnx\n", "imports onnx: not NumPy"),
        ("from numpy import load\n", "imports load from numpy"),
        ("from numpy import *\n", "imports * from numpy"),
        ("import numpy.ctypeslib\n", "imports ctypeslib from numpy"),
        ("from cv2 import dnn\n", "imports dnn from cv2"),
        ("import numpy as n\n\ndef run(p, i):\n    return n.load(i['f'])\n", "line 4: uses the attribute load"),
        ("import numpy as np\n\ndef run(p, i):\n    np.save('x', 1)\n", "uses the attribute save"),
        ("import numpy as np\n\ndef run(p, i):\n    i['a'].tofile('x')\n", "uses the attribute tofile"),
        ("import cv2\n\ndef run(p, i):\n    return cv2.imread('x')\n", "uses the attribute imread"),
        ("import cv2\n\ndef run(p, i):\n    return cv2.dnn.readNet('x')\n", "uses the attribute dnn"),
        ("import cv2\n\ndef run(p, i):\n    return cv2.VideoCapture(0)\n", "uses the attribute VideoCapture"),
        ("def run(p, i):\n    return open('x').read()\n", "line 2: uses open"),
        ("def run(p, i):\n    return eval(i['x'])\n", "uses eval"),
        ("def run(p, i):\n    exec('x = 1')\n", "uses exec"),
        ("def run(p, i):\n    return compile('1', 'f', 'eval')\n", "uses compile"),
        ("def run(p, i):\n    return __import__('os')\n", "uses __import__"),
        ("def run(p, i):\n    breakpoint()\n", "uses breakpoint"),
        ("def run(p, i):\n    return input()\n", "line 2: calls input"),
        ("def run(p, i):\n    return globals()\n", "uses globals"),
        ("def run(p, i):\n    return __builtins__\n", "uses __builtins__"),
        ("def run(p, i):\n    return __loader__\n", "uses __loader__"),
        ("def run(p, i):\n    return vars(i)\n", "uses vars"),
        ("def run(p, i):\n    return ().__class__.__bases__\n", "uses the attribute __class__"),
        ("import numpy as np\n\ndef run(p, i):\n    return getattr(np, 'lo' + 'ad')\n", "getattr with a name that is not"),
        ("import numpy as np\n\ndef run(p, i):\n    return getattr(np, 'load')\n", "the string 'load' names load"),
        ("import numpy as np\n\ndef run(p, i):\n    return getattr(np, i['name'])\n", "getattr with a name that is not"),
        ("import operator\n\ndef run(p, i):\n    return operator.attrgetter('__globals__')(run)\n",
         "the string '__globals__' names __globals__"),
        ("def run(p, i):\n    g = getattr\n    return g(p, 'x')\n", "line 2: uses getattr"),
        ("print('hi')\n", "line 1: the module runs code at import (Expr)"),
        ("X = make()\n", "line 1: the module runs code at import (Assign)"),
        ("f = lambda: open('x')\n", "line 1: the module runs code at import (Assign)"),
        ("for i in range(2):\n    pass\n", "line 1: the module runs code at import (For)"),
        ("try:\n    import numpy\nexcept ImportError:\n    pass\n", "line 1: the module runs code at import (Try)"),
        ("class A:\n    x = make()\n", "line 2: the class A runs code at import (Assign)"),
        ("def run(p, i:\n", "not a readable Python file: SyntaxError"),
        # Code in the header of a definition or in an annotation also runs at import.
        ("import cv2\nX: cv2.add(1, 2)\n", "line 2: the module runs code at import (AnnAssign)"),
        ("import cv2\nif cv2.add(1, 2) or cv2.TYPE_CHECKING:\n    import math\n", "line 2: the module runs code at import (If)"),
        ("def run(p, i, _=make()):\n    pass\n", "line 1: the module runs code at import (the header of run)"),
        ("def run(p: make(), i):\n    pass\n", "(the header of run)"),
        ("def run(p, i) -> make():\n    pass\n", "(the header of run)"),
        ("@(lambda f: f)\ndef run(p, i):\n    pass\n", "(the header of run)"),
        ("@wrap(make())\ndef run(p, i):\n    pass\n", "(the header of run)"),
        ("class A(make()):\n    pass\n", "(the header of A)"),
        ("class A(metaclass=make()):\n    pass\n", "(the header of A)"),
        ("class A:\n    x: list = make(default=list)\n", "line 2: the class A runs code at import (AnnAssign)"),
        # The allowed modules reach os, sys and importlib, and NumPy runs text as code.
        ("import cv2\n\ndef run(p, i):\n    cv2.os.system('calc')\n", "uses the attribute os"),
        ("import cv2\n\ndef run(p, i):\n    cv2.importlib.import_module('x')\n", "uses the attribute importlib"),
        ("import typing\n\ndef run(p, i):\n    typing.sys.modules\n", "uses the attribute sys"),
        ("import dataclasses\n\ndef run(p, i):\n    dataclasses.inspect\n", "uses the attribute inspect"),
        ("import enum\n\ndef run(p, i):\n    enum.bltns\n", "uses the attribute bltns"),
        ("import statistics\n\ndef run(p, i):\n    statistics.random._os\n", "uses the attribute _os"),
        ("import numpy as np\n\ndef run(p, i):\n    np.testing.measure('1', 1)\n", "uses the attribute measure"),
        ("import collections\n\ndef run(p, i):\n    collections._sys\n", "uses the attribute _sys"),
        # The OpenCV factories that load a model or a data file.
        ("import cv2\n\ndef run(p, i):\n    cv2.FaceDetectorYN_create('m', '', (1, 1))\n", "uses the attribute FaceDetectorYN_create"),
        ("import cv2\n\ndef run(p, i):\n    cv2.dnn_Net()\n", "uses the attribute dnn_Net"),
        ("import cv2\n\ndef run(p, i):\n    cv2.TrackerNano_create()\n", "uses the attribute TrackerNano_create"),
        ("import cv2\n\ndef run(p, i):\n    cv2.wechat_qrcode_WeChatQRCode('m')\n", "uses the attribute wechat_qrcode_WeChatQRCode"),
        ("import cv2\n\ndef run(p, i):\n    cv2.CascadeClassifier_convert('a', 'b')\n", "uses the attribute CascadeClassifier_convert"),
        ("import cv2\n\ndef run(p, i):\n    cv2.data.haarcascades\n", "uses the attribute haarcascades"),
        ("import cv2\n\ndef run(p, i):\n    cv2.FileStorage('x', 0)\n", "uses the attribute FileStorage"),
    ],
)
def test_the_static_check_finds_each_kind_of_finding(tmp_path: Path, text: str, finding: str) -> None:
    findings = reference_findings(tmp_path, text)
    assert any(finding in f for f in findings), findings


def test_the_static_check_allows_onnx_only_in_the_profile_module(tmp_path: Path) -> None:
    profile = "import onnx\n\ndef model_batch_convert(source, target, **kw):\n    onnx.save(onnx.load(source), target)\n"
    assert reference_findings(tmp_path, profile, "common_batch_conversion.py") == []
    assert reference_findings(tmp_path, profile, "post_det_clamp.py") != []


def test_the_static_check_allows_the_safe_headers_of_a_definition(tmp_path: Path) -> None:
    text = (
        "import dataclasses\nimport functools\nimport typing\nfrom dataclasses import dataclass, field\n"
        "if typing.TYPE_CHECKING:\n    import math\n\n\n"
        "@dataclass(frozen=True)\nclass P:\n    xs: list = field(default_factory=list)\n"
        "    ys: tuple = dataclasses.field(default=(1, 2))\n\n\n"
        "@functools.lru_cache(maxsize=None)\ndef run(params: dict, input: dict, scale: float = 1.0) -> dict:\n"
        "    return {}\n"
    )
    assert reference_findings(tmp_path, text) == []


def test_only_a_manifest_section_is_a_new_section_module(tmp_path: Path) -> None:
    """A file next to the module does not count, and a new section name must not be an installed module."""
    (tmp_path / "check").mkdir()
    (tmp_path / "check" / "post_new_section.py").write_text("", encoding="utf-8")
    path = tmp_path / "check" / "post_det_clamp.py"
    path.write_text("import os\nimport post_new_section\nimport pre_commit.util\n", encoding="utf-8")
    not_allowed = "not NumPy, OpenCV, a listed standard-library module or a section module"
    assert ib.reference_problems(path)[0] == [
        f"line 1: imports os: {not_allowed}",
        f"line 2: imports post_new_section: {not_allowed}",
        f"line 3: imports pre_commit.util: {not_allowed}",
    ]
    assert ib.reference_problems(path, {"post_new_section", "pre_commit", "os"})[0] == [
        f"line 1: imports os: {not_allowed}",
        "line 3: imports pre_commit.util: the section name is also the name of an installed module",
    ]


# A reference module that writes the file AD33_MARKER when it runs.
MALICIOUS = (
    "import os\n"
    "os.makedirs(os.path.dirname(os.environ['AD33_MARKER']), exist_ok=True)\n"
    "with open(os.environ['AD33_MARKER'], 'w') as handle:\n    handle.write('ran')\n\n\n"
    "def run(params, input):\n    return {'y': input['x']}\n"
)


@pytest.fixture
def marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "marker"
    monkeypatch.setenv("AD33_MARKER", str(path))
    return path


def test_the_malicious_module_writes_its_marker_when_it_runs(tmp_path: Path, marker: Path) -> None:
    """The proof that the tests below use a module that would leave a trace."""
    exec(compile(MALICIOUS, "malicious", "exec"), {})  # noqa: S102  # test code of this repo
    assert marker.read_text(encoding="utf-8") == "ran"


def test_verify_reads_a_malicious_reference_module_and_never_runs_it(tmp_path: Path, root: Path, marker: Path) -> None:
    rel = "vectors/post.det.clamp.yaml"
    vectors = {"section": "post.det.clamp", "tolerance": 0, "unverified": "a test",
               "cases": [{"id": "a", "params": {}, "input": {"x": 1}, "expect": {"y": 1}}]}
    source = payload(tmp_path, {
        "proposal.md": "text\n", "reference/post_det_clamp.py": MALICIOUS, rel: json.dumps(vectors),
    })
    ib.pack(source, proposal_fields(sections=["post.det.clamp"]), root, cwd=tmp_path)
    findings = ib.verify("proposal-box-clamp@ultralytics-exporter", root)
    module = "reference/post_det_clamp.py"
    at_import = "use only a docstring, imports, constants and definitions"
    assert findings == [
        f"{module}: line 2: the module runs code at import (Expr); {at_import}",
        f"{module}: line 3: the module runs code at import (With); {at_import}",
        f"{module}: line 1: imports os: not NumPy, OpenCV, a listed standard-library module or a section module",
        f"{module}: line 3: uses open",
        f"{module}: line 4: uses the attribute write",
        f"{module}: line 2: uses the attribute environ",
        f"{module}: line 3: uses the attribute environ",
    ]
    assert not marker.exists()


def test_a_contribution_gets_the_findings_of_its_owner_module(tmp_path: Path, root: Path, marker: Path) -> None:
    rel = "vectors/post.det.clamp.yaml"
    vectors = {"section": "post.det.clamp", "tolerance": 0, "unverified": "a test",
               "cases": [{"id": "a", "params": {}, "input": {"x": 1}, "expect": {"y": 1}}]}
    owner = payload(tmp_path / "o", {"proposal.md": "text\n", "reference/post_det_clamp.py": MALICIOUS})
    ib.pack(owner, proposal_fields(sections=["post.det.clamp"]), root, cwd=tmp_path)
    contribution = payload(tmp_path / "c", {"evidence.md": "text\n", rel: json.dumps(vectors)})
    ib.pack(contribution, proposal_fields(sections=["post.det.clamp"], contributor="openmmlab-exporter",
                                          contributes_to="box-clamp"), root, cwd=tmp_path)
    findings = ib.verify("proposal-box-clamp@openmmlab-exporter", root)
    prefix = "proposal-box-clamp@ultralytics-exporter/v1/reference/post_det_clamp.py: "
    assert [f[: len(prefix)] for f in findings] == [prefix] * 7
    assert not marker.exists()


def test_verify_allows_the_sections_of_a_depends_on_bundle_and_refuses_a_shim_file(tmp_path: Path, root: Path) -> None:
    other = payload(tmp_path / "o", {"proposal.md": "text\n", "reference/post_new_thing.py": "def run(params, input):\n    return {}\n"})
    ib.pack(other, proposal_fields(name="new-thing", sections=["post.new_thing"]), root, cwd=tmp_path)
    module = "import post_new_thing\nimport pre_commit\n\n\ndef run(params, input):\n    return post_new_thing.run(params, input)\n"
    source = payload(tmp_path / "s", {
        "proposal.md": "text\n", "reference/post_det_clamp.py": module, "reference/pre_commit.py": '"""A shim."""\n',
    })
    ib.pack(source, proposal_fields(sections=["post.det.clamp"], depends_on=["proposal-new-thing@ultralytics-exporter"]),
            root, cwd=tmp_path)
    findings = [f for f in ib.verify("proposal-box-clamp@ultralytics-exporter", root) if f.startswith("reference/")]
    assert findings == [
        "reference/post_det_clamp.py: line 2: imports pre_commit: not NumPy, OpenCV, a listed standard-library module "
        "or a section module",
        "reference/pre_commit.py: not reference/<section_module>.py of a section of the manifest",
    ]


def test_a_section_name_that_is_a_path_never_loads_a_file(tmp_path: Path, marker: Path) -> None:
    import make_vectors as mv

    (tmp_path / "evil.py").write_text(MALICIOUS, encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        mv.load_reference(tmp_path.as_posix() + "/evil", mv.REFERENCE_DIR)
    assert not marker.exists()
    assert mv.package_function("tools/make_vectors.py::main") is None
    assert mv.package_function("skellytracker/../tools/make_vectors.py::main") is None


def tiny_model(path: Path, domain: str = "", location: str | None = None) -> Path:
    """y = Relu(x), or y = x + w with the external data of w at `location`."""
    onnx = pytest.importorskip("onnx")
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
    assert ib.onnx_problems(tiny_model(tmp_path / "m.onnx")) == []
    assert ib.onnx_problems(tiny_model(tmp_path / "e.onnx", location="e.onnx.data")) == []
    assert ib.onnx_problems(tiny_model(tmp_path / "s.onnx", domain="com.microsoft")) == []


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
    findings = ib.onnx_problems(tiny_model(tmp_path / "m.onnx", **options))
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
    onnx = pytest.importorskip("onnx")
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
    assert any(finding in f for f in ib.onnx_problems(tmp_path / "m.onnx")), kind


def test_the_onnx_check_refuses_a_file_that_onnx_cannot_read(tmp_path: Path) -> None:
    pytest.importorskip("onnx")
    (tmp_path / "m.onnx").write_bytes(b"\xff not a model")
    assert ib.onnx_problems(tmp_path / "m.onnx")[0].startswith("onnx cannot read the file")


def test_batch_refuses_a_model_before_any_run(family, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ANN001
    root, fields, out = family({1: {}, 2: {}, 3: {}, 6: {}})
    tiny_model(tmp_path / "Exporter" / "m_b2_fp32.onnx", domain="my.custom")

    def no_run(*_args: object) -> None:
        raise AssertionError("batch ran a model")

    monkeypatch.setattr(ib, "_load_problem", no_run)
    monkeypatch.setattr(ib._Runner, "session", no_run)
    with pytest.raises(ib.BundleError, match=r"batch does not run \.\./\.\./Exporter/m_b2_fp32\.onnx: .*my\.custom"):
        ib.batch_check(fields, out, root=root)
    assert not (out / "report.json").exists()
