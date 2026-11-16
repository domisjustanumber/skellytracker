"""Tests of the generic annotator."""
import numpy as np

from skellytracker.core.pipelines.annotate import annotate
from skellytracker.core.pipelines.values import InstanceBoxes, InstanceKeypoints, InstanceRois

SCHEMA = {
    "points": {"port_type": "keypoints", "point_names": ["body/a", "body/b", "body/c"], "edges": [["body/a", "body/b"], ["body/b", "body/c"]]},
    "boxes": {"port_type": "detections", "class_names": ["person", None]},
    "crop": {"port_type": "roi"},
}
FIXED = {"frame_index": 0, "image_width": 64, "image_height": 48, "timestamp_ms": None, "node_ran": {"model": True}}


def image() -> np.ndarray:
    return np.zeros((48, 64, 3), dtype=np.uint8)


def keypoints() -> InstanceKeypoints:
    value = InstanceKeypoints.empty(("body/a", "body/b", "body/c"), 2)
    value.xy[0, :2] = [[10.0, 10.0], [40.0, 30.0]]  # `body/c` is missing
    value.score[0, :2] = [0.9, 0.2]
    value.present[0] = True
    return value


def boxes() -> InstanceBoxes:
    value = InstanceBoxes.empty(2)
    value.xyxy[0], value.score[0], value.class_index[0], value.present[0] = [5.0, 15.0, 30.0, 40.0], 0.8, 1, True
    return value


def rois() -> InstanceRois:
    value = InstanceRois.empty(2)
    value.rois[0], value.present[0] = [32.0, 24.0, 20.0, 10.0, 0.5], True
    return value


def test_it_draws_each_port_type_and_keeps_the_input_image():
    source = image()
    for name, value in (("points", keypoints()), ("boxes", boxes()), ("crop", rois())):
        drawn = annotate(source, {**FIXED, name: value}, SCHEMA)
        assert drawn.shape == source.shape and drawn.dtype == np.uint8
        assert drawn.any(), name
    assert not source.any()
    drawn = annotate(source, {**FIXED, "points": keypoints(), "boxes": boxes(), "crop": rois()}, SCHEMA)
    assert drawn.any()


def test_min_score_hides_a_point_and_its_edges():
    high = annotate(image(), {**FIXED, "points": keypoints()}, SCHEMA, min_score=0.5)
    assert high[10, 10].any() and not high[30, 40].any() and not high[20, 25].any()
    low = annotate(image(), {**FIXED, "points": keypoints()}, SCHEMA)
    assert low[30, 40].any() and low[20, 25].any()  # (25, 20) is on the edge from a to b


def test_empty_values_and_nan_points_draw_nothing():
    present_nan = InstanceKeypoints.empty(("body/a", "body/b", "body/c"), 1)
    present_nan.present[0] = True
    nan_box, nan_roi = InstanceBoxes.empty(1), InstanceRois.empty(1)
    nan_box.present[0] = nan_roi.present[0] = True
    for result in (
        FIXED,
        {**FIXED, "points": InstanceKeypoints.empty(("body/a", "body/b", "body/c"), 2), "boxes": InstanceBoxes.empty(2), "crop": InstanceRois.empty(2)},
        {**FIXED, "points": present_nan, "boxes": nan_box, "crop": nan_roi},
        {**FIXED, "points": None, "other": keypoints()},  # an empty image value, and a key with no schema
    ):
        assert not annotate(image(), result, SCHEMA).any()
