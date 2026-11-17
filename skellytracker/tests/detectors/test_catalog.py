"""The catalog of the `detectors` entry point, on temporary sidecar roots."""
from __future__ import annotations

import functools
import hashlib
import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from skellytracker.core import detectors
from skellytracker.core.detectors import catalog
from skellytracker.core.detectors.catalog import (
    STATIC_DETECTORS,
    DetectorNotFoundError,
    DetectorUnavailableError,
    describe_detector,
    get_detector,
    list_detectors,
    load_detector_sidecar,
    resolve_user_root,
    scan_sidecar_roots,
)
from skellytracker.core.model_spec import artifacts, sections
from skellytracker.tests.model_spec.sidecars import BASES, changed, write_yaml

DEMO = "detectors/object_detectors/demo/demo.yaml"
KEY = "demo@demo-exporter"
ONNX = b"not a real graph"


@pytest.fixture(autouse=True)
def private_hash_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(artifacts, "default_hash_cache_path", lambda: tmp_path / "cache" / "hash-cache.json")
    monkeypatch.delenv(catalog.USER_ROOT_VARIABLE, raising=False)
    # The catalog of these tests has no sidecar of `core/model_zoo/`: a test names each root.
    without_package = functools.partial(scan_sidecar_roots, package_root=tmp_path / "no-package-root")
    monkeypatch.setattr(catalog, "scan_sidecar_roots", without_package)


@pytest.fixture
def all_sections(monkeypatch: pytest.MonkeyPatch) -> None:
    """The state after the processing stages: the package runs each section."""
    monkeypatch.setattr(sections, "IMPLEMENTED_SECTIONS", frozenset(section.id for section in sections.SECTIONS))


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "user"


def put(root: Path, sidecar: dict[str, Any], relative_path: str = DEMO, files: bool = True, content: bytes = ONNX) -> Path:
    """Write a sidecar, and its ONNX files with the hash of the sidecar. Return the sidecar path."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    for size in sidecar["sizes"].values():
        for artifact in size["onnx"]["precision_artifacts"].values():
            artifact["sha256"] = hashlib.sha256(content).hexdigest()
            if files:
                (path.parent / artifact["filename"]).write_bytes(content)
    write_yaml(path, sidecar)
    return path


def onnx_entries(root: Path) -> list[Any]:
    return [entry for entry in list_detectors(root) if entry.category == "onnx"]


# ---------------------------------------------------------------------------------------------
# The user root and the entries with no sidecar
# ---------------------------------------------------------------------------------------------


def test_the_user_root_is_the_argument_then_the_variable_then_the_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    default = resolve_user_root()
    assert default.name == "models" and default.parent.name == "skellytracker"
    monkeypatch.setenv(catalog.USER_ROOT_VARIABLE, str(tmp_path / "from-variable"))
    assert resolve_user_root() == tmp_path / "from-variable"
    assert resolve_user_root(tmp_path / "argument") == tmp_path / "argument"


def test_an_empty_user_root_gives_the_entries_with_no_sidecar(root: Path) -> None:
    entries = list_detectors(root)
    assert [(entry.key, entry.category) for entry in entries] == [
        ("mediapipe_pose@skellytracker", "mediapipe"),
        ("mediapipe_hand@skellytracker", "mediapipe"),
        ("mediapipe_face@skellytracker", "mediapipe"),
        ("charuco@skellytracker", "calibration"),
        ("aruco@skellytracker", "calibration"),
    ]
    assert all(entry.sidecar_path is None and not entry.artifacts for entry in entries)
    assert not {"keypoint_bbox", "precomputed"} & {entry.key.split("@")[0] for entry in entries}


@pytest.mark.parametrize("static", STATIC_DETECTORS, ids=lambda static: static.detector_type)
def test_each_entry_of_the_static_table_has_a_known_class(static: catalog.StaticDetector) -> None:
    if static.category == "mediapipe":
        pytest.importorskip("mediapipe")
    assert isinstance(getattr(importlib.import_module(static.module), static.class_name), type)


def test_an_entry_with_no_sidecar_is_unavailable_without_its_package(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(catalog, "find_spec", lambda name: None if name == "mediapipe" else object())
    by_key = {entry.key: entry for entry in list_detectors(root)}
    pose = by_key["mediapipe_pose@skellytracker"]
    assert not pose.available and "skellytracker[mediapipe]" in pose.unavailable_reason
    assert by_key["charuco@skellytracker"].available and by_key["charuco@skellytracker"].unavailable_reason is None


def test_the_list_imports_no_detector_module(tmp_path: Path) -> None:
    modules = sorted({static.module for static in STATIC_DETECTORS})
    code = (
        "import sys\n"
        "from skellytracker.core.detectors import list_detectors\n"
        f"assert len(list_detectors({str(tmp_path)!r})) >= {len(STATIC_DETECTORS)}\n"
        f"print([name for name in {modules!r} if name in sys.modules])\n"
    )
    result = subprocess.run([sys.executable, "-W", "ignore", "-c", code], capture_output=True, text=True, env=dict(os.environ), check=True)  # noqa: S603
    assert result.stdout.strip() == "[]"


# ---------------------------------------------------------------------------------------------
# Sidecar entries: the capability check and the artifact hash check
# ---------------------------------------------------------------------------------------------


def test_a_sidecar_with_its_files_is_available(root: Path, all_sections: None) -> None:
    path = put(root, BASES["nms"]())
    (entry,) = onnx_entries(root)
    assert (entry.key, entry.version, entry.available, entry.unavailable_reason) == (KEY, "0.1.0", True, None)
    assert (entry.sidecar_path, entry.sidecar_root) == (path, root)
    assert entry.sidecar_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert entry.role == ("object_detector",) and "post.object.selection.nms" in entry.sections
    artifact = entry.artifact("n", "fp32")
    assert artifact.available and artifact.path == path.parent / "demo-n_b3_fp32.onnx"
    with pytest.raises(ValueError, match="no artifact xl/fp32"):
        entry.artifact("xl", "fp32")
    assert detectors.list_detectors is list_detectors


def test_a_sidecar_that_uses_a_section_that_the_package_does_not_run_is_unavailable(root: Path) -> None:
    put(root, BASES["top_k"]())
    (entry,) = onnx_entries(root)
    assert not entry.available and not entry.artifact("n", "fp32").available
    assert "post.object.selection.top_k" in entry.unavailable_reason and "pre.resize.stretch" not in entry.unavailable_reason
    assert "common.identity" not in entry.unavailable_reason
    with pytest.raises(DetectorUnavailableError, match="post.object.selection.top_k"):
        load_detector_sidecar(KEY, root)


def test_the_capability_check_is_for_each_artifact(root: Path, all_sections: None) -> None:
    sidecar = BASES["nms"]()
    sidecar["input"]["dtype"]["fp16"] = "float16"
    for output in sidecar["outputs"]:
        output["dtype"]["fp16"] = "float16"
    sidecar["sizes"]["n"]["onnx"]["precision_artifacts"]["fp16"] = {"filename": "demo-n_b3_fp16.onnx", "sha256": "0" * 64}
    path = put(root, sidecar)
    (path.parent / "demo-n_b3_fp16.onnx").unlink()
    (entry,) = onnx_entries(root)
    assert entry.available, entry.unavailable_reason
    assert entry.artifact("n", "fp32").available
    missing = entry.artifact("n", "fp16")
    assert not missing.available and "demo-n_b3_fp16.onnx is not present" in missing.unavailable_reason


def test_a_model_with_no_onnx_file_is_unavailable(root: Path, all_sections: None) -> None:
    put(root, BASES["nms"](), files=False)
    (entry,) = onnx_entries(root)
    assert not entry.available and "is not present" in entry.unavailable_reason
    assert not entry.artifact("n", "fp32").downloaded
    assert load_detector_sidecar(KEY, root).model_id == "demo"  # the sidecar itself loads


def test_a_url_artifact_that_is_not_downloaded_is_available_and_not_downloaded(root: Path, tmp_path: Path, all_sections: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(artifacts, "download_root", lambda: tmp_path / "cache" / "models")
    sidecar = BASES["nms"]()
    sidecar["sizes"]["n"]["onnx"]["precision_artifacts"]["fp32"].update(url="https://example.org/demo.onnx", url_sha256="e" * 64)
    path = put(root, sidecar, files=False)
    file = tmp_path / "cache" / "models" / KEY / "0.1.0" / "demo-n_b3_fp32.onnx"

    def state() -> tuple[bool, bool, bool, str | None, Path]:
        (entry,) = onnx_entries(root)
        artifact = entry.artifact("n", "fp32")
        return entry.available, artifact.available, artifact.downloaded, artifact.unavailable_reason, artifact.path

    assert state() == (True, True, False, None, file)
    file.parent.mkdir(parents=True)
    file.write_bytes(b"a partial download")  # the host downloads a bad file of the download folder again
    assert state() == (True, True, False, None, file)
    file.write_bytes(ONNX)
    assert state() == (True, True, True, None, file)
    beside = path.parent / "demo-n_b3_fp32.onnx"
    beside.write_bytes(ONNX)  # the file beside the sidecar comes first
    assert state() == (True, True, True, None, beside)


def test_an_onnx_file_with_a_different_hash_is_unavailable(root: Path, all_sections: None) -> None:
    path = put(root, BASES["nms"]())
    (path.parent / "demo-n_b3_fp32.onnx").write_bytes(b"a partial download")
    (entry,) = onnx_entries(root)
    assert not entry.available and "V-common.sizes_and_artifacts-10" in entry.artifact("n", "fp32").unavailable_reason
    assert "V-common.sizes_and_artifacts-10" in entry.unavailable_reason


def test_the_hash_check_uses_the_cache_and_full_hash_reads_the_file_again(root: Path, all_sections: None, monkeypatch: pytest.MonkeyPatch) -> None:
    put(root, BASES["nms"]())
    calls: list[Path] = []
    file_sha256 = artifacts.file_sha256
    monkeypatch.setattr(artifacts, "file_sha256", lambda path: calls.append(path) or file_sha256(path))
    list_detectors(root)
    list_detectors(root)
    assert len(calls) == 1
    list_detectors(root, full_hash=True)
    assert len(calls) == 2


def test_a_crlf_sidecar_is_listed_with_a_reason_that_names_crlf(root: Path) -> None:
    path = put(root, BASES["nms"]())
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    (entry,) = onnx_entries(root)
    assert entry.key == KEY and not entry.available
    assert "CRLF" in entry.unavailable_reason and "V-format.composition-3" in entry.unavailable_reason


def test_a_schema_version_that_the_release_does_not_implement_names_the_version(root: Path) -> None:
    put(root, changed(BASES["nms"](), {"schema_version": "9.9.9"}))
    (entry,) = onnx_entries(root)
    assert not entry.available and "'9.9.9'" in entry.unavailable_reason
    with pytest.raises(DetectorUnavailableError, match="9.9.9"):
        load_detector_sidecar(KEY, root)


def test_a_yaml_file_that_is_not_a_sidecar_is_not_in_the_list(root: Path) -> None:
    write_yaml(root / "detectors" / "shared" / "skeletons" / "fragment.yaml", ["a", "b"])
    write_yaml(root / "detectors" / "object_detectors" / "demo" / "other-name.yaml", BASES["nms"]())
    assert onnx_entries(root) == []
    write_yaml(root / "odd.yaml", {1: "a key that is not a string", "schema_version": "2.0.0", "model_id": "odd"})
    (entry,) = onnx_entries(root)
    assert entry.key == "odd@unknown" and not entry.available


# ---------------------------------------------------------------------------------------------
# Keys, versions and roots
# ---------------------------------------------------------------------------------------------


def test_the_newest_version_wins_in_pep_440_order_and_a_pin_gets_the_other(root: Path, all_sections: None) -> None:
    put(root, changed(BASES["nms"](), {"source.version": "0.9.0"}), "detectors/object_detectors/demo-old/demo.yaml")
    put(root, changed(BASES["nms"](), {"source.version": "0.10.0"}))
    assert [(entry.version, entry.superseded) for entry in onnx_entries(root)] == [("0.10.0", False), ("0.9.0", True)]
    assert get_detector(KEY, root).version == "0.10.0"
    assert get_detector(f"{KEY}==0.9.0", root).version == "0.9.0"
    assert describe_detector(f"{KEY}==0.9", root).entry.version == "0.9.0"
    with pytest.raises(DetectorNotFoundError, match="no version '1.0'"):
        get_detector(f"{KEY}==1.0", root)
    with pytest.raises(DetectorNotFoundError, match="no entry 'other@demo-exporter'"):
        get_detector("other@demo-exporter", root)


def test_a_version_that_is_not_pep_440_is_unavailable(root: Path, all_sections: None) -> None:
    put(root, changed(BASES["nms"](), {"source.version": "not a version"}))
    (entry,) = onnx_entries(root)
    assert not entry.available and "PEP 440" in entry.unavailable_reason


def test_one_key_and_version_with_different_bytes_is_unavailable_with_both_paths(root: Path, all_sections: None) -> None:
    first = put(root, BASES["nms"]())
    second = put(root, changed(BASES["nms"](), {"display_name": "Other"}), "detectors/object_detectors/demo-copy/demo.yaml")
    (entry,) = onnx_entries(root)
    assert not entry.available and not entry.artifact("n", "fp32").available
    assert str(first) in entry.unavailable_reason and str(second) in entry.unavailable_reason


def test_one_key_in_two_roots_uses_the_first_root_and_logs_it(tmp_path: Path, root: Path, caplog: pytest.LogCaptureFixture) -> None:
    package, other = tmp_path / "package", tmp_path / "other"
    used = put(package, BASES["nms"]())
    put(root, BASES["nms"]())
    put(other, BASES["nms"](), "demo.yaml")  # a folder with one sidecar and its files is also a root
    with caplog.at_level(logging.INFO, logger=catalog.logger.name):
        (found,) = scan_sidecar_roots(root, package_root=package, other_roots=[other])
    assert found.path == used and found.reason is None
    assert f"the catalog uses {used}" in caplog.text


def test_the_name_skellytracker_is_reserved_for_the_package_root(tmp_path: Path, root: Path, all_sections: None) -> None:
    ours = changed(BASES["nms"](), {"source.name": "skellytracker"})
    put(root, ours)
    (entry,) = onnx_entries(root)
    assert entry.key == "demo@skellytracker" and not entry.available and "reserved" in entry.unavailable_reason
    package = tmp_path / "package"
    put(package, ours)
    (found,) = scan_sidecar_roots(tmp_path / "empty", package_root=package)
    assert found.reason is None


def test_a_snapshot_of_symlinks_is_a_root(tmp_path: Path, root: Path, all_sections: None) -> None:
    blobs, snapshot = tmp_path / "hub" / "blobs", tmp_path / "hub" / "snapshots" / "0123abcd"
    path = put(tmp_path / "plain", BASES["nms"]())
    blobs.mkdir(parents=True)
    for index, file in enumerate(sorted(path.parent.iterdir())):
        link = snapshot / DEMO.rsplit("/", 1)[0] / file.name
        link.parent.mkdir(parents=True, exist_ok=True)
        blob = blobs / f"blob{index}"
        file.replace(blob)
        try:
            link.symlink_to(blob)
        except OSError:
            pytest.skip("this host cannot make a symlink")
    (found,) = scan_sidecar_roots(root, package_root=tmp_path / "empty", other_roots=[snapshot])
    assert found.reason is None and found.path == snapshot / DEMO and found.root == snapshot
    assert catalog._entry(found, artifacts.HashCache()).available


def test_a_long_path_with_non_ascii_characters_works_with_onnx_runtime(tmp_path: Path, all_sections: None) -> None:
    onnx = pytest.importorskip("onnx")
    import onnxruntime

    value = onnx.helper.make_tensor_value_info
    graph = onnx.helper.make_graph(
        [onnx.helper.make_node("Identity", ["input"], ["output"])],
        "tiny",
        [value("input", onnx.TensorProto.FLOAT, [3, 2])],
        [value("output", onnx.TensorProto.FLOAT, [3, 2])],
    )
    model = onnx.helper.make_model(graph, opset_imports=[onnx.helper.make_opsetid("", 13)], ir_version=8)
    root = tmp_path / ("Zoë Müller-Łukasiewicz 山田太郎 " + "n" * 24) / "models"
    path = put(root, BASES["nms"](), content=model.SerializeToString())
    (entry,) = onnx_entries(root)
    assert entry.available and entry.sidecar_path == path
    session = onnxruntime.InferenceSession(str(entry.artifact("n", "fp32").path), providers=["CPUExecutionProvider"])
    assert session.get_inputs()[0].shape == [3, 2]


# ---------------------------------------------------------------------------------------------
# describe_detector
# ---------------------------------------------------------------------------------------------


def test_describe_gives_the_sizes_the_ports_and_the_params_of_an_object_detector(root: Path, all_sections: None) -> None:
    path = put(root, BASES["nms"]())
    description = describe_detector(KEY, root)
    assert description.entry.sidecar_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert description.sizes == {"n": ("fp32",)} and description.point_names == ()
    assert [(port.name, port.direction, port.port_type) for port in description.ports] == [
        ("image", "input", "image"),
        ("boxes", "output", "boxes"),
    ]
    assert description.params["size"] == "n"
    decode = description.params["object_decode"]
    assert decode["selection"] == "nms" and decode["min_score"] == 0.7 and decode["nms"]["iou_threshold"] == 0.65


def test_describe_gives_the_point_names_and_the_ports_of_a_keypoint_model(root: Path) -> None:
    points_17 = BASES["packed"]()["keypoint"]["point_names"]
    write_yaml(root / "landmark_schemas" / "Demo3.yaml", {"name": "Demo3", "source": "test", "groups": [{"name": "body", "points": ["a", "b", "c"]}]})
    put(root, BASES["simcc"](), "detectors/keypoint_detectors/demo/body/demo-body.yaml")
    top_down = describe_detector("demo-body@demo-exporter", root)
    assert top_down.point_names == ("a", "b", "c") and top_down.params == {"size": "m"}
    assert [(port.name, port.direction) for port in top_down.ports] == [("image", "input"), ("boxes", "input"), ("keypoints", "output")]
    second = root.with_name("second")
    write_yaml(second / "landmark_schemas" / "Demo17.yaml", {"name": "Demo17", "source": "test", "groups": [{"name": "body", "points": points_17}]})
    put(second, BASES["packed"](), "detectors/keypoint_detectors/demo/body/demo-body.yaml")
    one_stage = describe_detector("demo-body@demo-exporter", second)
    assert [port.name for port in one_stage.ports] == ["image", "boxes", "keypoints"], one_stage.entry.unavailable_reason
    assert len(one_stage.point_names) == 17


def test_describe_of_an_entry_with_no_sidecar_or_with_a_bad_sidecar_has_only_the_entry(root: Path) -> None:
    calibration = describe_detector("charuco@skellytracker", root)
    assert calibration.entry.category == "calibration" and calibration.sizes == {} and calibration.ports == ()
    put(root, changed(BASES["nms"](), {"schema_version": "9.9.9"}))
    bad = describe_detector(KEY, root)
    assert not bad.entry.available and bad.sizes == {} and bad.params == {}
    with pytest.raises(DetectorNotFoundError, match="charuco@skellytracker"):
        describe_detector("nothing@nowhere", root)
