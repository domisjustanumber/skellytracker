"""Small models for the pipeline tests: a temporary sidecar root with an object detector and a top-down keypoint model.

    root = write_models(tmp_path / "user")                 # the sidecars, with ONNX files that are not graphs
    root = write_models(tmp_path / "user", graphs=True)    # with ONNX graphs that give known outputs (needs `onnx`)
    config = load_pipeline(detector_pipeline(), user_root=root)

A load needs only the sidecars and the hashes of the files. A run needs `graphs=True`. Call
`isolate` first, so that a test writes no hash cache and no download in a user folder.

The object detector `demo@demo-exporter` (size `n`, 32 x 32) gives three rows for each image:
`onnx_models.BOXES` with the scores `onnx_models.SCORES` times the mean of the image. Row 1
overlaps row 0, so the sidecar NMS (IoU 0.5) keeps the rows 0 and 2. The keypoint model
`demo-body@demo-exporter` (size `m`, 16 x 12, schema `Demo3`, points `a`, `b`, `c`) gives `a` at the
centre of the crop with the raw score 3, `b` at the top-left corner with the raw score 2, and no `c`.
The score map `SCORE_MAP` gives the scores `KEYPOINT_SCORES`.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import pytest

from skellytracker.core.detectors import catalog
from skellytracker.core.model_spec import artifacts
from skellytracker.tests.model_spec.sidecars import BASES, SCORE_MAP, _size, write_yaml

OBJECT_KEY = "demo@demo-exporter"
KEYPOINT_KEY = "demo-body@demo-exporter"
KEYPOINT_SCORES = [1 / (1 + math.exp(-3.0)), 1 / (1 + math.exp(-2.0)), 0.0]
"""The mapped scores of `a`, `b` and `c`: `1 / (1 + exp(-raw))` of the raw scores 3 and 2, and 0 for a missing point."""
KEYPOINT_RAW_SCORES = [3.0, 2.0, 0.0]
"""The raw scores of `a`, `b` and `c`: the decode scores before the map, and 0 for a missing point."""
SCHEMA = {"name": "Demo3", "source": "test", "groups": [{"name": "body", "points": ["a", "b", "c"]}]}
"""The landmark schema of the keypoint model: one group, so its group in a pipeline has the id of the node."""


def isolate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Put the hash cache and the download folder in `tmp_path`, and remove the user root variable."""
    monkeypatch.setattr(artifacts, "default_hash_cache_path", lambda: tmp_path / "cache" / "hash-cache.json")
    monkeypatch.setattr(artifacts, "download_root", lambda: tmp_path / "cache" / "models")
    monkeypatch.delenv(catalog.USER_ROOT_VARIABLE, raising=False)


def object_sidecar() -> dict[str, Any]:
    """The sidecar of the object detector: `selection: nms`, one class `person`, three rows (`Q` = 3)."""
    sidecar = BASES["nms"]()
    sidecar["object"]["decode"]["nms"] = {"iou_threshold": 0.5, "score_threshold": 0.01}
    sidecar["sizes"] = {"n": _size("demo", "n", 32, 32, [[3, 3, 4], [3, 3]])}
    return sidecar


def keypoint_sidecar() -> dict[str, Any]:
    """The sidecar of the top-down keypoint model: SimCC, the schema `Demo3`, the edges a-b and b-c."""
    sidecar = BASES["simcc"]()
    sidecar["keypoint"]["derived_points"] = {"mid": ["a", "b"]}
    sidecar["sizes"] = {"m": {**_size("demo-body", "m", 16, 12, [[3, 3, 24], [3, 3, 32]]), "score_map": dict(SCORE_MAP)}}
    return sidecar


def write_sidecar(root: Path, sidecar: dict[str, Any], content: bytes = b"not a graph", files: bool = True) -> str:
    """Write one sidecar in `root` with the hash of `content` for each artifact. Return the SHA-256 of the sidecar file.

    With `files`, each ONNX file of the sidecar holds `content`. A keypoint sidecar also gets the
    schema file `Demo3`.
    """
    kind = "keypoint_detectors/demo/body" if "keypoint" in sidecar else "object_detectors/demo"
    folder = root / "detectors" / kind
    folder.mkdir(parents=True, exist_ok=True)
    if "keypoint" in sidecar:
        write_yaml(root / "landmark_schemas" / "Demo3.yaml", SCHEMA)
    for size in sidecar["sizes"].values():
        for artifact in size["onnx"]["precision_artifacts"].values():
            artifact["sha256"] = hashlib.sha256(content).hexdigest()
            if files:
                (folder / artifact["filename"]).write_bytes(content)
    return write_yaml(folder / f"{sidecar['model_id']}.yaml", sidecar)


def write_models(root: Path, *, graphs: bool = False, files: bool = True) -> Path:
    """Write the two models in the sidecar root `root`, and return `root`.

    With `graphs`, each ONNX file is a batch-3 graph of `tests/detectors/onnx_models.py`, which
    needs the package `onnx`. Without `files`, the root has no ONNX file.
    """
    object_content = keypoint_content = b"not a graph"
    if graphs:
        from skellytracker.tests.detectors.onnx_models import keypoint_model, object_model

        object_content, keypoint_content = object_model(), keypoint_model()
    write_sidecar(root, object_sidecar(), object_content, files)
    write_sidecar(root, keypoint_sidecar(), keypoint_content, files)
    return root


def detector_pipeline(**person_params: Any) -> dict[str, Any]:
    """Return the config of the two models: `person` gives the ROIs of `body`.

    `person_params` are more params of the node `person`, for example `max_instances=2`. The
    outputs are `body` (keypoints, the group `body`), `person_box` and `person_roi`.
    """
    return {
        "schema_version": "2.0.0",
        "pipeline_id": "demo-models",
        "source": {"name": "demo-source", "version": "1.0.0"},
        "nodes": [
            {"id": "person", "type": "onnx_model", "inputs": {"image": "frame.image"},
             "params": {"key": OBJECT_KEY, "size": "n", "execution_provider": "cpu", **person_params}},
            {"id": "body", "type": "onnx_model", "inputs": {"image": "frame.image", "rois": "person.rois"},
             "params": {"key": KEYPOINT_KEY, "size": "m", "execution_provider": "cpu"}},
        ],
        "outputs": {"body": "body.keypoints", "person_box": "person.detections", "person_roi": "person.rois"},
    }


def image(value: int, height: int = 32, width: int = 32) -> Any:
    """Return a BGR frame with one value. The scores of the object model are `onnx_models.SCORES` times `value`: 0 gives no detection."""
    import numpy as np

    return np.full((height, width, 3), value, np.uint8)


def tracking_pipeline() -> dict[str, Any]:
    """Return a config with the two models and each glue node type, in the form of `yolox-rtmw-wholebody`.

    The detector runs on the first frame and then each 3 frames. `hand` is a second node of the
    keypoint model, so the two nodes can share one session. The outputs are `body`, `both`
    (`concat`), `merged` (`merge`), `smooth`, `person_box` and `person_roi` (the crop ROI).
    """
    cpu = {"execution_provider": "cpu"}
    nodes = [
        {"id": "trigger", "type": "redetect_trigger",
         "inputs": {"image": "frame.image", "previous_keypoints": "body.keypoints@prev", "previous_rois": "crop.rois@prev"},
         "params": {"redetect_interval": 3, "fitness_checks": [{"check": "roi_missing"}]}},
        {"id": "person", "type": "onnx_model", "inputs": {"image": "trigger.image"}, "params": {"key": OBJECT_KEY, "size": "n", **cpu}},
        {"id": "detected_box", "type": "first_of", "inputs": ["person.rois", "detected_box.value@prev"]},
        {"id": "points_box", "type": "roi_from_points",
         "inputs": {"keypoints": "body.keypoints@prev", "previous_rois": "crop.rois@prev", "reference_rois": "detected_box.value"},
         "params": {"expand_ratio": 1.2}},
        {"id": "carried_box", "type": "gate", "inputs": {"value": "points_box.rois", "condition": "trigger.image"}, "params": {"mode": "is_empty"}},
        {"id": "box", "type": "first_of", "inputs": ["person.rois", "carried_box.value"]},
        {"id": "hold", "type": "roi_hold", "inputs": {"previous": "crop.rois@prev", "current": "box.value"}},
        {"id": "crop", "type": "smooth_roi", "inputs": {"rois": "hold.rois"}},
        {"id": "body", "type": "onnx_model", "inputs": {"image": "frame.image", "rois": "crop.rois"}, "params": {"key": KEYPOINT_KEY, "size": "m", **cpu}},
        {"id": "hand", "type": "onnx_model", "inputs": {"image": "frame.image", "rois": "crop.rois"}, "params": {"key": KEYPOINT_KEY, "size": "m", **cpu}},
        {"id": "both", "type": "concat", "inputs": ["body.keypoints", "hand.keypoints"]},
        {"id": "merged", "type": "merge", "inputs": {"target": "body.keypoints", "source": "hand.keypoints"},
         "params": {"slots": {"extra": "body/a"}, "source_anchor": "hand/a", "max_distance": 10.0}},
        {"id": "smooth", "type": "smooth_keypoints", "inputs": {"keypoints": "both.keypoints"}},
    ]
    outputs = {
        "body": "body.keypoints", "both": "both.keypoints", "merged": "merged.keypoints", "smooth": "smooth.keypoints",
        "person_box": "person.detections", "person_roi": "crop.rois",
    }
    return {
        "schema_version": "2.0.0", "pipeline_id": "demo-tracking", "source": {"name": "demo-source", "version": "1.0.0"},
        "nodes": nodes, "outputs": outputs,
    }
