"""Tests for the nine glue node types of the pipeline spec (stage 1.10 of the implementation plan).

The vector cases of each node run in ``tools/tests/test_vectors.py``. These tests check the load
rules of ``output_info``, the fixed shapes and the padding rows, the ``instance_score`` copy rules
and that no call changes an input or a state in place.
"""
from __future__ import annotations

import copy
import dataclasses
from typing import Any

import numpy as np
import pytest

from skellytracker.core.pipelines._runtime import (
    node_concat,
    node_first_of,
    node_gate,
    node_merge,
    node_redetect_trigger,
    node_roi_from_points,
    node_roi_hold,
    node_smooth_keypoints,
    node_smooth_roi,
)
from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines.config import (
    GateParams,
    MergeParams,
    NoParams,
    RedetectTriggerParams,
    RoiFromPointsParams,
    RoiHoldParams,
    SmoothKeypointsParams,
    SmoothRoiParams,
)
from skellytracker.core.pipelines.values import Group, InstanceBoxes, InstanceKeypoints, InstanceRois, PortInfo

BODY = ("body/left_wrist", "body/right_wrist", "body/nose")
HAND = ("hand/root", "hand/tip")
IMAGE = np.zeros((4, 4, 3), dtype=np.uint8)


def frame(index: int = 0, mode: str = "video") -> FrameContext:
    return FrameContext(index, None if mode == "image" else index * 40.0, (640, 480), mode)


def kp_info(names: tuple[str, ...], rows: int = 2, source: str = "person", geometry: str = "2d", **facts: Any) -> PortInfo:
    groups: list[Group] = []
    for column, name in enumerate(names):
        group = name.partition("/")[0]
        if groups and groups[-1].name == group:
            groups[-1] = Group(group, groups[-1].start, groups[-1].count + 1, None)
        else:
            groups.append(Group(group, column, 1, None))
    return PortInfo(
        "keypoints", max_instances=rows, instance_source=source, point_names=names, groups=tuple(groups), geometry=geometry, **facts
    )


def roi_info(rows: int = 2, source: str = "person") -> PortInfo:
    return PortInfo("roi", max_instances=rows, instance_source=source)


def kp(names: tuple[str, ...], rows: list[Any], scores: list[float] | None = None) -> InstanceKeypoints:
    """A value from rows of [x, y] points. A row of None is a padding row."""
    out = InstanceKeypoints.empty(names, len(rows))
    for i, row in enumerate(rows):
        if row is not None:
            out.xyz[i, :, :2], out.score[i], out.present[i] = row, 0.9, True
            out.instance_score[i] = 0.8 if scores is None else scores[i]
    return out


def rois(rows: list[Any], scores: list[float] | None = None) -> InstanceRois:
    out = InstanceRois.empty(len(rows))
    for i, row in enumerate(rows):
        if row is not None:
            out.rois[i], out.present[i] = row, True
            out.instance_score[i] = 0.7 if scores is None else scores[i]
    return out


def same(a: Any, b: Any) -> bool:
    """Return true when two values or states are equal. NaN equals NaN."""
    if dataclasses.is_dataclass(a) and not isinstance(a, type):
        return type(a) is type(b) and all(same(getattr(a, f.name), getattr(b, f.name)) for f in dataclasses.fields(a))
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and a.dtype == b.dtype and np.array_equal(a, b, equal_nan=a.dtype.kind == "f")
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return type(a) is type(b) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b, strict=True))
    return a == b or (isinstance(a, float) and isinstance(b, float) and a != a and b != b)


def is_padding(value: Any, row: int) -> bool:
    """Return true when one row of an instance value has the padding values of pipeline.outputs."""
    if value.present[row]:
        return False
    if isinstance(value, InstanceKeypoints):
        return bool(
            np.isnan(value.xyz[row]).all() and (value.score[row] == 0).all()
            and value.instance_score[row] == 0 and value.track_ids[row] == -1
        )
    if isinstance(value, InstanceRois):
        return bool(np.isnan(value.rois[row]).all() and value.instance_score[row] == 0)
    return bool(np.isnan(value.xyxy[row]).all() and value.score[row] == 0 and value.class_index[row] == -1 and value.track_ids[row] == -1)


def refuses(rule: str, call: Any, *args: Any, **kwargs: Any) -> None:
    with pytest.raises(ValueError, match=rf"^{rule}:"):
        call(*args, **kwargs)


# ---------------------------------------------------------------------------------------------
# One scenario for each node: row 0 is present and row 1 is a padding row, on two frames
# ---------------------------------------------------------------------------------------------


@dataclasses.dataclass
class Scenario:
    module: Any
    params: Any
    infos: Any
    frames: list[Any]
    """The inputs of each frame."""
    output: str
    extra: tuple[Any, ...] = ()

    def plan(self) -> tuple[Any, Any]:
        outputs, _ = self.module.output_info("node", self.params, self.infos, *self.extra)
        prepare = getattr(self.module, "prepare", None)
        return outputs, None if prepare is None else prepare("node", self.params, self.infos, outputs, *self.extra)

    def run(self) -> list[Any]:
        _, plan = self.plan()
        state, results = None, []
        for index, inputs in enumerate(self.frames):
            result, state = self.module.run(self.params, inputs, state, frame(index), plan)
            results.append(result[self.output])
        return results


def body(dx: float = 0.0, scores: list[float] | None = None) -> InstanceKeypoints:
    return kp(BODY, [[[100 + dx, 100], [200 + dx, 100], [150 + dx, 50]], None], scores)


def scenarios() -> dict[str, Scenario]:
    box, moved = [100, 100, 50, 80, 0.0], [104, 98, 55, 77, 0.0]
    hands = kp(HAND, [[[205, 110], [210, 130]], [[95, 105], [90, 125]]], [0.3, 0.4])
    return {
        "roi_from_points": Scenario(
            node_roi_from_points, RoiFromPointsParams(min_previous_ratio=0.5), {"keypoints": kp_info(BODY), "previous_rois": roi_info()},
            [{"keypoints": body(), "previous_rois": rois([None, None])}, {"keypoints": body(5), "previous_rois": rois([box, None])}],
            "rois",
        ),
        "roi_hold": Scenario(
            node_roi_hold, RoiHoldParams(),
            {"previous": roi_info(), "current": roi_info(), "previous_keypoints": kp_info(BODY)},
            [
                {"previous": rois([None, None]), "current": rois([box, None]), "previous_keypoints": kp(BODY, [None, None])},
                {"previous": rois([moved, moved], [0.9, 0.9]), "current": rois([box, None]), "previous_keypoints": kp(BODY, [None, None])},
            ],
            "rois",
        ),
        "gate": Scenario(
            node_gate, GateParams(mode="is_present"), {"value": roi_info(), "condition": kp_info(BODY)},
            [{"value": rois([box, moved]), "condition": body()}, {"value": rois([box, None]), "condition": body(5)}], "value",
        ),
        "first_of": Scenario(
            node_first_of, NoParams(), [roi_info(), roi_info()],
            [[rois([None, None]), rois([box, None])], [rois([moved, None]), rois([box, None])]], "value",
        ),
        "concat": Scenario(
            node_concat, NoParams(), [kp_info(BODY), kp_info(("left_hand/wrist", "left_hand/tip"))],
            [
                [body(), kp(("left_hand/wrist", "left_hand/tip"), [None, None])],
                [body(5), kp(("left_hand/wrist", "left_hand/tip"), [[[95, 105], [90, 125]], None])],
            ],
            "keypoints",
        ),
        "merge": Scenario(
            node_merge, MergeParams(slots={"right_hand": "body/right_wrist", "left_hand": "body/left_wrist"}, source_anchor="hand/root", max_distance=1.0),
            {"target": kp_info(BODY), "source": kp_info(HAND, source="hands")},
            [{"target": body(), "source": kp(HAND, [None, None])}, {"target": body(), "source": hands}], "keypoints",
        ),
        "smooth_keypoints": Scenario(
            node_smooth_keypoints, SmoothKeypointsParams(max_gap_ms=100.0), {"keypoints": kp_info(BODY)},
            [{"keypoints": body()}, {"keypoints": body(5)}, {"keypoints": kp(BODY, [None, None])}], "keypoints",
        ),
        "smooth_roi": Scenario(
            node_smooth_roi, SmoothRoiParams(), {"rois": roi_info()},
            [{"rois": rois([box, None])}, {"rois": rois([moved, None])}], "rois",
        ),
        "smooth_roi_one_euro": Scenario(
            node_smooth_roi, SmoothRoiParams(filter="one_euro"), {"rois": roi_info()},
            [{"rois": rois([box, None])}, {"rois": rois([moved, None])}], "rois",
        ),
    }


NAMES = sorted(scenarios())


@pytest.mark.parametrize("name", NAMES)
def test_each_frame_has_the_rows_of_the_output_port_and_padding_rows(name: str) -> None:
    scenario = scenarios()[name]
    outputs, _ = scenario.plan()
    info = outputs[scenario.output]
    for value in scenario.run():
        assert len(value.present) == info.max_instances == 2
        assert value.present[0] and is_padding(value, 1)
        if isinstance(value, InstanceKeypoints):
            assert value.point_names == info.point_names
            assert value.xyz.shape == (2, len(info.point_names), 3) and value.score.shape == (2, len(info.point_names))
        elif isinstance(value, InstanceRois):
            assert value.rois.shape == (2, 5)


@pytest.mark.parametrize("name", NAMES)
def test_a_call_changes_no_input_and_no_state_in_place(name: str) -> None:
    scenario = scenarios()[name]
    _, plan = scenario.plan()
    state = None
    for index, inputs in enumerate(scenario.frames):
        inputs_before, state_before = copy.deepcopy(inputs), copy.deepcopy(state)
        _, new_state = scenario.module.run(scenario.params, inputs, state, frame(index), plan)
        assert same(inputs, inputs_before)
        assert same(state, state_before)
        state = new_state


@pytest.mark.parametrize("name", ["smooth_keypoints", "smooth_roi", "smooth_roi_one_euro"])
def test_a_temporal_node_keeps_a_state_and_none_in_the_running_mode_image(name: str) -> None:
    scenario = scenarios()[name]
    result, state = scenario.module.run(scenario.params, scenario.frames[0], None, frame(), None)
    assert state is not None
    result, state = scenario.module.run(scenario.params, scenario.frames[0], None, frame(mode="image"), None)
    assert state is None and result[scenario.output] is scenario.frames[0][scenario.output]


def test_each_module_names_the_empty_inputs_that_it_reads() -> None:
    assert node_gate.READS_EMPTY == {"condition"}
    assert node_first_of.READS_EMPTY == {"*"} == node_concat.READS_EMPTY
    assert node_roi_hold.READS_EMPTY == {"previous"}
    assert node_merge.READS_EMPTY == {"source"}
    assert node_smooth_keypoints.READS_EMPTY == {"keypoints"}
    assert node_smooth_roi.READS_EMPTY == {"rois"}
    assert node_roi_from_points.READS_EMPTY == frozenset() == node_redetect_trigger.READS_EMPTY


# ---------------------------------------------------------------------------------------------
# roi_from_points
# ---------------------------------------------------------------------------------------------


def test_v_node_roi_from_points_2_a_name_must_be_a_point_of_the_input_or_a_derived_point() -> None:
    infos = {"keypoints": kp_info(BODY)}
    refuses("V-node.roi_from_points-2", node_roi_from_points.output_info, "n", RoiFromPointsParams(points=["body/elbow"]), infos)
    refuses(
        "V-node.roi_from_points-2", node_roi_from_points.output_info, "n",
        RoiFromPointsParams(points=["mid"], derived_points={"mid": ["body/nose", "body/elbow"]}), infos,
    )
    params = RoiFromPointsParams(
        points=["mid", ["body/right_wrist", "body/nose"]], derived_points={"mid": ["body/nose", "body/left_wrist"]},
        size_rule="alignment", alignment_start="body/nose", alignment_end="mid",
    )
    outputs, warnings = node_roi_from_points.output_info("n", params, infos)
    assert warnings == [] and outputs["rois"] == PortInfo("roi", max_instances=2, instance_source="person")


def test_v_node_roi_from_points_6_a_floor_ratio_needs_its_input() -> None:
    infos = {"keypoints": kp_info(BODY)}
    refuses("V-node.roi_from_points-6", node_roi_from_points.output_info, "n", RoiFromPointsParams(min_previous_ratio=0.5), infos)
    refuses("V-node.roi_from_points-6", node_roi_from_points.output_info, "n", RoiFromPointsParams(min_reference_ratio=0.5), infos)


@pytest.mark.parametrize("port", ["previous_rois", "reference_rois"])
@pytest.mark.parametrize("other", [roi_info(rows=1), roi_info(source="hands")])
def test_v_node_roi_from_points_7_a_floor_input_has_the_source_and_the_rows_of_keypoints(port: str, other: PortInfo) -> None:
    refuses("V-node.roi_from_points-7", node_roi_from_points.output_info, "n", RoiFromPointsParams(), {"keypoints": kp_info(BODY), port: other})


def test_roi_from_points_copies_the_instance_score_of_the_keypoints_row() -> None:
    keypoints = kp(BODY, [[[1, 2], [3, 4], [5, 6]], [[1, 2], [np.nan, np.nan], [5, 6]]], [0.8, 0.6])
    params = RoiFromPointsParams(points=["body/right_wrist"])
    out = node_roi_from_points.run(params, {"keypoints": keypoints}, None, frame())[0]["rois"]
    assert out.instance_score.tolist() == [0.8, 0.0] and out.present.tolist() == [True, False] and is_padding(out, 1)


def test_roi_from_points_reads_a_param_that_a_run_can_set_at_each_call() -> None:
    inputs = {"keypoints": body()}
    wide = node_roi_from_points.run(RoiFromPointsParams(expand_ratio=2.0), inputs, None, frame())[0]["rois"]
    assert wide.rois[0].tolist() == [150.0, 75.0, 200.0, 100.0, 0.0]


# ---------------------------------------------------------------------------------------------
# roi_hold
# ---------------------------------------------------------------------------------------------


def test_v_node_roi_hold_2_the_inputs_have_the_same_number_of_rows() -> None:
    refuses("V-node.roi_hold-2", node_roi_hold.output_info, "n", RoiHoldParams(), {"previous": roi_info(rows=1), "current": roi_info()})
    infos = {"previous": roi_info(), "current": roi_info(), "previous_keypoints": kp_info(BODY, rows=3)}
    refuses("V-node.roi_hold-2", node_roi_hold.output_info, "n", RoiHoldParams(), infos)


def test_v_node_roi_hold_3_the_inputs_have_the_instance_source_of_current() -> None:
    refuses("V-node.roi_hold-3", node_roi_hold.output_info, "n", RoiHoldParams(), {"previous": roi_info(source="hands"), "current": roi_info()})
    infos = {"previous": roi_info(), "current": roi_info(), "previous_keypoints": kp_info(BODY, source="hands")}
    refuses("V-node.roi_hold-3", node_roi_hold.output_info, "n", RoiHoldParams(), infos)
    outputs, _ = node_roi_hold.output_info("n", RoiHoldParams(), {"previous": roi_info(), "current": roi_info()})
    assert outputs["rois"] == roi_info()


def test_roi_hold_keeps_the_instance_score_of_a_kept_previous_row() -> None:
    previous = rois([[104, 98, 55, 47, 0.0], [300, 300, 50, 50, 0.0]], [0.9, 0.9])
    current = rois([[100, 100, 50, 50, 0.0], [100, 100, 50, 50, 0.0]], [0.6, 0.7])
    out = node_roi_hold.run(RoiHoldParams(), {"previous": previous, "current": current}, None, frame())[0]["rois"]
    assert out.instance_score.tolist() == [0.9, 0.7]
    assert out.rois.tolist() == [[104, 98, 55, 47, 0], [100, 100, 50, 50, 0]]


# ---------------------------------------------------------------------------------------------
# gate
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("condition", [roi_info(), PortInfo("image"), PortInfo("tensor")])
def test_v_node_gate_2_score_above_needs_a_condition_with_a_score(condition: PortInfo) -> None:
    params = GateParams(mode="score_above", threshold=0.5)
    refuses("V-node.gate-2", node_gate.output_info, "n", params, {"value": PortInfo("image"), "condition": condition})
    for scored in (kp_info(BODY), PortInfo("detections", max_instances=2, instance_source="person")):
        outputs, _ = node_gate.output_info("n", params, {"value": PortInfo("image"), "condition": scored})
        assert outputs["value"] == PortInfo("image")


def test_v_node_gate_3_two_instance_ports_have_the_same_number_of_rows() -> None:
    params = GateParams(mode="is_present")
    refuses("V-node.gate-3", node_gate.output_info, "n", params, {"value": roi_info(rows=2), "condition": kp_info(BODY, rows=1)})
    node_gate.output_info("n", params, {"value": PortInfo("image"), "condition": kp_info(BODY, rows=1)})


def gate(params: GateParams, value: Any, condition: Any, value_info: PortInfo, condition_info: PortInfo) -> Any:
    infos = {"value": value_info, "condition": condition_info}
    outputs, _ = node_gate.output_info("n", params, infos)
    return node_gate.run(params, {"value": value, "condition": condition}, None, frame(), node_gate.prepare("n", params, infos, outputs))[0]["value"]


def test_gate_passes_an_image_and_a_tensor_unchanged_or_gives_none() -> None:
    empty = kp(BODY, [None, None])
    assert gate(GateParams(mode="is_empty"), IMAGE, empty, PortInfo("image"), kp_info(BODY)) is IMAGE
    assert gate(GateParams(mode="is_empty"), IMAGE, body(), PortInfo("image"), kp_info(BODY)) is None
    tensor = np.ones((1, 3), dtype=np.float32)
    assert gate(GateParams(mode="is_present"), tensor, IMAGE, PortInfo("tensor"), PortInfo("image")) is tensor
    assert gate(GateParams(mode="is_present"), tensor, None, PortInfo("tensor"), PortInfo("image")) is None


def test_gate_keeps_the_rows_of_a_detections_value_and_their_class_index() -> None:
    boxes = InstanceBoxes(
        np.array([[0.0, 0, 10, 10], [5, 5, 20, 20]]), np.array([0.9, 0.4]), np.array([3, 1]), np.array([True, True]), np.array([-1, -1])
    )
    info = PortInfo("detections", max_instances=2, instance_source="person")
    out = gate(GateParams(mode="score_above", threshold=0.5), boxes, boxes, info, info)
    assert out.class_index.tolist() == [3, -1] and out.score.tolist() == [0.9, 0.0] and is_padding(out, 1)
    assert gate(GateParams(mode="is_present"), boxes, IMAGE, info, PortInfo("image")) is boxes


def test_gate_copies_the_instance_score_of_the_value_row() -> None:
    value = rois([[1, 2, 3, 4, 0.0], [5, 6, 7, 8, 0.0]], [0.6, 0.5])
    out = gate(GateParams(mode="is_present"), value, body(), roi_info(), kp_info(BODY))
    assert out.instance_score.tolist() == [0.6, 0.0]
    one_test = gate(GateParams(mode="is_present"), value, IMAGE, roi_info(), PortInfo("image"))
    assert one_test is value
    blocked = gate(GateParams(mode="is_empty"), value, IMAGE, roi_info(), PortInfo("image"))
    assert same(blocked, InstanceRois.empty(2))


def test_gate_reads_the_threshold_at_each_call() -> None:
    value, condition = rois([[1, 2, 3, 4, 0.0], None]), body()
    assert gate(GateParams(mode="score_above", threshold=0.5), value, condition, roi_info(), kp_info(BODY)).present.tolist() == [True, False]
    assert gate(GateParams(mode="score_above", threshold=0.95), value, condition, roi_info(), kp_info(BODY)).present.tolist() == [False, False]


# ---------------------------------------------------------------------------------------------
# first_of
# ---------------------------------------------------------------------------------------------


def test_v_node_first_of_2_instance_inputs_have_one_instance_source_and_the_same_groups() -> None:
    refuses("V-node.first_of-2", node_first_of.output_info, "n", NoParams(), [roi_info(), roi_info(source="hands")])
    refuses("V-node.first_of-2", node_first_of.output_info, "n", NoParams(), [kp_info(BODY), kp_info(HAND)])
    outputs, _ = node_first_of.output_info("n", NoParams(), [PortInfo("image"), PortInfo("image")])
    assert outputs["value"] == PortInfo("image")
    outputs, _ = node_first_of.output_info("n", NoParams(), [kp_info(BODY), kp_info(BODY)])
    assert outputs["value"] == kp_info(BODY)


def test_first_of_gives_the_first_value_that_is_not_empty_with_its_instance_score() -> None:
    kept = rois([[1, 2, 3, 4, 0.0], None], [0.6, 0.0])
    values = [rois([None, None]), kept, rois([[9, 9, 9, 9, 0.0], None])]
    assert node_first_of.run(NoParams(), values, None, frame(), roi_info())[0]["value"] is kept
    assert same(node_first_of.run(NoParams(), values[:1], None, frame(), roi_info())[0]["value"], InstanceRois.empty(2))
    assert node_first_of.run(NoParams(), [None, IMAGE], None, frame(), PortInfo("image"))[0]["value"] is IMAGE
    assert node_first_of.run(NoParams(), [None, None], None, frame(), PortInfo("image"))[0]["value"] is None


# ---------------------------------------------------------------------------------------------
# concat
# ---------------------------------------------------------------------------------------------


def test_v_node_concat_1_each_input_has_the_same_instance_source() -> None:
    refuses("V-node.concat-1", node_concat.output_info, "n", NoParams(), [kp_info(BODY), kp_info(HAND, source="hands")])


def test_v_node_concat_2_the_point_names_do_not_collide() -> None:
    refuses("V-node.concat-2", node_concat.output_info, "n", NoParams(), [kp_info(BODY), kp_info(BODY)])


def test_v_node_concat_3_each_input_has_the_same_geometry() -> None:
    refuses("V-node.concat-3", node_concat.output_info, "n", NoParams(), [kp_info(BODY), kp_info(HAND, geometry="3d")])


def test_concat_gives_the_points_the_groups_and_the_edges_of_each_input_in_list_order() -> None:
    hand = kp_info(HAND, edges=(("hand/root", "hand/tip"),))
    outputs, warnings = node_concat.output_info("n", NoParams(), [hand, kp_info(BODY, edges=(("body/nose", "body/left_wrist"),))])
    out = outputs["keypoints"]
    assert warnings == [] and out.point_names == HAND + BODY
    assert out.groups == (Group("hand", 0, 2, None), Group("body", 2, 3, None))
    assert out.edges == (("hand/root", "hand/tip"), ("body/nose", "body/left_wrist"))
    assert (out.max_instances, out.instance_source, out.geometry) == (2, "person", "2d")


def test_concat_fills_the_columns_of_an_empty_input_with_missing_points() -> None:
    """ADR-6DKT item 5: x, y and z are NaN and the score is 0."""
    infos = [kp_info(BODY), kp_info(HAND)]
    outputs, _ = node_concat.output_info("n", NoParams(), infos)
    plan = node_concat.prepare("n", NoParams(), infos, outputs)
    # An empty value can hold old numbers in its arrays: the node must not copy them.
    stale = InstanceKeypoints(HAND, np.ones((2, 2, 3)), np.ones((2, 2)), np.ones(2), np.zeros(2, dtype=bool), np.full(2, -1))
    out = node_concat.run(NoParams(), [body(), stale], None, frame(), plan)[0]["keypoints"]
    assert np.isnan(out.xyz[:, 3:]).all() and (out.score[:, 3:] == 0).all()
    assert out.xyz[0, :3, :2].tolist() == [[100, 100], [200, 100], [150, 50]] and np.isnan(out.xyz[0, :3, 2]).all()
    assert out.present.tolist() == [True, False] and is_padding(out, 1)
    each_empty = node_concat.run(NoParams(), [kp(BODY, [None, None]), stale], None, frame(), plan)[0]["keypoints"]
    assert same(each_empty, InstanceKeypoints.empty(BODY + HAND, 2))


def test_concat_takes_the_instance_score_of_the_first_input_whose_row_is_present() -> None:
    infos = [kp_info(HAND), kp_info(BODY)]
    outputs, _ = node_concat.output_info("n", NoParams(), infos)
    hand = kp(HAND, [[[1, 1], [2, 2]], None], [0.8, 0.0])
    full = kp(BODY, [[[1, 1], [2, 2], [3, 3]], [[4, 4], [5, 5], [6, 6]]], [0.7, 0.6])
    out = node_concat.run(NoParams(), [hand, full], None, frame(), node_concat.prepare("n", NoParams(), infos, outputs))[0]["keypoints"]
    assert out.instance_score.tolist() == [0.8, 0.6] and out.present.tolist() == [True, True]
    assert np.isnan(out.xyz[1, :2]).all() and out.xyz[1, 2:, :2].tolist() == [[4, 4], [5, 5], [6, 6]]


# ---------------------------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------------------------

WHOLE = ("body/left_wrist", "body/nose", "left_hand/left_hand_root", "left_hand/left_thumb1")
MERGE_INFOS = {"target": kp_info(BODY), "source": kp_info(HAND, source="hands", rows=3)}


def merge_params(**changes: Any) -> MergeParams:
    values = {"slots": {"left_hand": "body/left_wrist"}, "source_anchor": "hand/root", "max_distance": 1.0, **changes}
    return MergeParams(**values)


def test_v_node_merge_2_each_name_is_a_point_of_its_port() -> None:
    for changes in (
        {"slots": {"left_hand": "body/elbow"}},
        {"source_anchor": "hand/wrist"},
        {"map": {"body/elbow": "left_hand/root"}},
        {"map": {"body/nose": "left_hand/wrist"}},
    ):
        refuses("V-node.merge-2", node_merge.output_info, "n", merge_params(**changes), MERGE_INFOS)


def test_v_node_merge_3_target_and_source_have_the_same_geometry() -> None:
    infos = {"target": kp_info(BODY), "source": kp_info(HAND, source="hands", geometry="3d")}
    refuses("V-node.merge-3", node_merge.output_info, "n", merge_params(), infos)


def test_v_node_merge_4_source_has_exactly_one_group() -> None:
    infos = {"target": kp_info(BODY), "source": kp_info(("hand/root", "arm/tip"), source="hands")}
    refuses("V-node.merge-4", node_merge.output_info, "n", merge_params(), infos)


def test_v_node_merge_5_a_face_replace_needs_a_map_key_in_the_group_face() -> None:
    infos = {"target": kp_info(("body/nose", "face/chin")), "source": kp_info(("mesh/p1",), source="faces")}
    params = {"slots": {"face": "body/nose"}, "source_anchor": "mesh/p1"}
    refuses("V-node.merge-5", node_merge.output_info, "n", merge_params(**params), infos)
    refuses("V-node.merge-5", node_merge.output_info, "n", merge_params(**params, map={"body/nose": "face/p1"}), infos)
    node_merge.output_info("n", merge_params(**params, map={"face/chin": "face/p1"}), infos)


def test_merge_keeps_the_facts_of_target_and_adds_the_group_and_the_edges_of_an_adding_slot() -> None:
    target = kp_info(BODY, edges=(("body/nose", "body/left_wrist"),), depth_unit=None)
    source = PortInfo(
        "keypoints", max_instances=3, instance_source="hands", point_names=HAND, groups=(Group("hand", 0, 2, "Hand21"),),
        geometry="2d", edges=(("hand/root", "hand/tip"),),
    )
    params = merge_params(slots={"right_hand": "body/right_wrist", "left_hand": "body/left_wrist"})
    outputs, warnings = node_merge.output_info("n", params, {"target": target, "source": source})
    out = outputs["keypoints"]
    assert warnings == []
    assert out.point_names == (*BODY, "right_hand/root", "right_hand/tip", "left_hand/root", "left_hand/tip")
    assert out.groups == (Group("body", 0, 3, None), Group("right_hand", 3, 2, "Hand21"), Group("left_hand", 5, 2, "Hand21"))
    assert out.edges == (
        ("body/nose", "body/left_wrist"),
        ("right_hand/root", "right_hand/tip"), ("body/right_wrist", "right_hand/root"),
        ("left_hand/root", "left_hand/tip"), ("body/left_wrist", "left_hand/root"),
    )
    assert (out.max_instances, out.instance_source, out.geometry) == (2, "person", "2d")


def test_merge_gives_the_warning_merge_unfilled_points_for_a_replaced_group() -> None:
    infos = {"target": kp_info(WHOLE, edges=(("body/nose", "left_hand/left_thumb1"),)), "source": kp_info(HAND, source="hands")}
    outputs, warnings = node_merge.output_info("n", merge_params(), infos)
    assert outputs["keypoints"].point_names == WHOLE and outputs["keypoints"].groups == infos["target"].groups
    assert outputs["keypoints"].edges == infos["target"].edges  # a replacing slot adds no edge
    assert [(w["code"], w["node_ids"], w["details"]) for w in warnings] == [
        ("merge_unfilled_points", ("n",), {"points": ["left_hand/left_hand_root", "left_hand/left_thumb1"]})
    ]
    canonical = {"left_hand/left_hand_root": "wrist", "hand/root": "wrist"}
    _, warnings = node_merge.output_info("n", merge_params(), infos, canonical)
    assert warnings[0]["details"] == {"points": ["left_hand/left_thumb1"]}
    _, warnings = node_merge.output_info("n", merge_params(map={"left_hand/left_thumb1": "left_hand/tip"}), infos, canonical)
    assert warnings == []


def test_merge_copies_the_instance_score_of_the_target_row_and_reads_max_distance_at_each_call() -> None:
    scenario = scenarios()["merge"]
    _, plan = scenario.plan()
    inputs = scenario.frames[1]
    out = node_merge.run(scenario.params, inputs, None, frame(), plan)[0]["keypoints"]
    assert out.instance_score.tolist() == [0.8, 0.0] and out.track_ids.tolist() == [-1, -1]
    assert out.xyz[0, 3:, :2].tolist() == [[205, 110], [210, 130], [95, 105], [90, 125]]
    assert out.score[0].tolist() == [0.9] * 7
    near = scenario.params.model_copy(update={"max_distance": 0.01})
    out = node_merge.run(near, inputs, None, frame(), plan)[0]["keypoints"]
    assert np.isnan(out.xyz[0, 3:]).all() and (out.score[0, 3:] == 0).all() and out.present.tolist() == [True, False]


# ---------------------------------------------------------------------------------------------
# smooth_keypoints, smooth_roi and redetect_trigger
# ---------------------------------------------------------------------------------------------


def stamped(t: float, mode: str = "video") -> FrameContext:
    return FrameContext(0, t, (640, 480), mode)


@pytest.mark.parametrize("t", [40.0, 30.0])
def test_v_node_smooth_keypoints_3_a_timestamp_that_does_not_increase_is_refused(t: float) -> None:
    params, inputs = SmoothKeypointsParams(), {"keypoints": body()}
    _, state = node_smooth_keypoints.run(params, inputs, None, stamped(40.0))
    before = copy.deepcopy(state)
    refuses("V-node.smooth_keypoints-3", node_smooth_keypoints.run, params, inputs, state, stamped(t))
    assert same(state, before)
    roi_state = (((1.0, 2.0, 3.0, 4.0), (0.0,) * 4, 40.0),)
    refuses(
        "V-node.smooth_keypoints-3", node_smooth_roi.run, SmoothRoiParams(filter="one_euro"), {"rois": rois([[1, 2, 3, 4, 0.0]])},
        roi_state, stamped(t),
    )


def test_smooth_keypoints_gives_the_facts_of_its_input_and_passes_z_and_the_score() -> None:
    info = kp_info(BODY, geometry="3d", depth_unit="mm")
    assert node_smooth_keypoints.output_info("n", SmoothKeypointsParams(), {"keypoints": info}) == ({"keypoints": info}, [])
    first, second = body(), body(10)
    first.xyz[0, :, 2], second.xyz[0, :, 2] = 1.0, 2.0
    second.score[0] = [0.1, 0.2, 0.3]
    _, state = node_smooth_keypoints.run(SmoothKeypointsParams(), {"keypoints": first}, None, stamped(0.0))
    out = node_smooth_keypoints.run(SmoothKeypointsParams(), {"keypoints": second}, state, stamped(40.0))[0]["keypoints"]
    assert out.xyz[0, :, 2].tolist() == [2.0, 2.0, 2.0] and out.score[0].tolist() == [0.1, 0.2, 0.3]
    assert 100 < out.xyz[0, 0, 0] < 110 and out.xyz[0, 0, 1] == 100


def test_smooth_keypoints_does_not_run_before_its_first_input_and_holds_the_instance_score() -> None:
    params, empty = SmoothKeypointsParams(max_gap_ms=50.0), kp(BODY, [None, None])
    out, state = node_smooth_keypoints.run(params, {"keypoints": empty}, None, stamped(0.0))
    assert state is None and same(out["keypoints"], empty)
    _, state = node_smooth_keypoints.run(params, {"keypoints": body(scores=[0.9, 0.0])}, state, stamped(40.0))
    held, state = node_smooth_keypoints.run(params, {"keypoints": empty}, state, stamped(80.0))
    assert held["keypoints"].present.tolist() == [True, False] and held["keypoints"].instance_score.tolist() == [0.9, 0.0]
    assert held["keypoints"].xyz[0, :, :2].tolist() == [[100, 100], [200, 100], [150, 50]] and is_padding(held["keypoints"], 1)
    gone, _ = node_smooth_keypoints.run(params, {"keypoints": empty}, state, stamped(120.0))
    assert same(gone["keypoints"], empty)


def test_smooth_roi_passes_the_instance_score_and_keeps_or_clears_its_state_on_an_empty_input() -> None:
    box, empty = rois([[100, 100, 50, 80, 0.0], None], [0.6, 0.0]), rois([None, None])
    for params, kept in ((SmoothRoiParams(), True), (SmoothRoiParams(filter="one_euro"), False)):
        out, state = node_smooth_roi.run(params, {"rois": box}, None, stamped(0.0))
        assert out["rois"].instance_score.tolist() == [0.6, 0.0] and state is not None
        out, after = node_smooth_roi.run(params, {"rois": empty}, state, stamped(40.0))
        assert same(out["rois"], empty) and (after is state if kept else after is None)
    assert node_smooth_roi.output_info("n", SmoothRoiParams(), {"rois": roi_info()}) == ({"rois": roi_info()}, [])


def test_v_node_redetect_trigger_2_roi_missing_needs_the_input_previous_rois() -> None:
    params = RedetectTriggerParams(fitness_checks=[{"check": "roi_missing"}])
    refuses("V-node.redetect_trigger-2", node_redetect_trigger.output_info, "n", params, {"image": PortInfo("image")})
    outputs, warnings = node_redetect_trigger.output_info("n", params, {"image": PortInfo("image"), "previous_rois": roi_info(rows=1)})
    assert (outputs, warnings) == ({"image": PortInfo("image")}, [])


def test_redetect_trigger_gives_the_input_image_or_none_and_reads_the_interval_at_each_call() -> None:
    inputs = {"image": IMAGE}
    out, last = node_redetect_trigger.run(RedetectTriggerParams(redetect_interval=3), inputs, None, frame(0))
    assert out["image"] is IMAGE and last == 0
    out, last = node_redetect_trigger.run(RedetectTriggerParams(redetect_interval=3), inputs, last, frame(2))
    assert out["image"] is None and last == 0
    out, last = node_redetect_trigger.run(RedetectTriggerParams(redetect_interval=2), inputs, last, frame(2))
    assert out["image"] is IMAGE and last == 2
    out, last = node_redetect_trigger.run(RedetectTriggerParams(redetect_interval=9), inputs, last, frame(3, mode="image"))
    assert out["image"] is IMAGE and last is None
