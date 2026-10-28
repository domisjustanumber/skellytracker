"""The hand-over tool `tools/intake_bundle.py` packs, lists and verifies bundles."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import intake_bundle as ib
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
