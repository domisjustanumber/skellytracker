"""The host load checks of a pipeline (`_runtime/resolve.py`), on a temporary sidecar root and on the built-ins."""
from __future__ import annotations

import copy
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from skellytracker.core.detectors.catalog import load_detector_sidecar
from skellytracker.core.model_spec.landmark_schemas import load_landmark_schema_registry
from skellytracker.core.pipelines._runtime import mediapipe_tasks, resolve as resolve_module
from skellytracker.core.pipelines._runtime.resolve import keypoint_port_info, resolve
from skellytracker.core.pipelines.catalog import PACKAGE_PIPELINE_ROOT, find_pipeline, list_pipelines
from skellytracker.core.pipelines.config import PipelineConfig
from skellytracker.core.pipelines.loading import check_pipeline, export_pipeline, load_pipeline, load_pipeline_file
from skellytracker.core.pipelines.values import PortInfo
from skellytracker.tests.model_spec.sidecars import BASES
from skellytracker.tests.pipelines.pipeline_models import (
    KEYPOINT_KEY,
    OBJECT_KEY,
    detector_pipeline,
    isolate,
    keypoint_sidecar,
    object_sidecar,
    write_models,
    write_sidecar,
)

MODES = ("image", "video", "live")


@pytest.fixture(autouse=True)
def private_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isolate(monkeypatch, tmp_path)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return write_models(tmp_path / "user")


def config_of(data: dict[str, Any]) -> PipelineConfig:
    return PipelineConfig.model_validate(data)


def with_nodes(*nodes: dict[str, Any], outputs: dict[str, str] | None = None, **person_params: Any) -> dict[str, Any]:
    """Return `detector_pipeline` with more nodes, and with other outputs when `outputs` is given."""
    data = detector_pipeline(**person_params)
    data["nodes"] += copy.deepcopy(list(nodes))
    data["outputs"] = outputs or data["outputs"]
    return data


def mediapipe_pipeline(*nodes: dict[str, Any], outputs: dict[str, str], **params: Any) -> dict[str, Any]:
    first = {"id": "mp", "type": "mediapipe_tasks", "inputs": {"image": "frame.image"}, "params": {"variant": "body", **params}}
    return {**detector_pipeline(), "nodes": [first, *copy.deepcopy(list(nodes))], "outputs": outputs}


# ---------------------------------------------------------------------------------------------
# The facts of the ports and the output schema
# ---------------------------------------------------------------------------------------------


def test_the_output_schema_of_two_models_comes_from_the_sidecars(root: Path) -> None:
    resolved = resolve(config_of(detector_pipeline(max_instances=2)), root)
    assert resolved.order == ("person", "body")
    assert resolved.output_schema == {
        "body": {
            "port_type": "keypoints",
            "point_names": ["body/a", "body/b", "body/c"],
            # A schema with one group gives the group the id of the node.
            "groups": [{"name": "body", "start": 0, "count": 3, "landmark_schema": "Demo3"}],
            "canonical_names": ["body/a", "body/b", "body/c"],
            "geometry": "2d",
            "max_instances": 2,
            "tracked": False,
            "instance_source": "person",
            "edges": [["body/a", "body/b"], ["body/b", "body/c"]],
            "canonical_edges": [["body/a", "body/b"], ["body/b", "body/c"]],
        },
        "person_box": {"port_type": "detections", "class_names": ["person"], "max_instances": 2, "tracked": False, "instance_source": "person"},
        "person_roi": {"port_type": "roi", "max_instances": 2, "tracked": False, "instance_source": "person"},
    }
    person, body = resolved.nodes["person"], resolved.nodes["body"]
    assert (person.model.kind, person.model.key, person.model.version, person.model.precisions) == ("object", OBJECT_KEY, "0.1.0", ("fp32",))
    assert person.model.decode.nms.iou_threshold == 0.5 and person.model.entry.artifact("n", "fp32").available
    assert (body.model.kind, body.model.decode, body.model.size) == ("top_down", None, "m")
    assert [(item.name, item.node, item.port, item.prev) for item in body.inputs] == [("image", "frame", "image", False), ("rois", "person", "rois", False)]
    assert body.inputs_info["rois"] == resolved.port_info("person", "rois") and resolved.port_info("frame", "image") == PortInfo("image")
    assert resolved.warnings == () and resolved.has_onnx_model and not resolved.needs_execution_provider


def test_an_edge_with_a_derived_point_is_not_in_the_edges(tmp_path: Path) -> None:
    sidecar = keypoint_sidecar()
    sidecar["keypoint"]["skeletons"][0]["edges"].append(["mid", "c"])
    root = write_models(tmp_path / "user")
    write_sidecar(root, sidecar)
    assert resolve(config_of(detector_pipeline()), root).output_schema["body"]["edges"] == [["body/a", "body/b"], ["body/b", "body/c"]]


def test_the_output_schema_of_mediapipe_holistic_tasks(tmp_path: Path) -> None:
    resolved = resolve(load_pipeline_file(PACKAGE_PIPELINE_ROOT / "mediapipe-holistic-tasks.pipeline.yaml"), tmp_path)
    schema = resolved.output_schema["holistic"]
    assert len(schema["point_names"]) == 553 and schema["canonical_names"] == schema["point_names"]
    # Each group passes through, so each edge keeps its names.
    assert schema["canonical_edges"] == schema["edges"] and len(schema["edges"]) == 213
    assert all(point in schema["canonical_names"] for edge in schema["canonical_edges"] for point in edge)
    assert [(group["name"], group["count"], group["landmark_schema"]) for group in schema["groups"]] == [
        ("body", 33, None), ("right_hand", 21, None), ("left_hand", 21, None), ("face", 478, None),
    ]
    assert (schema["geometry"], schema["depth_unit"], schema["max_instances"], schema["instance_source"]) == ("3d", "pixel", 1, "holistic")
    assert not resolved.has_onnx_model and not resolved.needs_execution_provider
    assert [resolved.stateful_nodes(mode) for mode in MODES] == [(), (), ()]


def test_the_output_schema_of_yolox_rtmw_wholebody_with_the_package_sidecars(tmp_path: Path) -> None:
    """The graph has `@prev` loops, also the self loop of `detected_box`. The ONNX files can be absent."""
    resolved = resolve(load_pipeline_file(PACKAGE_PIPELINE_ROOT / "yolox-rtmw-wholebody.pipeline.yaml"), tmp_path)
    assert resolved.order == ("trigger", "person", "detected_box", "points_box", "carried_box", "box", "crop", "wholebody")
    schema = resolved.output_schema
    assert schema["wholebody"]["groups"] == [  # the example of `specs/pipeline/outputs.md`
        {"name": "body", "start": 0, "count": 17, "landmark_schema": "COCO_WholeBody"},
        {"name": "feet", "start": 17, "count": 6, "landmark_schema": "COCO_WholeBody"},
        {"name": "face", "start": 23, "count": 68, "landmark_schema": "COCO_WholeBody"},
        {"name": "left_hand", "start": 91, "count": 21, "landmark_schema": "COCO_WholeBody"},
        {"name": "right_hand", "start": 112, "count": 21, "landmark_schema": "COCO_WholeBody"},
    ]
    names = schema["wholebody"]["point_names"]
    assert len(names) == len(set(names)) == 133 and names[0].startswith("body/") and names[-1].startswith("right_hand/")
    assert len(schema["wholebody"]["canonical_names"]) == 137 and schema["wholebody"]["geometry"] == "2d"
    assert "depth_unit" not in schema["wholebody"]
    assert schema["wholebody"]["edges"] and all(a in names and b in names for a, b in schema["wholebody"]["edges"])
    canonical_edges = schema["wholebody"]["canonical_edges"]
    assert len(canonical_edges) == len(schema["wholebody"]["edges"]) == 65
    assert all(point in schema["wholebody"]["canonical_names"] for edge in canonical_edges for point in edge)
    assert ["body/left_ankle", "body/left_big_toe"] in canonical_edges and ["left_hand/wrist", "left_hand/thumb_cmc"] in canonical_edges
    assert schema["person_box"]["class_names"] == ["person"] and schema["person_roi"]["port_type"] == "roi"
    assert [(schema[name]["instance_source"], schema[name]["max_instances"]) for name in ("wholebody", "person_box", "person_roi")] == [("person", 1)] * 3
    assert resolved.nodes["person"].model.decode.nms.post_nms_top_k == 1
    assert resolved.needs_execution_provider and resolved.has_onnx_model
    # The `@prev` consumers, and the temporal nodes upstream of a model. The mode does not change them.
    assert [resolved.stateful_nodes(mode) for mode in MODES] == [("trigger", "detected_box", "points_box", "crop")] * 3


def test_a_node_whose_facts_depend_only_on_prev_values_does_not_resolve(root: Path) -> None:
    loop = [
        {"id": "one", "type": "smooth_roi", "inputs": {"rois": "two.rois@prev"}},
        {"id": "two", "type": "smooth_roi", "inputs": {"rois": "one.rois@prev"}},
    ]
    with pytest.raises(ValueError, match="cannot find the port facts"):
        resolve(config_of(with_nodes(*loop)), root)


def test_a_load_check_of_a_glue_node_keeps_its_rule_id_and_a_load_warning_is_a_pipeline_warning(tmp_path: Path) -> None:
    hand = {"id": "hand", "type": "mediapipe_tasks", "inputs": {"image": "frame.image"}, "params": {"variant": "hand"}}
    merge = {"id": "both", "type": "merge", "inputs": {"target": "mp.keypoints", "source": "hand.keypoints"},
             "params": {"slots": {"mp": "mp/left_wrist"}, "source_anchor": "hand/wrist", "max_distance": 0.2}}
    resolved = resolve(config_of(mediapipe_pipeline(hand, merge, outputs={"both": "both.keypoints"})), tmp_path)
    (warning,) = resolved.warnings
    assert (warning.code, warning.node_ids) == ("merge_unfilled_points", ("both",)) and len(warning.details["points"]) == 33
    assert resolved.nodes["both"].infos is not None  # the `prepare` result of the node module
    merge["params"]["source_anchor"] = "hand/no_point"
    with pytest.raises(ValueError, match="^V-node.merge-2: both"):
        resolve(config_of(mediapipe_pipeline(hand, merge, outputs={"both": "both.keypoints"})), tmp_path)


# ---------------------------------------------------------------------------------------------
# The rules of the node `onnx_model`
# ---------------------------------------------------------------------------------------------


def test_v_node_onnx_model_1_the_sidecar_hash_must_be_the_hash_of_the_file(root: Path, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger=resolve_module.__name__):
        found = resolve(config_of(detector_pipeline()), root).nodes["person"].model.sidecar_sha256
    assert any(found in record.getMessage() for record in caplog.records)  # the loader logs the hash that it resolves
    resolve(config_of(detector_pipeline(sidecar_sha256=found)), root)
    with pytest.raises(ValueError, match=f"^V-node.onnx_model-1: person: .*{'0' * 64}.*{found}"):
        resolve(config_of(detector_pipeline(sidecar_sha256="0" * 64)), root)


def test_v_node_onnx_model_2_the_role_must_match_the_rois_input_and_the_used_ports(root: Path) -> None:
    no_rois = detector_pipeline()
    del no_rois["nodes"][1]["inputs"]["rois"]
    with pytest.raises(ValueError, match="^V-node.onnx_model-2: body: .*needs `rois` input"):
        resolve(config_of(no_rois), root)
    second = {"id": "second", "type": "onnx_model", "inputs": {"image": "frame.image", "rois": "person.rois"},
              "params": {"key": OBJECT_KEY, "size": "n"}}
    with pytest.raises(ValueError, match="^V-node.onnx_model-2: second: .*takes no `rois` input"):
        resolve(config_of(with_nodes(second)), root)
    # An output, an input of a node and a tap use a port.
    with pytest.raises(ValueError, match=r"^V-node.onnx_model-2: person: .*\['keypoints'\]"):
        resolve(config_of(with_nodes(outputs={"points": "person.keypoints"})), root)
    smooth = {"id": "smooth", "type": "smooth_roi", "inputs": {"rois": "body.rois"}}
    with pytest.raises(ValueError, match=r"^V-node.onnx_model-2: body: .*\['rois'\]"):
        resolve(config_of(with_nodes(smooth)), root)
    tapped = detector_pipeline()
    tapped["instrumentation"] = {"taps": [{"action": "record", "port": "body.detections", "name": "boxes"}]}
    with pytest.raises(ValueError, match=r"^V-node.onnx_model-2: body: .*\['detections'\]"):
        resolve(config_of(tapped), root)


@pytest.mark.parametrize(
    "changes",
    [
        {"no_field": 1},
        {"nms": {"no_field": 1}},
        {"min_score": "high"},
        {"min_score": 2},
        {"nms": {"post_nms_top_k": 0}},
        {"nms": 3},
        {"box_format": "xyzw"},
        {"scores_output": "no_output"},
        {"min_box_size": None},
    ],
)
def test_v_node_onnx_model_3_each_name_of_object_decode_must_be_a_field_of_the_sidecar_block(root: Path, changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="^V-node.onnx_model-3: person: "):
        resolve(config_of(detector_pipeline(object_decode=changes)), root)


def test_v_node_onnx_model_3_the_changes_nest_and_each_other_field_keeps_the_value_of_the_sidecar(root: Path) -> None:
    changes = {"min_score": 0.25, "nms": {"post_nms_top_k": 1}}
    decode = resolve(config_of(detector_pipeline(object_decode=changes)), root).nodes["person"].model.decode
    assert (decode.min_score, decode.nms.post_nms_top_k, decode.nms.iou_threshold, decode.scores_output) == (0.25, 1, 0.5, "scores")
    assert load_detector_sidecar(OBJECT_KEY, root).object.decode.nms.post_nms_top_k is None  # the sidecar does not change
    on_keypoints = detector_pipeline()
    on_keypoints["nodes"][1]["params"]["object_decode"] = {"min_score": 0.5}
    with pytest.raises(ValueError, match="^V-node.onnx_model-3: body: .*no object.decode block"):
        resolve(config_of(on_keypoints), root)


def test_v_node_onnx_model_4_the_size_and_the_precision_must_be_in_the_sidecar(root: Path) -> None:
    with pytest.raises(ValueError, match=r"^V-node.onnx_model-4: person: size 'xl' .*\['n'\]"):
        resolve(config_of(detector_pipeline(size="xl")), root)
    with pytest.raises(ValueError, match=r"^V-node.onnx_model-4: person: .*no precision fp16.*\['fp32'\]"):
        resolve(config_of(detector_pipeline(precision="fp16")), root)
    resolve(config_of(detector_pipeline(precision="fp32")), root)


def test_v_node_onnx_model_5_max_instances_must_not_be_more_than_the_limit_of_the_model(root: Path) -> None:
    # `selection: nms` with no `post_nms_top_k`: the row count Q = 3 of the primary output.
    resolve(config_of(detector_pipeline(max_instances=3)), root)
    with pytest.raises(ValueError, match="^V-node.onnx_model-5: person: max_instances 4 .*limit 3"):
        resolve(config_of(detector_pipeline(max_instances=4)), root)
    # A change of `post_nms_top_k` in `object_decode` sets the limit.
    resolve(config_of(detector_pipeline(max_instances=2, object_decode={"nms": {"post_nms_top_k": 2}})), root)
    with pytest.raises(ValueError, match="^V-node.onnx_model-5: person: max_instances 2 .*limit 1"):
        resolve(config_of(detector_pipeline(max_instances=2, object_decode={"nms": {"post_nms_top_k": 1}})), root)


def test_a_key_that_the_catalog_does_not_have_is_an_error_that_names_the_node_and_the_key(root: Path) -> None:
    with pytest.raises(ValueError, match="^person: key 'other@demo-exporter': the catalog has no entry"):
        resolve(config_of(detector_pipeline(key="other@demo-exporter")), root)
    with pytest.raises(ValueError, match="^person: key 'demo@demo-exporter==9.0': the catalog has no version"):
        resolve(config_of(detector_pipeline(key=f"{OBJECT_KEY}==9.0")), root)
    resolve(config_of(detector_pipeline(key=f"{OBJECT_KEY}==0.1.0")), root)


def test_a_model_that_the_generic_detectors_do_not_run_is_an_error_that_names_the_node(tmp_path: Path) -> None:
    root = write_models(tmp_path / "user")
    write_sidecar(root, BASES["top_k"]())  # the key of the object detector, with `selection: top_k`
    with pytest.raises(ValueError, match="^person: this release does not run .*post.object.selection.top_k"):
        resolve(config_of(detector_pipeline()), root)
    write_sidecar(root, object_sidecar())
    bottom_up = keypoint_sidecar()
    bottom_up["keypoint"]["estimator_type"] = "bottom_up"
    write_sidecar(root, bottom_up)
    with pytest.raises(ValueError, match="^body: this release does not run .*post.keypoint.bottom_up"):
        resolve(config_of(detector_pipeline()), root)
    broken = keypoint_sidecar()
    del broken["keypoint"]["geometry"]
    write_sidecar(root, broken)
    with pytest.raises(ValueError, match=f"^body: the sidecar of '{KEYPOINT_KEY}' does not load"):
        resolve(config_of(detector_pipeline()), root)


def test_a_model_with_both_roles_is_an_error_that_names_the_node(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No sidecar of the tests has both roles and only sections that the package runs, so the test changes the loaded model."""
    scan = resolve_module.scan_sidecar_roots

    def both_roles(user_root: Any) -> list[Any]:
        found = scan(user_root)
        for sidecar in found:
            if sidecar.key == OBJECT_KEY:
                sidecar.model = sidecar.model.model_copy(update={"role": ["object_detector", "keypoint_detector"]})
        return found

    monkeypatch.setattr(resolve_module, "scan_sidecar_roots", both_roles)
    with pytest.raises(ValueError, match="^person: this release does not run .*a model with both roles"):
        resolve(config_of(detector_pipeline()), root)


# ---------------------------------------------------------------------------------------------
# The rules of the graph and of the outputs
# ---------------------------------------------------------------------------------------------


def test_v_pipeline_graph_8_a_point_name_of_a_sidecar_must_have_no_slash_and_no_whitespace(root: Path) -> None:
    """The sidecar loader refuses such a name in a schema file, so the test changes the loaded model."""
    keypoint = load_detector_sidecar(KEYPOINT_KEY, root).keypoint
    schema = load_landmark_schema_registry(root)["Demo3"]
    rois = PortInfo("roi", max_instances=1, instance_source="person")
    assert keypoint_port_info("body", keypoint, schema, rois).point_names == ("body/a", "body/b", "body/c")
    for bad in ("a/b", "a b", "a\tb"):
        with pytest.raises(ValueError, match="^V-pipeline.graph-8: body: "):
            keypoint_port_info("body", keypoint.model_copy(update={"point_names": [bad, "b", "c"]}), schema, rois)


def test_v_pipeline_graph_10_the_groups_that_the_nodes_make_must_have_unique_names(tmp_path: Path) -> None:
    holistic = {"variant": "holistic"}
    other = {"id": "other", "type": "mediapipe_tasks", "inputs": {"image": "frame.image"}, "params": holistic}
    outputs = {"one": "mp.keypoints", "two": "other.keypoints"}
    with pytest.raises(ValueError, match="^V-pipeline.graph-10: the nodes mp and other both make the group 'body'"):
        resolve(config_of(mediapipe_pipeline(other, outputs=outputs, **holistic)), tmp_path)
    # A variant with one group gives the group the id of its node.
    other["params"] = {"variant": "body"}
    resolve(config_of(mediapipe_pipeline(other, outputs=outputs)), tmp_path)
    # An adding slot of a `merge` node makes a group. A replacing slot makes none.
    hand = {"id": "hand", "type": "mediapipe_tasks", "inputs": {"image": "frame.image"}, "params": {"variant": "hand"}}
    merge = {"id": "both", "type": "merge", "inputs": {"target": "mp.keypoints", "source": "hand.keypoints"},
             "params": {"slots": {"hand": "mp/left_wrist"}, "source_anchor": "hand/wrist", "max_distance": 0.2}}
    with pytest.raises(ValueError, match="^V-pipeline.graph-10: the nodes hand and both both make the group 'hand'"):
        resolve(config_of(mediapipe_pipeline(hand, merge, outputs={"both": "both.keypoints"})), tmp_path)
    merge["params"]["slots"] = {"left": "mp/left_wrist", "mp": "mp/right_wrist"}
    resolve(config_of(mediapipe_pipeline(hand, merge, outputs={"both": "both.keypoints"})), tmp_path)


@pytest.mark.parametrize(
    "node",
    [
        {"id": "temporal", "type": "smooth_roi", "inputs": {"rois": "person.rois"}},
        {"id": "temporal", "type": "smooth_keypoints", "inputs": {"keypoints": "body.keypoints"}},
        {"id": "temporal", "type": "redetect_trigger", "inputs": {"image": "frame.image", "previous_rois": "person.rois@prev"}},
    ],
)
def test_v_pipeline_graph_11_each_input_of_a_temporal_node_must_have_one_row(root: Path, node: dict[str, Any]) -> None:
    resolve(config_of(with_nodes(node)), root)
    with pytest.raises(ValueError, match="^V-pipeline.graph-11: temporal: .*I = 2"):
        resolve(config_of(with_nodes(node, max_instances=2)), root)


def test_v_pipeline_graph_11_each_prev_input_must_have_one_row(root: Path, tmp_path: Path) -> None:
    hold = {"id": "hold", "type": "roi_hold", "inputs": {"previous": "hold.rois@prev", "current": "person.rois"}}
    resolve(config_of(with_nodes(hold)), root)
    with pytest.raises(ValueError, match="^V-pipeline.graph-11: hold: the input hold.rois@prev has I = 2"):
        resolve(config_of(with_nodes(hold, max_instances=2)), root)
    # The same input with no `@prev` is not an input of a temporal node: I can be more than 1.
    hold["inputs"]["previous"] = "person.rois"
    resolve(config_of(with_nodes(hold, max_instances=2)), root)
    box = {"id": "box", "type": "roi_from_points", "inputs": {"keypoints": "mp.keypoints@prev"}}
    resolve(config_of(mediapipe_pipeline(box, outputs={"box": "box.rois"})), tmp_path)
    with pytest.raises(ValueError, match="^V-pipeline.graph-11: box: the input mp.keypoints@prev has I = 2"):
        resolve(config_of(mediapipe_pipeline(box, outputs={"box": "box.rois"}, max_instances=2)), tmp_path)


def test_v_pipeline_outputs_2_each_point_name_of_an_output_must_be_unique(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The nodes of the package give no repeated name, so the test changes the facts of a node."""
    config = config_of(mediapipe_pipeline(outputs={"points": "mp.keypoints"}))
    resolve(config, tmp_path)
    output_info = mediapipe_tasks.output_info

    def repeated(node_id: str, params: Any, inputs: Any = None) -> Any:
        ports, warnings = output_info(node_id, params, inputs)
        names = ports["keypoints"].point_names
        return {"keypoints": PortInfo(**{**vars(ports["keypoints"]), "point_names": (names[1], *names[1:])})}, warnings

    monkeypatch.setattr(mediapipe_tasks, "output_info", repeated)
    with pytest.raises(ValueError, match="^V-pipeline.outputs-2: the output 'points' .*mp/left_eye_inner"):
        resolve(config, tmp_path)


# ---------------------------------------------------------------------------------------------
# Stateful pipelines and the execution provider
# ---------------------------------------------------------------------------------------------


def test_a_smooth_keypoints_node_after_the_last_model_does_not_make_a_pipeline_stateful(root: Path) -> None:
    smooth = {"id": "smooth", "type": "smooth_keypoints", "inputs": {"keypoints": "body.keypoints"}}
    resolved = resolve(config_of(with_nodes(smooth, outputs={"body": "smooth.keypoints"})), root)
    assert [resolved.stateful_nodes(mode) for mode in MODES] == [(), (), ()]
    # A temporal node upstream of a model, and a node with an `@prev` input, make it stateful.
    data = with_nodes({"id": "crop", "type": "smooth_roi", "inputs": {"rois": "person.rois"}}, smooth)
    data["nodes"][1]["inputs"]["rois"] = "crop.rois"
    assert resolve(config_of(data), root).stateful_nodes("video") == ("crop",)
    hold = {"id": "hold", "type": "roi_hold", "inputs": {"previous": "hold.rois@prev", "current": "person.rois"}}
    assert resolve(config_of(with_nodes(hold)), root).stateful_nodes("image") == ("hold",)


def test_a_mediapipe_tasks_node_upstream_of_a_model_is_temporal_only_in_video_and_live(root: Path) -> None:
    data = mediapipe_pipeline(
        {"id": "box", "type": "roi_from_points", "inputs": {"keypoints": "mp.keypoints"}},
        {"id": "body", "type": "onnx_model", "inputs": {"image": "frame.image", "rois": "box.rois"}, "params": {"key": KEYPOINT_KEY, "size": "m"}},
        outputs={"body": "body.keypoints"},
    )
    resolved = resolve(config_of(data), root)
    assert [resolved.stateful_nodes(mode) for mode in MODES] == [(), ("mp",), ("mp",)]
    assert resolved.output_schema["body"]["instance_source"] == "mp"


def test_needs_execution_provider_is_true_when_an_onnx_model_node_has_no_execution_provider(root: Path, tmp_path: Path) -> None:
    data = detector_pipeline()
    assert not resolve(config_of(data), root).needs_execution_provider and not check_pipeline(config_of(data), user_root=root).needs_execution_provider
    del data["nodes"][1]["params"]["execution_provider"]
    resolved = resolve(config_of(data), root)
    assert resolved.needs_execution_provider and resolved.has_onnx_model
    assert check_pipeline(config_of(data), user_root=root).needs_execution_provider
    no_model = resolve(config_of(mediapipe_pipeline(outputs={"points": "mp.keypoints"})), tmp_path)
    assert not no_model.needs_execution_provider and not no_model.has_onnx_model


# ---------------------------------------------------------------------------------------------
# The warning `missing_dependency`, the load, the catalog and the export
# ---------------------------------------------------------------------------------------------


def write_pipeline(root: Path, data: dict[str, Any]) -> Path:
    import yaml

    path = root / "pipelines" / f"{data['pipeline_id']}.pipeline.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_an_onnx_file_that_is_absent_gives_the_warning_missing_dependency_and_the_pipeline_loads(tmp_path: Path) -> None:
    root = write_models(tmp_path / "user", files=False)
    write_pipeline(root, detector_pipeline())
    config = load_pipeline("demo-models@demo-source", user_root=root)  # a load gives the warning; it is not an error
    check = check_pipeline(config, user_root=root)
    assert [(warning.code, warning.node_ids, warning.details["files"]) for warning in check.warnings] == [
        ("missing_dependency", ("person",), ["demo-n_b3_fp32.onnx"]),
        ("missing_dependency", ("body",), ["demo-body-m_b3_fp32.onnx"]),
    ]
    assert "is not present" in check.warnings[0].message and check.output_schema["body"]["max_instances"] == 1
    (entry,) = [entry for entry in list_pipelines(root) if entry.key == "demo-models@demo-source"]
    assert not entry.available and "demo-n_b3_fp32.onnx" in entry.unavailable_reason and entry.warnings == check.warnings
    assert find_pipeline("demo-models@demo-source", root) == entry and entry.needs_execution_provider is False


def test_an_onnx_file_with_a_different_hash_gives_the_warning_missing_dependency(tmp_path: Path) -> None:
    root = write_models(tmp_path / "user")
    (root / "detectors" / "object_detectors" / "demo" / "demo-n_b3_fp32.onnx").write_bytes(b"other bytes")
    (warning,) = resolve(config_of(detector_pipeline()), root).warnings
    assert (warning.code, warning.node_ids, warning.details) == ("missing_dependency", ("person",), {"files": ["demo-n_b3_fp32.onnx"], "key": OBJECT_KEY})


def test_an_extra_that_is_not_installed_gives_the_warning_missing_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = mediapipe_pipeline(outputs={"points": "mp.keypoints"})
    write_pipeline(tmp_path, data)
    assert resolve(config_of(data), tmp_path).warnings == () or mediapipe_tasks.missing_extra() is not None
    monkeypatch.setattr(mediapipe_tasks, "missing_extra", lambda: "mediapipe")
    (warning,) = check_pipeline(load_pipeline(data), user_root=tmp_path).warnings
    assert (warning.code, warning.node_ids, warning.details) == ("missing_dependency", ("mp",), {"extra": "mediapipe"})
    (entry,) = [entry for entry in list_pipelines(tmp_path) if entry.key == "demo-models@demo-source"]
    assert not entry.available and "the extra `mediapipe` is not installed" in entry.unavailable_reason


def test_a_load_runs_the_load_checks_and_the_catalog_gives_the_reason(root: Path) -> None:
    data = detector_pipeline(max_instances=4)
    with pytest.raises(ValueError, match="^V-node.onnx_model-5"):
        load_pipeline(data, user_root=root)
    path = write_pipeline(root, data)
    with pytest.raises(ValueError, match="^V-node.onnx_model-5"):
        load_pipeline(path, user_root=root)
    (entry,) = [entry for entry in list_pipelines(root) if entry.key == "demo-models@demo-source"]
    assert not entry.available and entry.unavailable_reason.startswith("V-node.onnx_model-5") and entry.needs_execution_provider is None
    write_pipeline(root, detector_pipeline())
    (entry,) = [entry for entry in list_pipelines(root) if entry.key == "demo-models@demo-source"]
    assert entry.available and entry.warnings == () and entry.needs_execution_provider is False


def test_an_export_gives_the_sidecar_hash_of_each_onnx_model_node(root: Path) -> None:
    config = load_pipeline(detector_pipeline(), user_root=root)
    hashes = {node_id: node.model.sidecar_sha256 for node_id, node in resolve(config, root).nodes.items()}
    for resolved in (False, True):
        written = export_pipeline(config, resolved, user_root=root)
        assert {node["id"]: node["params"]["sidecar_sha256"] for node in written["nodes"]} == hashes
        assert load_pipeline(written, user_root=root).nodes[0].params.sidecar_sha256 == hashes["person"]
    written = export_pipeline(config, user_root=root)
    assert written == export_pipeline(load_pipeline(written, user_root=root), user_root=root)
    del written["nodes"][0]["params"]["sidecar_sha256"], written["nodes"][1]["params"]["sidecar_sha256"]
    assert written == detector_pipeline()  # the export as written adds only the hashes


_NO_RUNTIME_AT_LOAD = """
import sys
from pathlib import Path
from skellytracker.core.model_spec import artifacts
from skellytracker.core.pipelines import catalog
from skellytracker.core.pipelines.loading import load_pipeline
artifacts.default_hash_cache_path = lambda: Path(sys.argv[1]) / "hash-cache.json"
for path in sorted(catalog.PACKAGE_PIPELINE_ROOT.glob("*.pipeline.yaml")):
    load_pipeline(path, user_root=Path(sys.argv[1]))
print("LOADED", sorted(m for m in sys.modules if m.split(".")[0] in ("mediapipe", "onnxruntime")), flush=True)
"""


def test_a_load_of_the_built_ins_loads_no_onnxruntime_and_no_mediapipe(tmp_path: Path) -> None:
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", _NO_RUNTIME_AT_LOAD, str(tmp_path)], capture_output=True, text=True, timeout=120,
    )
    assert result.stdout.strip().splitlines()[-1] == "LOADED []", result.stderr[-2000:]
