"""Parity test A of the built-in `yolox-rtmw-wholebody`: the box logic against the recording of the branch sfn26.

The fixture `data/sfn26_box_parity.npz` holds the values of the old tracker for each frame
(`decisions/scripts/record_sfn26_box_parity.py`, ADR-RA0E). The test runs the graph of the built-in
through `start_pipeline`. Only the model call of the two `onnx_model` nodes is replaced: the
detectors give the recorded YOLOX box and the recorded keypoints of the frame. The executor runs
each node under its normal rules. The test needs no ONNX file and no session.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from skellytracker.core.detectors import catalog
from skellytracker.core.model_spec import artifacts
from skellytracker.core.pipelines import Frame, load_pipeline, start_pipeline
from skellytracker.core.pipelines._runtime import sessions
from skellytracker.core.pipelines._runtime.executor import Executor
from skellytracker.core.pipelines._runtime.onnx_model import OnnxModelRunner

FIXTURE = Path(__file__).parent / "data" / "sfn26_box_parity.npz"
BUILT_IN = "yolox-rtmw-wholebody@skellytracker"


def roi_to_xyxy(roi: np.ndarray) -> np.ndarray:
    """Return `x1, y1, x2, y2` of one ROI row `(cx, cy, w, h, rotation)` with no rotation."""
    cx, cy, w, h = (float(value) for value in roi[:4])
    return np.array([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2])


def clip_to_pixels(xyxy: np.ndarray, width: int, height: int) -> list[int]:
    """Clip a box to whole pixels with the rule of the old code: a clamp to the image, then `int()` (toward zero).

    `width` and `height` are `image_width` and `image_height` of the result of a camera.
    """
    return [int(min(max(0.0, float(value)), float(limit))) for value, limit in zip(xyxy, (width, height, width, height), strict=True)]


class RecordedDetector:
    """The model call of one `onnx_model` node: it gives the recorded values of the frame `frame["k"]`."""

    def __init__(self, data: Any, frame: dict[str, int]) -> None:
        self.data, self.frame = data, frame

    def detect(self, images: Any, rois: Any = None, timer: Any = None) -> Any:
        k = self.frame["k"]
        if rois is None:  # the object detector: one result for each image
            found = bool(self.data["yolox_found"][k])
            return [SimpleNamespace(
                boxes=self.data["yolox_box"][k : k + 1][:found], scores=self.data["yolox_score"][k : k + 1][:found],
                class_indices=np.zeros(int(found), dtype=np.int64),
            )]
        assert len(rois) == 1  # one camera, one person
        scores = self.data["keypoints_score"][k : k + 1]  # the recording has one score: it serves as the raw score too
        return SimpleNamespace(keypoints=self.data["keypoints_xy"][k : k + 1], scores=scores, raw_scores=scores)

    def close(self) -> None:
        pass


@pytest.fixture
def recorded(monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, dict[str, int]]:
    """Replace the session start of the run: each `onnx_model` node gets a `RecordedDetector`, and no ONNX file is needed."""
    data = np.load(FIXTURE, allow_pickle=False)
    frame = {"k": 0}
    # The load writes no hash cache in a user folder, and reads no user root.
    monkeypatch.setattr(artifacts, "default_hash_cache_path", lambda: tmp_path_factory.getbasetemp() / "model-zoo-hash-cache.json")
    monkeypatch.delenv(catalog.USER_ROOT_VARIABLE, raising=False)

    def open_sessions(self: Executor) -> dict[str, list[Any]]:
        for node_id in self.order:
            node = self.resolved.nodes[node_id]
            if node.type == "onnx_model":
                runner = object.__new__(OnnxModelRunner)  # the real rows of the node, with no detector of a session
                runner.kind, runner.outputs_info, runner.detectors = node.model.kind, node.outputs_info, [RecordedDetector(data, frame)]
                self.models[node_id] = runner
        return {}

    monkeypatch.setattr(Executor, "_open_sessions", open_sessions)
    monkeypatch.setattr(sessions, "check_dependencies", lambda *args, **kwargs: None)  # the ONNX files can be absent
    return data, frame


def test_the_box_logic_of_the_built_in_agrees_with_the_recording_of_sfn26(recorded: tuple[Any, dict[str, int]]) -> None:
    data, frame = recorded
    height, width = (int(value) for value in data["image_size"])
    image = np.zeros((height, width, 3), np.uint8)
    differences: list[str] = []
    with start_pipeline(load_pipeline(BUILT_IN), camera_ids=[0], running_mode="video", execution_provider="cpu") as run:
        for k in range(len(data["frame_index"])):
            frame["k"] = k
            result = run.process(Frame(image, int(data["frame_index"][k]), float(data["timestamp_ms"][k])))
            assert (result["image_width"], result["image_height"]) == (width, height)
            roi = result["person_roi"]
            if result["node_ran"]["person"] != data["detector_ran"][k]:
                differences.append(f"frame {k}: node_ran.person is {result['node_ran']['person']}, detector_ran is {data['detector_ran'][k]}")
            # The old tracker runs RTMW exactly on the frames with a box, and the node `wholebody` stops on an empty ROI.
            if result["node_ran"]["wholebody"] != data["keypoints_ran"][k]:
                differences.append(f"frame {k}: node_ran.wholebody is {result['node_ran']['wholebody']}, keypoints_ran is {data['keypoints_ran'][k]}")
            if bool(roi.present[0]) != data["box_present"][k]:
                differences.append(f"frame {k}: person_roi present is {bool(roi.present[0])}, box_present is {data['box_present'][k]}")
            elif roi.present[0]:
                xyxy = roi_to_xyxy(roi.rois[0])
                error = float(np.abs(xyxy - data["smoothed_box"][k]).max())
                if not error <= 1e-6:
                    differences.append(f"frame {k}: person_roi {xyxy.tolist()} differs from smoothed_box {data['smoothed_box'][k].tolist()} by {error} px")
                clip = clip_to_pixels(xyxy, result["image_width"], result["image_height"])
                if clip != data["bounding_box"][k].tolist():
                    differences.append(f"frame {k}: the clip {clip} is not {data['bounding_box'][k].tolist()}")
    assert not differences, f"{len(differences)} differences, the first 10:\n" + "\n".join(differences[:10])
