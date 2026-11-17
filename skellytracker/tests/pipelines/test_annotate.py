"""Tests of the generic annotator: it draws the delivered values `CanonicalKeypoints` and `OutputBoxes`."""
import numpy as np

from skellytracker.core.pipelines.annotate import annotate
from skellytracker.core.pipelines.canonical import CanonicalKeypoints
from skellytracker.core.pipelines.values import OutputBoxes

NAMES = ("body/a", "body/b", "body/c")
SCHEMA = {
    "wholebody": {"port_type": "keypoints", "point_names": list(NAMES), "edges": [["body/a", "body/b"], ["body/b", "body/c"]]},
    "boxes": {"port_type": "boxes", "class_names": ["person", None]},
}
FIXED = {"frame_index": 0, "image_width": 64, "image_height": 48, "timestamp_ms": None, "node_ran": {"model": True}}


def image() -> np.ndarray:
    return np.zeros((48, 64, 3), dtype=np.uint8)


def keypoints(rows: int = 2, present: bool = True) -> CanonicalKeypoints:
    value = CanonicalKeypoints(NAMES, np.full((rows, 3, 2), np.nan), np.zeros((rows, 3)), (), np.zeros(rows, bool), np.zeros(rows))
    if present:
        value.xy[0, :2] = [[10.0, 10.0], [40.0, 30.0]]  # `body/c` is missing
        value.score[0, :2] = [0.9, 0.2]
        value.present[0] = True
    return value


def boxes(rows: int = 2, present: bool = True) -> OutputBoxes:
    """Row 0 is a detector box with a class: the annotator writes its label. Row 1 has no class."""
    value = OutputBoxes(np.full((rows, 4), np.nan), np.zeros(rows), np.full(rows, -1, dtype=np.int64), np.zeros(rows, bool), np.zeros(rows, bool))
    if present:
        value.xyxy[0], value.score[0], value.class_index[0], value.present[0] = [5.0, 15.0, 30.0, 40.0], 0.8, 1, True
        value.xyxy[1], value.present[1] = [22.0, 19.0, 42.0, 29.0], True
    return value


def test_it_draws_each_delivered_form_and_keeps_the_input_image():
    source = image()
    for name, value in (("wholebody", keypoints()), ("boxes", boxes())):
        drawn = annotate(source, {**FIXED, name: value}, SCHEMA)
        assert drawn.shape == source.shape and drawn.dtype == np.uint8
        assert drawn.any(), name
    assert not source.any()
    drawn = annotate(source, {**FIXED, "wholebody": keypoints(), "boxes": boxes()}, SCHEMA)
    assert drawn[15, 5:30].any() and drawn[29, 22:42].any()  # the top edge of row 0 and the bottom edge of row 1


def test_min_score_hides_a_point_and_its_edges():
    high = annotate(image(), {**FIXED, "wholebody": keypoints()}, SCHEMA, min_score=0.5)
    assert high[10, 10].any() and not high[30, 40].any() and not high[20, 25].any()
    low = annotate(image(), {**FIXED, "wholebody": keypoints()}, SCHEMA)
    assert low[30, 40].any() and low[20, 25].any()  # (25, 20) is on the edge from a to b


def test_empty_values_and_nan_points_draw_nothing():
    present_nan, nan_box = keypoints(1, present=False), boxes(1, present=False)
    present_nan.present[0] = nan_box.present[0] = True
    for result in (
        FIXED,
        {**FIXED, "wholebody": keypoints(2, present=False), "boxes": boxes(2, present=False)},
        {**FIXED, "wholebody": present_nan, "boxes": nan_box},
        {**FIXED, "other": keypoints()},  # a key with no schema
    ):
        assert not annotate(image(), result, SCHEMA).any()
