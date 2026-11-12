"""Named tests of the glue nodes first_of, concat and merge (ADR-3SF2 item 4).

These node types have no vector file. Each test runs the reference implementation in
`specs/pipeline/reference/` on a small case of its section in `specs/pipeline/nodes/`.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest

import make_vectors

REFERENCE = Path(__file__).resolve().parents[2] / "specs" / "pipeline" / "reference"
NAN = math.nan


def node(name: str) -> Any:
    return make_vectors.load_reference(f"node.{name}", REFERENCE)


def keypoints(names: list[str], rows: list[list[list[float]] | None], source: str = "person", geometry: str = "2d") -> dict[str, Any]:
    """A keypoints value. A row of None is a padding row. Each point is [x, y] with score 0.9.

    The instance score of a present row is 0.8, and of a padding row 0.
    """
    width = len(names)
    return {
        "point_names": names,
        "xyz": [[[NAN] * 3] * width if row is None else [[x, y, NAN] for x, y in row] for row in rows],
        "score": [[0.0] * width if row is None else [0.0 if math.isnan(x) else 0.9 for x, _ in row] for row in rows],
        "instance_score": [0.0 if row is None else 0.8 for row in rows],
        "present": [row is not None for row in rows],
        "track_ids": [-1] * len(rows),
        "instance_source": source,
        "geometry": geometry,
    }


def xy(value: dict[str, Any], row: int, name: str) -> list[float]:
    return value["xyz"][row][value["point_names"].index(name)][:2]


# ---------------------------------------------------------------------------
# first_of
# ---------------------------------------------------------------------------


def test_first_of_gives_the_first_input_that_is_not_empty_in_list_order() -> None:
    detected = keypoints(["body.nose"], [None])  # no present row: empty
    tracked = keypoints(["body.nose"], [[[1, 2]]])
    assert node("first_of").run({}, {"values": [None, detected, tracked]}) == {"value": tracked}
    assert node("first_of").run({}, {"values": ["image", tracked]}) == {"value": "image"}


def test_first_of_is_empty_when_each_input_is_empty() -> None:
    assert node("first_of").run({}, {"values": [None, keypoints(["body.nose"], [None])]}) == {"value": None}


# ---------------------------------------------------------------------------
# concat
# ---------------------------------------------------------------------------


def test_concat_joins_row_i_of_each_input_in_list_order() -> None:
    body = keypoints(["body.nose", "body.left_wrist"], [[[10, 10], [20, 30]], None])
    hand = keypoints(["left_hand.wrist"], [[[21, 31]], None])
    out = run_concat([body, hand])
    assert out["point_names"] == ["body.nose", "body.left_wrist", "left_hand.wrist"]
    assert xy(out, 0, "left_hand.wrist") == [21, 31]
    assert out["present"] == [True, False]
    assert out["instance_score"] == [0.8, 0.0]
    assert out["instance_source"] == "person"


def run_concat(values: list[dict[str, Any] | None], names: list[list[str]] | None = None) -> dict[str, Any] | None:
    point_names = names or [value["point_names"] for value in values]
    return node("concat").run({}, {"values": values, "point_names": point_names})["keypoints"]


def test_concat_runs_with_an_empty_input_and_gives_missing_points_in_its_columns() -> None:
    body = keypoints(["body.nose", "body.left_wrist"], [[[10, 10], [20, 30]]])
    empty_hand = keypoints(["left_hand.wrist", "left_hand.tip"], [None])  # no present row: empty
    for hand in (None, empty_hand):
        out = run_concat([body, hand], [body["point_names"], empty_hand["point_names"]])
        assert out["point_names"] == ["body.nose", "body.left_wrist", "left_hand.wrist", "left_hand.tip"]
        assert xy(out, 0, "body.left_wrist") == [20, 30]
        assert all(math.isnan(v) for v in xy(out, 0, "left_hand.wrist") + xy(out, 0, "left_hand.tip"))
        assert out["score"][0] == [0.9, 0.9, 0.0, 0.0]
        assert out["present"] == [True]


def test_concat_is_empty_when_each_input_is_empty() -> None:
    assert run_concat([None, None], [["body.nose"], ["left_hand.wrist"]]) is None


@pytest.mark.parametrize(
    ("second", "rule"),
    [
        (keypoints(["hand.wrist"], [[[1, 1]]], source="hands"), "V-node.concat-1"),
        (keypoints(["body.nose"], [[[1, 1]]]), "V-node.concat-2"),
        (keypoints(["face.tip"], [[[1, 1]]], geometry="3d"), "V-node.concat-3"),
    ],
    ids=["instance-source", "collision", "geometry"],
)
def test_concat_refuses_mixed_instance_sources_collisions_and_mixed_geometries(second: dict[str, Any], rule: str) -> None:
    body = keypoints(["body.nose"], [[[10, 10]]])
    with pytest.raises(ValueError, match=rule):
        run_concat([body, second])


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------

BODY_NAMES = ["body.left_wrist", "body.right_wrist", "body.nose"]
HAND_NAMES = ["hand.wrist", "hand.tip"]
PARAMS = {
    "slots": {"right_hand": "body.right_wrist", "left_hand": "body.left_wrist"},
    "source_anchor": "hand.wrist",
    "map": {"body.left_wrist": "left_hand.wrist"},
}


def run_merge(target: dict[str, Any] | None, source: dict[str, Any] | None, **params: Any) -> dict[str, Any] | None:
    return node("merge").run({**PARAMS, **params}, {"target": target, "source": source, "source_names": HAND_NAMES})["keypoints"]


def test_merge_puts_each_source_row_in_the_nearest_slot_and_keeps_the_target_rows() -> None:
    body = keypoints(BODY_NAMES, [[[100, 100], [200, 100], [150, 50]], None], source="person")
    hands = keypoints(HAND_NAMES, [[[205, 110], [210, 130]], [[95, 105], [90, 125]]], source="hands")
    out = run_merge(body, hands)
    assert out["point_names"] == [*BODY_NAMES, "right_hand.wrist", "right_hand.tip", "left_hand.wrist", "left_hand.tip"]
    assert xy(out, 0, "right_hand.tip") == [210, 130]
    assert xy(out, 0, "left_hand.tip") == [90, 125]
    # The map replaces the body left wrist with the present left-hand wrist; the right wrist stays.
    assert xy(out, 0, "body.left_wrist") == [95, 105]
    assert xy(out, 0, "body.right_wrist") == [200, 100]
    assert out["present"] == [True, False]
    assert out["instance_source"] == "person"
    # The output keeps the instance score of the target row, not of the hand rows.
    hands["instance_score"] = [0.3, 0.4]
    assert run_merge(body, hands)["instance_score"] == [0.8, 0.0]
    assert all(math.isnan(v) for v in xy(out, 1, "left_hand.wrist"))


def test_merge_gives_each_slot_at_most_one_source_row_greedy_by_distance() -> None:
    body = keypoints(BODY_NAMES, [[[100, 100], [200, 100], [150, 50]]])
    # Both hands are nearest to the left wrist. The nearer hand takes it; the other takes the right slot.
    hands = keypoints(HAND_NAMES, [[[110, 100], [0, 0]], [[101, 100], [1, 1]]], source="hands")
    out = run_merge(body, hands)
    assert xy(out, 0, "left_hand.tip") == [1, 1]
    assert xy(out, 0, "right_hand.tip") == [0, 0]


def test_merge_drops_a_match_farther_than_max_distance() -> None:
    # The box around the body points is 100 x 50: the diagonal is about 111.8.
    body = keypoints(BODY_NAMES, [[[100, 100], [200, 100], [150, 50]]])
    hands = keypoints(HAND_NAMES, [[[100, 160], [0, 0]]], source="hands")
    assert xy(run_merge(body, hands, max_distance=0.6), 0, "left_hand.tip") == [0, 0]
    out = run_merge(body, hands, max_distance=0.5)
    assert all(math.isnan(v) for v in xy(out, 0, "left_hand.tip") + xy(out, 0, "right_hand.tip"))


def test_an_empty_source_gives_missing_slot_columns_and_an_empty_target_gives_an_empty_output() -> None:
    body = keypoints(BODY_NAMES, [[[100, 100], [200, 100], [150, 50]]])
    out = run_merge(body, None)
    assert xy(out, 0, "body.left_wrist") == [100, 100]
    assert all(math.isnan(v) for v in xy(out, 0, "left_hand.wrist"))
    assert out["score"][0][out["point_names"].index("left_hand.wrist")] == 0.0
    assert run_merge(keypoints(BODY_NAMES, [None]), None) is None


@pytest.mark.parametrize(
    ("params", "rule"),
    [
        ({"slots": {"body": "body.left_wrist"}}, "V-node.merge-1"),
        ({"source_anchor": "hand.thumb"}, "V-node.merge-2"),
        ({"map": {"body.left_wrist": "left_hand.thumb"}}, "V-node.merge-2"),
    ],
    ids=["slot-column-collides", "unknown-anchor", "unknown-map-column"],
)
def test_merge_refuses_unknown_names_and_colliding_slot_columns(params: dict[str, Any], rule: str) -> None:
    body = keypoints(["body.left_wrist", "body.wrist"], [[[1, 1], [2, 2]]])
    with pytest.raises(ValueError, match=rule):
        node("merge").run(
            {**PARAMS, "map": {}, **params}, {"target": body, "source": None, "source_names": HAND_NAMES}
        )


def test_merge_refuses_mixed_geometries() -> None:
    body = keypoints(BODY_NAMES, [[[100, 100], [200, 100], [150, 50]]])
    hands = keypoints(HAND_NAMES, [[[100, 100], [0, 0]]], source="hands", geometry="3d")
    with pytest.raises(ValueError, match="V-node.merge-3"):
        run_merge(body, hands)
