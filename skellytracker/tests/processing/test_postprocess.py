"""The spec postprocessing modules of `processing/post/`: the unprojection, the decodes and the keypoint rules.

`tools/tests/test_package_vectors.py` runs the numeric vector cases of each section. These tests cover the
array forms, the run-time rules of a keypoint and the cases that the vector test does not run.
"""
from __future__ import annotations

import numpy as np
import pytest

from skellytracker.core.detectors.processing.post.keypoint_decode_simcc import decode_simcc
from skellytracker.core.detectors.processing.post.keypoint_schema import derived_points, mark_missing
from skellytracker.core.detectors.processing.post.keypoint_score_map import map_scores
from skellytracker.core.detectors.processing.post.object_decode import (
    confidence_mask,
    filter_classes,
    score_order,
    to_xyxy,
    unproject_and_filter,
)
from skellytracker.core.detectors.processing.post.object_selection_nms import decode_nms
from skellytracker.core.detectors.processing.post.unprojection import resize_inverse, unproject_boxes, unproject_points
from skellytracker.core.detectors.processing.pre.preprocess import resize_geometry
from skellytracker.core.model_spec.model import KeypointSpec, ObjectDecodeSpec, ResizeSpec, ScoreMapSpec

RESIZES = [
    (ResizeSpec(method="letterbox", pad_position="center", rounding="half_even"), [64, 64], None),
    (ResizeSpec(method="stretch"), [64, 32], None),
    (ResizeSpec(method="fit", pad_value=0), [64, 64], None),
    (ResizeSpec(method="none"), None, None),
    (ResizeSpec(method="affine_crop"), [64, 48], [100.0, 60.0, 40.0, 50.0, 0.4]),
]


@pytest.mark.parametrize(("resize", "target_size", "roi"), RESIZES, ids=[row[0].method for row in RESIZES])
def test_the_inverse_of_each_method_takes_the_model_image_of_a_source_point_back(resize, target_size, roi) -> None:
    geometry = resize_geometry(resize, target_size, 200, 120, roi)
    source = np.array([[0.0, 0.0], [200.0, 120.0], [77.0, 31.5]])
    values = geometry.values
    forward = {
        "letterbox": lambda: source * [values["n_w"] / 200, values["n_h"] / 120] + [values["left"], values["top"]],
        "stretch": lambda: source * [32 / 200, 64 / 120],
        "fit": lambda: source * values["scale"] + [values["left"], values["top"]],
        "none": lambda: source,
        "affine_crop": lambda: source @ values["matrix"][:, :2].T + values["matrix"][:, 2],
    }[resize.method]()
    assert resize_inverse(forward, geometry) == pytest.approx(source)
    assert resize_inverse(forward, geometry).dtype == np.float64


def test_the_unprojection_converts_the_coordinate_space_first_and_takes_arrays() -> None:
    geometry = resize_geometry(ResizeSpec(method="stretch"), [64, 32], 320, 640)
    pixel = unproject_points([[16.0, 32.0], [32.0, 64.0]], "pixel", geometry)
    assert pixel.tolist() == [[160.0, 320.0], [320.0, 640.0]]
    assert unproject_points([[0.5, 0.5], [1.0, 1.0]], "normalized_01", geometry).tolist() == pixel.tolist()
    assert unproject_points([[0.0, 0.0], [1.0, 1.0]], "normalized_11", geometry).tolist() == pixel.tolist()
    boxes = unproject_boxes(np.array([[[0.0, 0.0, 16.0, 32.0]], [[16.0, 32.0, 32.0, 64.0]]]), "pixel", geometry)
    assert boxes.shape == (2, 1, 4) and boxes[1, 0].tolist() == [160.0, 320.0, 320.0, 640.0]
    with pytest.raises(ValueError, match="coordinate space"):
        unproject_points([[0.0, 0.0]], "normalized", geometry)


# ---------------------------------------------------------------------------
# The object decode
# ---------------------------------------------------------------------------


def test_the_shared_steps_of_the_object_decode() -> None:
    assert score_order([0.5, 0.9, 0.5, 0.9]).tolist() == [1, 3, 0, 2]
    assert to_xyxy([10, 20, 4, 6], "xywh").tolist() == [10, 20, 14, 26]
    assert to_xyxy([10, 20, 4, 6], "cxcywh").tolist() == [8, 17, 12, 23]
    # Half to even, a gap, an index outside the list and keep_classes.
    indexes = np.array([0.5, 1.5, 1.0, 3.0, -1.0], dtype=np.float32)
    assert filter_classes(indexes, ["a", None, "c"], None).tolist() == [0, 2, -1, -1, -1]
    assert filter_classes(indexes, ["a", None, "c"], ["c"]).tolist() == [-1, 2, -1, -1, -1]
    # The comparison is strict and in float32: 0.7 as float32 is not more than the float32 of 0.7.
    assert confidence_mask([np.float32(0.7), 0.7000001], 0.7).tolist() == [False, True]


def test_the_clamp_runs_only_when_clamp_boxes_is_true_and_min_score_can_come_from_the_caller() -> None:
    geometry = resize_geometry(ResizeSpec(method="none"), None, 100, 50)
    boxes, scores = [[-10.0, -10.0, 120.0, 60.0], [10.0, 10.0, 12.0, 40.0]], [0.9, 0.6]
    decode = ObjectDecodeSpec(selection="none", min_box_size=5)
    positions, kept = unproject_and_filter(boxes, scores, decode, geometry)
    assert positions.tolist() == [0] and kept.tolist() == [[0.0, 0.0, 100.0, 50.0]]
    unclamped = ObjectDecodeSpec(selection="none", clamp_boxes=False)
    positions, kept = unproject_and_filter(boxes, scores, unclamped, geometry, min_score=0.5)
    assert positions.tolist() == [0, 1] and kept[0].tolist() == boxes[0]
    # With no geometry, the boxes stay in model-input pixels: no clamp and no size filter.
    positions, kept = unproject_and_filter(boxes, scores, decode, None, min_score=0)
    assert positions.tolist() == [0, 1] and kept.tolist() == boxes


def test_decode_nms_gives_source_boxes_in_score_order() -> None:
    decode = ObjectDecodeSpec(
        selection="nms", box_format="cxcywh", box_space="normalized_01", min_score=0.3,
        nms={"iou_threshold": 0.5, "score_threshold": 0.1}, keep_classes=["person"],
    )
    geometry = resize_geometry(ResizeSpec(method="stretch"), [100, 100], 200, 400)
    boxes = np.array([[0.5, 0.5, 0.2, 0.2], [0.5, 0.5, 0.2, 0.22], [0.2, 0.2, 0.1, 0.1], [0.8, 0.8, 0.1, 0.1]], np.float32)
    scores = np.array([0.8, 0.9, 0.95, 0.2], dtype=np.float32)
    found = decode_nms(boxes, scores, np.array([0, 0, 1, 0]), decode, ["person", "car"], (100, 100), geometry)
    assert found["rows"].tolist() == [1]  # row 0 overlaps row 1, row 2 is a car, row 3 is below min_score
    assert found["class_indices"].tolist() == [0]
    assert found["boxes"].tolist() == [pytest.approx([80.0, 156.0, 120.0, 244.0])]
    no_source = decode_nms(boxes, scores, None, decode.model_copy(update={"keep_classes": None}), ["person"], (100, 100), None)
    assert no_source["rows"].tolist() == [2, 1] and no_source["class_indices"].tolist() == [0, 0]


# ---------------------------------------------------------------------------
# The keypoint rules
# ---------------------------------------------------------------------------


def test_simcc_reads_the_bin_scale_from_the_bin_counts_and_takes_no_softmax() -> None:
    simcc_x = np.zeros((1, 2, 8), dtype=np.float32)
    simcc_y = np.zeros((1, 2, 16), dtype=np.float32)
    simcc_x[0, 0, 6], simcc_y[0, 0, 4] = 3.0, 5.0
    result = decode_simcc(simcc_x, simcc_y, (32, 24))
    assert result["scores"].tolist() == [[3.0, 0.0]]  # min(peak_x, peak_y), raw values
    assert result["bins"].tolist() == [[[6, 4], [-1, -1]]]
    assert result["keypoints"].tolist() == [[[6 * 24 / 8, 4 * 32 / 16], [-24 / 8, -32 / 16]]]


def test_a_keypoint_with_a_score_at_or_below_zero_or_a_nan_score_is_missing() -> None:
    keypoints = np.arange(10, dtype=np.float64).reshape(1, 5, 2)
    scores = np.array([[0.5, 0.0, -0.2, np.nan, 1e-9]], dtype=np.float32)
    points, marked = mark_missing(keypoints, scores)
    assert marked.tolist() == [[0.5, 0.0, 0.0, 0.0, pytest.approx(1e-9)]]
    assert np.isnan(points[0, 1:4]).all() and not np.isnan(points[0, [0, 4]]).any()
    assert np.array_equal(keypoints, np.arange(10).reshape(1, 5, 2))  # the input does not change
    integer_points, _ = mark_missing(np.ones((1, 2), dtype=np.int64), np.zeros(1, dtype=np.float32))
    assert np.isnan(integer_points).all()


def test_the_derived_points_of_a_loaded_keypoint_block() -> None:
    spec = KeypointSpec.model_validate(
        {
            "estimator_type": "bottom_up",
            "geometry": "2d",
            "landmark_schema": "Demo",
            "point_names": ["nose", "l_hip", "r_hip", "l_a", "l_b"],
            "skeletons": [],
            "decode": {"method": "coordinate"},
            "derived_points": {
                "prefixes": ["l_"],
                "nose_dup": "nose",
                "mid_hip": ["l_hip", "r_hip"],
                "past_hip": {"l_hip": 2.0, "r_hip": -1.0},
                "[prefix]mid": ["a", "b"],
            },
        }
    )
    assert list(spec.derived_points) == ["nose_dup", "mid_hip", "past_hip", "l_mid"]
    keypoints = np.array([[[1.0, 2.0], [10.0, 0.0], [20.0, 4.0], [0.0, 0.0], [5.0, 5.0]]])
    keypoints = np.concatenate([keypoints, keypoints])
    scores = np.array([[0.9, 0.8, 0.6, 0.7, 0.2], [0.9, 0.8, 0.0, 0.7, 0.2]])
    keypoints, scores = mark_missing(keypoints, scores)
    points, derived_scores = derived_points(keypoints, scores, spec.point_names, spec.derived_points)
    assert points.shape == (2, 4, 2) and derived_scores.shape == (2, 4)
    assert points[0].tolist() == [[1.0, 2.0], [15.0, 2.0], [0.0, -4.0], [2.5, 2.5]]
    assert derived_scores[0].tolist() == [0.9, 0.6, 0.6, 0.2]
    # In the second instance, r_hip is missing: each point with that source is missing.
    assert derived_scores[1].tolist() == [0.9, 0.0, 0.0, 0.2]
    assert np.isnan(points[1, 1:3]).all() and points[1, [0, 3]].tolist() == [[1.0, 2.0], [2.5, 2.5]]


def test_the_score_map_saturates_with_no_floating_point_warning() -> None:
    """post.keypoint.score_map: an extreme z gives 0 or 1, never NaN, and raises no warning."""
    score_map = ScoreMapSpec(method="logistic", a=1e30, b=-1e30)
    raw = np.array([[3.4e38, 1e-30, np.inf, np.nan, -np.inf, 0.0]], dtype=np.float32)
    with np.errstate(all="raise"):
        scores = map_scores(raw, score_map, None)
    assert scores.dtype == np.float32 and scores.tolist() == [[1.0, 0.0, 1.0, 0.0, 0.0, 0.0]]
    assert map_scores(np.zeros((0, 6), np.float32), score_map, None).shape == (0, 6)
    with np.errstate(all="raise"):  # a * raw overflows float64 here
        assert map_scores(raw[:, :1], ScoreMapSpec(method="logistic", a=1e300, b=0.0), None).tolist() == [[1.0]]


def test_a_mapped_score_of_zero_keeps_a_derived_point_when_its_sources_are_present() -> None:
    """A present keypoint can map to 0.0 in float32. `present` keeps its derived point."""
    points = np.array([[[0.0, 0.0], [2.0, 2.0]]])
    mapped = np.array([[0.0, 0.5]], dtype=np.float32)
    derived, scores = derived_points(points, mapped, ["a", "b"], {"mid": ["a", "b"]}, present=np.array([[True, True]]))
    assert derived.tolist() == [[[1.0, 1.0]]] and scores.tolist() == [[0.0]]
    missing, _ = derived_points(points, mapped, ["a", "b"], {"mid": ["a", "b"]})
    assert np.isnan(missing).all()  # with no `present`, a score 0 is a missing source
