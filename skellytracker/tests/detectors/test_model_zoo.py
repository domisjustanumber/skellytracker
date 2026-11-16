"""The package sidecars of `core/model_zoo/`: their catalog entries, and one frame on each model.

Git does not track the ONNX files. A test that runs a model skips when its file is not present.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from skellytracker.core.detectors import catalog
from skellytracker.core.detectors.catalog import get_detector, load_detector_sidecar
from skellytracker.core.detectors.generic import create_detector
from skellytracker.core.model_spec import artifacts
from skellytracker.core.model_spec.landmark_schemas import PACKAGE_SIDECAR_ROOT

YOLOX = "yolox-person@openmmlab-exporter"
RTMW = "rtmw-wholebody133@openmmlab-exporter"
ROLES = {YOLOX: ("object_detector",), RTMW: ("keypoint_detector",)}


@pytest.fixture(autouse=True)
def private_folders(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    # One hash cache for the test run: the catalog hashes each present ONNX file one time.
    cache = tmp_path_factory.getbasetemp() / "model-zoo-hash-cache.json"
    monkeypatch.setattr(artifacts, "default_hash_cache_path", lambda: cache)
    monkeypatch.delenv(catalog.USER_ROOT_VARIABLE, raising=False)


def detector_or_skip(key: str, user_root: Path):  # noqa: ANN201
    entry = get_detector(key, user_root)
    if not entry.artifacts[0].downloaded:
        pytest.skip(f"the ONNX file {entry.artifacts[0].filename} is not in core/model_zoo/")
    return create_detector(key, execution_provider="cpu", user_root=user_root)


@pytest.mark.parametrize("key", [YOLOX, RTMW])
def test_a_package_sidecar_loads_and_is_in_the_catalog(key: str, tmp_path: Path) -> None:
    sidecar = load_detector_sidecar(key, tmp_path)  # no V- rule failure, and each section has its module
    entry = get_detector(key, tmp_path)
    assert entry.role == ROLES[key]
    assert entry.sidecar_root == PACKAGE_SIDECAR_ROOT
    assert sidecar.batching.batch == 3
    for artifact in entry.artifacts:  # a file that is present has the hash of the sidecar
        assert artifact.downloaded or "is not present" in artifact.unavailable_reason, artifact


def test_yolox_person_runs_one_frame_by_its_catalog_key(test_image: np.ndarray, tmp_path: Path) -> None:
    detector = detector_or_skip(YOLOX, tmp_path)
    (found,) = detector.detect([test_image])
    detector.close()
    height, width = test_image.shape[:2]
    assert len(found.scores) >= 1
    assert (found.scores > detector.decode.min_score).all()
    assert found.boxes.shape == (len(found.scores), 4)
    assert (found.boxes[:, 2] > found.boxes[:, 0]).all() and (found.boxes[:, 0] < width).all() and (found.boxes[:, 1] < height).all()
    assert (found.class_indices == 0).all()


def test_rtmw_wholebody133_runs_one_frame_by_its_catalog_key(test_image: np.ndarray, tmp_path: Path) -> None:
    detector = detector_or_skip(RTMW, tmp_path)
    height, width = test_image.shape[:2]
    found = detector.detect([test_image], [(width / 2, height / 2, width, height, 0.0)])
    detector.close()
    assert found.keypoints.shape == (1, 133, 2)
    assert found.scores.shape == (1, 133)
    present = ~np.isnan(found.keypoints).any(-1)
    assert present.sum() > 100
    assert (found.scores[present] > 0).all()
