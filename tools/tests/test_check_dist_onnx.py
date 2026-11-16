"""The release check fails when a wheel or an sdist holds an ``.onnx`` file (decision AMJ8 item 5)."""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import check_dist_onnx as cdo

ONNX = "skellytracker/core/model_zoo/detectors/x/x.onnx"
YAML = "skellytracker/core/model_zoo/detectors/x/x.yaml"


def wheel(path: Path, *names: str) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name in names:
            zf.writestr(name, b"")
    return path


def sdist(path: Path, *names: str) -> Path:
    with tarfile.open(path, "w:gz") as tf:
        for name in names:
            tf.addfile(tarfile.TarInfo(f"skellytracker-1.0/{name}"), io.BytesIO(b""))
    return path


def test_clean_archives_pass(tmp_path: Path) -> None:
    wheel(tmp_path / "skellytracker-1.0-py3-none-any.whl", YAML)
    sdist(tmp_path / "skellytracker-1.0.tar.gz", YAML)
    assert cdo.main([str(tmp_path)]) == 0


def test_onnx_in_a_wheel_fails(tmp_path: Path, capsys) -> None:
    whl = wheel(tmp_path / "skellytracker-1.0-py3-none-any.whl", YAML, ONNX)
    assert cdo.main([str(whl)]) == 1
    assert ONNX in capsys.readouterr().err


def test_onnx_in_an_sdist_fails(tmp_path: Path, capsys) -> None:
    wheel(tmp_path / "skellytracker-1.0-py3-none-any.whl", YAML)
    sdist(tmp_path / "skellytracker-1.0.tar.gz", ONNX.upper())
    assert cdo.main([str(tmp_path)]) == 1
    assert "skellytracker-1.0.tar.gz" in capsys.readouterr().err


def test_no_archive_fails(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("")
    assert cdo.main([str(tmp_path)]) == 2
