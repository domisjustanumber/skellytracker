"""The CLI commands `detectors` and `describe`."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from skellytracker.core.detectors.cli import main
from skellytracker.core.model_spec import artifacts
from skellytracker.tests.detectors.test_catalog import KEY, put
from skellytracker.tests.model_spec.sidecars import BASES


@pytest.fixture(autouse=True)
def private_hash_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(artifacts, "default_hash_cache_path", lambda: tmp_path / "cache" / "hash-cache.json")


def test_detectors_prints_one_line_for_each_entry(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    put(tmp_path / "user", BASES["nms"]())
    assert main(["detectors", "--user-root", str(tmp_path / "user")]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith(f"{KEY}==0.1.0  [onnx]  unavailable: the sidecar uses spec sections")
    assert "charuco@skellytracker  [calibration]  available" in lines
    assert main(["detectors", "--json", "--user-root", str(tmp_path / "user")]) == 0
    entries = json.loads(capsys.readouterr().out)
    assert entries[0]["key"] == KEY and entries[0]["artifacts"][0]["filename"] == "demo-n_b3_fp32.onnx"


def test_describe_prints_one_entry_and_exits_with_1_for_an_unknown_key(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    put(tmp_path / "user", BASES["nms"]())
    assert main(["describe", KEY, "--user-root", str(tmp_path / "user")]) == 0
    text = capsys.readouterr().out
    assert "sidecar_sha256: " in text and "port detections: output, detections" in text and "param size: \"n\"" in text
    assert main(["describe", KEY, "--json", "--user-root", str(tmp_path / "user")]) == 0
    description = json.loads(capsys.readouterr().out)
    assert description["sizes"] == {"n": ["fp32"]} and description["params"]["object_decode"]["selection"] == "nms"
    assert main(["describe", "nothing@nowhere", "--user-root", str(tmp_path / "user")]) == 1
    assert "no entry 'nothing@nowhere'" in capsys.readouterr().out
