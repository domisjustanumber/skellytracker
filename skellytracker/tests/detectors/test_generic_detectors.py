"""The generic detectors, on tiny ONNX models that `onnx.helper` makes, with sidecars in a temporary root."""
from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import onnx
import pytest

from skellytracker.core.detectors import catalog  # noqa: E402
from skellytracker.core.detectors.catalog import DetectorUnavailableError, get_detector, load_detector_sidecar  # noqa: E402
from skellytracker.core.detectors.generic import (  # noqa: E402

    GenericKeypointDetector,
    GenericObjectDetector,
    create_detector,
    download,
    open_session,
    overlay_edges,
    overlay_groups,
)
from skellytracker.core.detectors.generic.inference import session_batch  # noqa: E402
from skellytracker.core.errors import VRAMExhaustionError  # noqa: E402
from skellytracker.core.model_spec import artifacts  # noqa: E402
from skellytracker.core.model_spec.model import BatchingSpec, ResizeSpec  # noqa: E402
from skellytracker.tests.detectors.onnx_models import keypoint_model, object_model  # noqa: E402
from skellytracker.tests.detectors.test_generic_download import fake_fetch, zipped  # noqa: E402
from skellytracker.tests.model_spec.sidecars import BASES, SCORE_MAP, _size, write_yaml  # noqa: E402

OBJECT_KEY = "demo@demo-exporter"
KEYPOINT_KEY = "demo-body@demo-exporter"


@pytest.fixture(autouse=True)
def private_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(artifacts, "default_hash_cache_path", lambda: tmp_path / "cache" / "hash-cache.json")
    monkeypatch.setattr(artifacts, "download_root", lambda: tmp_path / "cache" / "models")
    monkeypatch.delenv(catalog.USER_ROOT_VARIABLE, raising=False)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "user"


def object_sidecar() -> dict[str, Any]:
    sidecar = BASES["nms"]()
    sidecar["object"]["decode"]["nms"] = {"iou_threshold": 0.5, "score_threshold": 0.01}
    sidecar["sizes"] = {"n": _size("demo", "n", 32, 32, [[3, 3, 4], [3, 3]])}
    return sidecar


def keypoint_sidecar() -> dict[str, Any]:
    sidecar = BASES["simcc"]()
    sidecar["keypoint"]["derived_points"] = {"mid": ["a", "b"]}
    sidecar["sizes"] = {"m": {**_size("demo-body", "m", 16, 12, [[3, 3, 24], [3, 3, 32]]), "score_map": dict(SCORE_MAP)}}
    return sidecar


def put(root: Path, sidecar: dict[str, Any], content: bytes, files: bool = True) -> Path:
    """Write a sidecar with the hash of `content`, and its ONNX files. Return the folder of the sidecar."""
    kind = "keypoint_detectors/demo/body" if "keypoint" in sidecar else "object_detectors/demo"
    folder = root / "detectors" / kind
    folder.mkdir(parents=True, exist_ok=True)
    if "keypoint" in sidecar:
        write_yaml(root / "landmark_schemas" / "Demo3.yaml", {"name": "Demo3", "source": "test", "groups": [{"name": "body", "points": ["a", "b", "c"]}]})
    for size in sidecar["sizes"].values():
        for artifact in size["onnx"]["precision_artifacts"].values():
            artifact["sha256"] = hashlib.sha256(content).hexdigest()
            if files:
                (folder / artifact["filename"]).write_bytes(content)
    write_yaml(folder / f"{sidecar['model_id']}.yaml", sidecar)
    return folder


def frame(value: int, height: int = 32, width: int = 32) -> np.ndarray:
    return np.full((height, width, 3), value, np.uint8)


# ---------------------------------------------------------------------------------------------
# The object detector, the batch loop and the batch conversion
# ---------------------------------------------------------------------------------------------


def test_the_object_detector_runs_a_catalog_entry_on_a_batch_of_images(root: Path) -> None:
    put(root, object_sidecar(), object_model())
    assert get_detector(OBJECT_KEY, root).available
    detector = create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)
    assert isinstance(detector, GenericObjectDetector) and detector.size == "n" and session_batch(detector.session) == 3
    # Four images through a batch-3 session: two groups, and zero tensors fill the second group.
    ones, twos, large, dark = detector.detect([frame(1), frame(2), frame(1, 64, 64), frame(0)])
    np.testing.assert_allclose(ones.boxes, [[2, 2, 10, 10], [20, 20, 30, 30]])
    np.testing.assert_allclose(ones.scores, [0.9, 0.75], rtol=1e-6)
    assert ones.class_indices.tolist() == [0, 0] and detector.classes == ["person"]
    np.testing.assert_allclose(twos.scores, [1.8, 1.5], rtol=1e-6)  # the scores of this graph follow the image
    np.testing.assert_allclose(large.boxes, [[4, 4, 20, 20], [40, 40, 60, 60]])  # the letterbox scale 0.5 is unprojected
    assert dark.boxes.shape == (0, 4) and dark.scores.shape == (0,)
    assert detector.detect([]) == []


def test_the_decode_fields_of_the_sidecar_and_the_caller_control_the_decode(root: Path) -> None:
    put(root, object_sidecar(), object_model())
    sidecar = load_detector_sidecar(OBJECT_KEY, root)
    session = create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root).session
    (strict,) = GenericObjectDetector(sidecar, "n", "fp32", session).detect([frame(1)], min_score=0.8)
    np.testing.assert_allclose(strict.scores, [0.9], rtol=1e-6)
    no_nms = sidecar.object.decode.model_copy(update={"nms": sidecar.object.decode.nms.model_copy(update={"iou_threshold": 0.9})})
    (loose,) = GenericObjectDetector(sidecar, "n", "fp32", session, no_nms).detect([frame(1)])
    np.testing.assert_allclose(loose.scores, [0.9, 0.8, 0.75], rtol=1e-6)
    with pytest.raises(ValueError, match="no size 'xl'"):
        GenericObjectDetector(sidecar, "xl", "fp32", session)
    with pytest.raises(ValueError, match="selection: top_k"):
        GenericObjectDetector(sidecar, "n", "fp32", session, sidecar.object.decode.model_copy(update={"selection": "top_k"}))


@pytest.mark.parametrize("batch", [1, 2, 5])
def test_the_batch_conversion_at_session_start_gives_a_session_at_the_batch_of_the_request(root: Path, batch: int) -> None:
    put(root, object_sidecar(), object_model())
    detector = create_detector(OBJECT_KEY, execution_provider="cpu", batch=batch, user_root=root)
    assert session_batch(detector.session) == batch
    results = detector.detect([frame(1), frame(2), frame(1)])
    np.testing.assert_allclose([result.scores[0] for result in results], [0.9, 1.8, 0.9], rtol=1e-6)


def test_the_session_report_names_the_execution_provider_and_the_artifact(root: Path) -> None:
    put(root, object_sidecar(), object_model())
    entry, sidecar = get_detector(OBJECT_KEY, root), load_detector_sidecar(OBJECT_KEY, root)
    session, report = open_session(entry, sidecar, "n", "fp32", execution_provider="cpu", batch=3)
    assert session_batch(session) == 3
    assert (report.requested_ep, report.precision, report.artifact_sha256) == ("cpu", "fp32", entry.artifact("n", "fp32").sha256)
    one_batch = sidecar.model_copy(update={"batching": BatchingSpec(batch=1)})
    with pytest.raises(ValueError, match="no batching.batch_conversion"):
        open_session(entry, one_batch, "n", "fp32", execution_provider="cpu", batch=2)


# ---------------------------------------------------------------------------------------------
# The keypoint detector and the overlay
# ---------------------------------------------------------------------------------------------


def test_the_keypoint_detector_runs_a_top_down_model_on_a_batch_of_crops(root: Path) -> None:
    put(root, keypoint_sidecar(), keypoint_model())
    detector = create_detector(KEYPOINT_KEY, execution_provider="cpu", user_root=root)
    assert isinstance(detector, GenericKeypointDetector) and detector.takes_crops
    assert (detector.point_names, detector.derived_names) == (["a", "b", "c"], ["mid"])
    image = np.random.default_rng(0).integers(0, 256, (120, 100, 3), dtype=np.uint8)
    # The ROI 30 x 40 with expand_ratio 1.25 is a crop of 37.5 x 50, which has the aspect of the 12 x 16 input.
    centres = [(50.0, 60.0), (40.0, 70.0), (60.0, 50.0), (55.0, 65.0)]
    found = detector.detect([image] * 4, [(c_x, c_y, 30.0, 40.0, 0.0) for c_x, c_y in centres])
    assert found.keypoints.shape == (4, 3, 2) and found.scores.shape == (4, 3)
    for index, (c_x, c_y) in enumerate(centres):
        np.testing.assert_allclose(found.keypoints[index, 0], [c_x, c_y], atol=1e-4)
        np.testing.assert_allclose(found.keypoints[index, 1], [c_x - 18.75, c_y - 25], atol=1e-4)
        assert np.isnan(found.keypoints[index, 2]).all()
        np.testing.assert_allclose(found.derived_keypoints[index, 0], [c_x - 9.375, c_y - 12.5], atol=1e-4)
    np.testing.assert_allclose(found.raw_scores, [[3, 2, 0]] * 4)
    # SCORE_MAP is a = 1, b = 0: the mapped score is 1 / (1 + exp(-raw)); a missing point keeps 0.
    mapped = [1 / (1 + np.exp(-3.0)), 1 / (1 + np.exp(-2.0)), 0]
    assert found.scores.dtype == np.float32
    np.testing.assert_allclose(found.scores, [mapped] * 4, rtol=1e-6)
    np.testing.assert_allclose(found.derived_scores, [[mapped[1]]] * 4, rtol=1e-6)
    with pytest.raises(ValueError, match="needs rois"):
        detector.detect([image])
    empty = detector.detect([], [])
    assert empty.keypoints.shape == (0, 3, 2) and empty.derived_scores.shape == (0, 1)


def test_a_bottom_up_model_takes_the_full_image(root: Path) -> None:
    put(root, keypoint_sidecar(), keypoint_model())
    top_down = load_detector_sidecar(KEYPOINT_KEY, root)
    session = create_detector(KEYPOINT_KEY, execution_provider="cpu", user_root=root).session
    model = top_down.model_copy(update={
        "keypoint": top_down.keypoint.model_copy(update={"estimator_type": "bottom_up"}),
        "input": top_down.input.model_copy(update={"resize": ResizeSpec(method="stretch")}),
    })
    detector = GenericKeypointDetector(model, "m", "fp32", session)
    assert not detector.takes_crops
    found = detector.detect([frame(7, 160, 120)])
    np.testing.assert_allclose(found.keypoints[0, :2], [[60, 80], [0, 0]])  # the stretch 12 x 16 to 120 x 160
    with pytest.raises(ValueError, match="takes no rois"):
        detector.detect([frame(7)], [(1.0, 1.0, 2.0, 2.0, 0.0)])
    # The catalog gives no bottom-up model yet: the section of its decode has no processing module.
    sidecar = keypoint_sidecar()
    sidecar["keypoint"]["estimator_type"] = "bottom_up"
    put(root, sidecar, keypoint_model())
    with pytest.raises(DetectorUnavailableError, match="post.keypoint.bottom_up"):
        create_detector(KEYPOINT_KEY, execution_provider="cpu", user_root=root)


def test_the_overlay_groups_come_from_the_parts_and_the_skeleton(root: Path) -> None:
    sidecar = keypoint_sidecar()
    sidecar["keypoint"]["skeletons"].append({"name": "full", "edges": [["a", "b"], ["b", "c"], ["a", "c"]]})
    sidecar["keypoint"]["overlay"] = {
        "skeleton": "full",
        "keypoint_color": [1, 2, 3],
        "parts": {
            "rest": {"edge_color": [0, 255, 0]},
            "picked": {"edges": [["c", "b"]], "edge_color": [255, 0, 0], "edge_thickness": 3, "keypoint_color": [9, 9, 9]},
            "c_side": {"prefix": "c", "edge_color": [0, 0, 255]},
        },
    }
    put(root, sidecar, keypoint_model())
    keypoint = load_detector_sidecar(KEYPOINT_KEY, root).keypoint
    assert overlay_edges(keypoint) == (("a", "b"), ("b", "c"), ("a", "c"))
    groups = {group.name: group for group in overlay_groups(keypoint)}
    assert list(groups) == ["rest", "picked", "c_side"]
    assert groups["picked"].edges == (("b", "c"),) and groups["c_side"].edges == (("a", "c"),) and groups["rest"].edges == (("a", "b"),)
    assert (groups["picked"].edge_thickness, groups["picked"].keypoint_color) == (3, (9.0, 9.0, 9.0))
    assert (groups["rest"].edge_thickness, groups["rest"].keypoint_color, groups["rest"].edge_color) == (2, (1.0, 2.0, 3.0), (0.0, 255.0, 0.0))
    no_overlay = keypoint.model_copy(update={"overlay": None})
    assert overlay_edges(no_overlay) == (("a", "b"), ("b", "c")) and overlay_groups(no_overlay) == ()


# ---------------------------------------------------------------------------------------------
# The capability check and the download
# ---------------------------------------------------------------------------------------------


def test_a_sidecar_with_a_section_that_the_package_does_not_run_gives_no_detector(root: Path) -> None:
    put(root, BASES["top_k"](), b"no graph")
    with pytest.raises(DetectorUnavailableError, match="post.object.selection.top_k"):
        create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)


def test_a_missing_file_with_no_url_gives_no_detector(root: Path) -> None:
    put(root, object_sidecar(), object_model(), files=False)
    with pytest.raises(DetectorUnavailableError, match="is not present"):
        create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)


def url_sidecar(served: bytes) -> dict[str, Any]:
    sidecar = object_sidecar()
    sidecar["sizes"]["n"]["onnx"]["precision_artifacts"]["fp32"].update(
        url="https://example.org/demo.bin", url_sha256=hashlib.sha256(served).hexdigest()
    )
    return sidecar


@pytest.mark.parametrize("archive", [False, True])
def test_a_session_downloads_a_url_artifact_that_is_not_present(root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, archive: bool) -> None:
    model = object_model()
    served = zipped({"end2end.onnx": model}) if archive else model
    put(root, url_sidecar(served), model, files=False)
    calls: list[str] = []
    monkeypatch.setattr(download, "fetch", fake_fetch(served, calls))
    before = get_detector(OBJECT_KEY, root)
    assert before.available and not before.artifact("n", "fp32").downloaded

    detector = create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)
    file = tmp_path / "cache" / "models" / OBJECT_KEY / "0.1.0" / "demo-n_b3_fp32.onnx"
    assert file.read_bytes() == model and [item.name for item in file.parent.iterdir()] == [file.name]
    assert len(detector.detect([frame(1)])[0].scores) == 2

    # The download wrote the record of the hash check cache: the catalog does not read the file again.
    monkeypatch.setattr(artifacts, "file_sha256", lambda path: pytest.fail(f"hashed {path} again"))
    after = get_detector(OBJECT_KEY, root)
    assert after.available and after.artifact("n", "fp32").downloaded and after.artifact("n", "fp32").path == file
    create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)
    assert calls == ["https://example.org/demo.bin"]


# ---------------------------------------------------------------------------------------------
# Threads
# ---------------------------------------------------------------------------------------------


def echo_model() -> bytes:
    """A graph whose output `echo` is its input `input`, with a dynamic batch: ONNX Runtime can give the output the input buffer."""
    helper, proto = onnx.helper, onnx.TensorProto
    graph = helper.make_graph(
        [helper.make_node("Identity", ["input"], ["echo"])], "echo",
        [helper.make_tensor_value_info("input", proto.FLOAT, ["N", 3, 32, 32])], [helper.make_tensor_value_info("echo", proto.FLOAT, ["N", 3, 32, 32])],
    )
    return helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)], ir_version=8).SerializeToString()


def test_an_output_of_the_batch_loop_does_not_change_when_the_next_call_writes_the_batch() -> None:
    """The batch of `BatchPreprocessor` is the array of its next call: no output of `run_batches` can share its memory."""
    from skellytracker.core.detectors.generic.inference import run_batches
    from skellytracker.core.detectors.processing.pre.preprocess import BatchPreprocessor
    from skellytracker.core.eps import build_session
    from skellytracker.core.model_spec.model import SidecarModel

    sidecar = SidecarModel.model_validate(object_sidecar())
    sidecar = sidecar.model_copy(update={"outputs": [sidecar.outputs[0].model_copy(update={"name": "echo"})]})
    session, _ = build_session(echo_model(), execution_provider="cpu")
    preprocessor = BatchPreprocessor(sidecar, "n", "fp32")
    batch, _ = preprocessor.preprocess([frame(1), frame(2), frame(3)])
    first = run_batches(session, sidecar, batch)["echo"]
    kept = first.copy()
    assert np.array_equal(first, batch) and not np.shares_memory(first, batch)
    second_batch, _ = preprocessor.preprocess([frame(9), frame(8), frame(7)])
    assert np.shares_memory(batch, second_batch) and not np.array_equal(batch, kept)  # the next call wrote the batch
    assert np.array_equal(first, kept)


def test_a_result_that_the_caller_keeps_does_not_change_at_the_next_call(root: Path) -> None:
    put(root, object_sidecar(), object_model())
    detector = create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)
    first = detector.detect([frame(1), frame(2)])
    kept = [(found.boxes.copy(), found.scores.copy()) for found in first]
    detector.detect([frame(3), frame(4), frame(5)])
    for found, (boxes, scores) in zip(first, kept, strict=True):
        assert np.array_equal(found.boxes, boxes) and np.array_equal(found.scores, scores)
    put(root, keypoint_sidecar(), keypoint_model())
    keypoints = create_detector(KEYPOINT_KEY, execution_provider="cpu", user_root=root)
    image = np.random.default_rng(0).integers(0, 256, (120, 100, 3), dtype=np.uint8)
    found = keypoints.detect([image] * 2, [(50.0, 60.0, 30.0, 40.0, 0.0), (40.0, 70.0, 30.0, 40.0, 0.0)])
    kept_points = found.keypoints.copy()
    keypoints.detect([image], [(60.0, 50.0, 30.0, 40.0, 0.5)])
    assert np.array_equal(found.keypoints, kept_points, equal_nan=True)


def test_a_detector_made_on_one_thread_runs_on_other_threads_and_closes_from_an_other_thread(root: Path) -> None:
    put(root, object_sidecar(), object_model())
    detector = create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda value: detector.detect([frame(value)] * 4), [1, 2] * 8))
        for value, found in zip([1, 2] * 8, results, strict=True):
            np.testing.assert_allclose([item.scores[0] for item in found], [0.9 * value] * 4, rtol=1e-6)
        pool.submit(detector.close).result()  # after each run ended
    assert detector.session is None


class FailingSession:
    """A session whose `run` raises `error`. Each other attribute is the attribute of `session`."""

    def __init__(self, session: Any, error: Exception) -> None:
        self.session, self.error = session, error

    def __getattr__(self, name: str) -> Any:
        return getattr(self.session, name)

    def run(self, *args: Any, **kwargs: Any) -> Any:
        raise self.error


def test_a_detect_call_raises_vram_exhaustion_error_for_an_out_of_memory_error_and_passes_each_other_error_through(root: Path) -> None:
    put(root, object_sidecar(), object_model())
    detector = create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)
    real = detector.session
    detector.session = FailingSession(real, RuntimeError("Failed to allocate memory for requested buffer of size 1073741824"))
    with pytest.raises(VRAMExhaustionError, match="during a call"):
        detector.detect([frame(1)])
    other = RuntimeError("Invalid rank for input: images")
    detector.session = FailingSession(real, other)
    with pytest.raises(RuntimeError) as raised:
        detector.detect([frame(1)])
    assert raised.value is other


def test_a_close_during_a_detect_call_lets_the_call_end_and_a_later_call_raises_one_clear_error(root: Path) -> None:
    put(root, object_sidecar(), object_model())
    detector = create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)

    class ClosesInTheRun:
        """The session of the detector, with a `close` of the detector in the middle of each run."""

        def __init__(self, session: Any) -> None:
            self.get_inputs, self.session = session.get_inputs, session

        def run(self, names: Any, feed: Any) -> Any:
            detector.close()
            return self.session.run(names, feed)

    detector.session = ClosesInTheRun(detector.session)
    (found,) = detector.detect([frame(1)])
    np.testing.assert_allclose(found.scores, [0.9, 0.75], rtol=1e-6)
    with pytest.raises(RuntimeError, match="the detector of demo is closed"):
        detector.detect([frame(1)])
