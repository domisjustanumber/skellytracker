"""Tests of the canonical form (pipeline.outputs Behaviour item 7; post.keypoint.canonical_mapping)."""
import numpy as np
import pytest

from skellytracker.core.model_spec.landmark_schemas import load_landmark_schema_registry
from skellytracker.core.pipelines.canonical import canonical_names, to_canonical
from skellytracker.core.pipelines.values import Group, InstanceKeypoints

HAND_SCHEMA = """\
name: Test_Hand
source: test
groups:
  - name: hand
    points: [root, tip]
canonical_mapping:
  hand:
    wrist: root
    middle: {root: 0.25, tip: 0.75}
"""


def wholebody() -> tuple[InstanceKeypoints, dict]:
    """A value with 2 rows of the 133 points of `COCO_WholeBody`, and its output schema."""
    schema = load_landmark_schema_registry()["COCO_WholeBody"]
    groups, names, start = [], [], 0
    for group in schema.groups:
        groups.append({"name": group.name, "start": start, "count": len(group.points), "landmark_schema": "COCO_WholeBody"})
        names += [f"{group.name}/{point}" for point in group.points]
        start += len(group.points)
    xyz = np.arange(2 * 133 * 3, dtype=np.float64).reshape(2, 133, 3)
    score = np.linspace(0.1, 1.0, 2 * 133).reshape(2, 133)
    value = InstanceKeypoints(tuple(names), xyz, score, np.ones(2), np.ones(2, dtype=bool), np.full(2, -1, dtype=np.int64))
    return value, {"port_type": "keypoints", "point_names": names, "groups": groups, "canonical_names": canonical_names(groups, names)}


def test_coco_wholebody_has_137_canonical_names_and_no_feet_column():
    value, output_schema = wholebody()
    names = output_schema["canonical_names"]
    assert len(names) == 137
    assert not [name for name in names if name.startswith("feet/")]
    assert names[:2] == ("body/nose", "body/left_eye")
    assert names[17] == "body/left_big_toe"  # a point of the group `feet`, in the region `body`
    assert names[23:27] == ("body/head_center", "body/neck_center", "body/trunk_center", "body/hips_center")
    assert names[27] == "face/face-0" and names[95] == "left_hand/wrist" and names[116] == "right_hand/wrist"
    assert canonical_names([Group(**group) for group in output_schema["groups"]], value.point_names) == names

    result = to_canonical(value, output_schema)
    assert result.names == names
    assert result.xyz.shape == (2, 137, 3) and result.score.shape == (2, 137)
    # The face group passes through, in the canonical columns.
    assert result.groups == (Group("face", 27, 68, "COCO_WholeBody"),)
    np.testing.assert_array_equal(result.xyz[:, 27:95], value.xyz[:, 23:91])
    # A passthrough keeps the point and its score.
    toe = value.point_names.index("feet/left_big_toe")
    np.testing.assert_array_equal(result.xyz[:, 17], value.xyz[:, toe])
    np.testing.assert_array_equal(result.score[:, 95], value.score[:, value.point_names.index("left_hand/left_hand_root")])
    # A mean point: the mean of its sources, with the minimum of their scores.
    hips = [value.point_names.index("body/left_hip"), value.point_names.index("body/right_hip")]
    np.testing.assert_allclose(result.xyz[:, 26], value.xyz[:, hips].mean(axis=1))
    np.testing.assert_array_equal(result.score[:, 26], value.score[:, hips].min(axis=1))


def test_a_missing_left_hip_makes_hips_center_missing():
    value, output_schema = wholebody()
    hip = value.point_names.index("body/left_hip")
    value.xyz[0, hip] = np.nan
    value.score[0, hip] = 0.0
    result = to_canonical(value, output_schema)
    names = result.names
    for name in ("body/left_hip", "body/hips_center", "body/trunk_center"):
        assert np.isnan(result.xyz[0, names.index(name)]).all() and result.score[0, names.index(name)] == 0
        assert np.isfinite(result.xyz[1, names.index(name)]).all()
    assert np.isfinite(result.xyz[0, names.index("body/neck_center")]).all()


def test_a_group_with_a_null_schema_passes_through():
    names = ("face/a", "face/b", "left_hand/x")
    groups = [Group("face", 0, 2, None), Group("left_hand", 2, 1, None)]
    assert canonical_names(groups, names) == names
    value = InstanceKeypoints.empty(names, 1)
    value.xyz[0, 2] = (1.0, 2.0, 3.0)
    result = to_canonical(value, {"groups": groups, "canonical_names": names})
    assert result.names == names and result.groups == tuple(groups)
    np.testing.assert_array_equal(result.xyz, value.xyz)
    np.testing.assert_array_equal(result.score, value.score)


def test_the_group_name_gives_the_side_of_a_one_hand_schema(tmp_path):
    (tmp_path / "landmark_schemas").mkdir()
    (tmp_path / "landmark_schemas" / "Test_Hand.yaml").write_bytes(HAND_SCHEMA.encode())  # LF line endings
    names = ("left_hand/root", "left_hand/tip", "right_hand/root", "right_hand/tip")
    groups = [Group("left_hand", 0, 2, "Test_Hand"), Group("right_hand", 2, 2, "Test_Hand")]
    canonical = canonical_names(groups, names, tmp_path)
    assert canonical == ("left_hand/wrist", "left_hand/middle", "right_hand/wrist", "right_hand/middle")
    xyz = np.array([[[0.0, 0.0, 0.0], [4.0, 8.0, 0.0], [10.0, 10.0, 0.0], [np.nan, np.nan, np.nan]]])
    score = np.array([[0.9, 0.5, 0.8, 0.0]])
    value = InstanceKeypoints(names, xyz, score, np.ones(1), np.ones(1, dtype=bool), np.full(1, -1, dtype=np.int64))
    result = to_canonical(value, {"groups": groups, "canonical_names": canonical}, user_root=tmp_path)
    assert result.groups == ()
    np.testing.assert_allclose(result.xyz[0, :3], [[0.0, 0.0, 0.0], [3.0, 6.0, 0.0], [10.0, 10.0, 0.0]])
    np.testing.assert_allclose(result.score[0], [0.9, 0.5, 0.8, 0.0])
    assert np.isnan(result.xyz[0, 3]).all()  # each group stands alone: the right tip is missing


def test_refusals():
    value, output_schema = wholebody()
    with pytest.raises(ValueError, match="canonical_names"):
        to_canonical(value, {**output_schema, "canonical_names": output_schema["canonical_names"][:-1]})
    with pytest.raises(ValueError, match="not in the registry"):
        canonical_names([Group("body", 0, 1, "No_Such_Schema")], ("body/a",))
    with pytest.raises(ValueError, match="no column"):
        canonical_names([output_schema["groups"][0]], value.point_names[:17])  # `body` without `feet`
