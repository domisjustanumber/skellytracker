"""The sidecar test vectors match their generator, their sections and the package.

The vector files are in `specs/sidecar/vectors/`. `tools/make_vectors.py` writes
them. These tests check four things:

- the files have the documented shape and name existing sections;
- the files equal the generator's output, so they never drift from it;
- hand-computed anchors from the section text agree with the files;
- the skellytracker functions named in `verified_against` still give the same
  results as the cases that list them (and differ where a case does not).
"""

from __future__ import annotations

import functools
import importlib
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest
import yaml

import make_vectors as mv

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = REPO_ROOT / "specs" / "sidecar"
VECTORS_DIR = SPEC_ROOT / "vectors"

CASE_KEYS = {
    "id",
    "params",
    "input",
    "expect",
    "unproject",
    "tolerance",
    "verified_against",
}
REQUIRED_CASE_KEYS = {"id", "params", "input", "expect"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def vector_paths() -> list[Path]:
    return sorted(VECTORS_DIR.glob("*.yaml"))


@functools.cache
def load(name: str) -> dict[str, Any]:
    return yaml.safe_load((VECTORS_DIR / name).read_text(encoding="utf-8"))


def cases_of(section: str) -> list[dict[str, Any]]:
    return load(f"{section}.yaml")["cases"]


def case_params(section: str) -> list[Any]:
    return [pytest.param(case, id=case["id"]) for case in cases_of(section)]


def case_named(section: str, case_id: str) -> dict[str, Any]:
    return next(case for case in cases_of(section) if case["id"] == case_id)


def approx(value: Any, case: dict[str, Any]) -> Any:
    return pytest.approx(value, abs=case.get("tolerance", 0))


def section_ids() -> set[str]:
    """Every section ID in the front matter of the section files."""
    found: set[str] = set()
    for path in SPEC_ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if text.startswith("---\n"):
            front_matter = yaml.safe_load(text.split("---\n", 2)[1])
            if isinstance(front_matter, dict) and "id" in front_matter:
                found.add(front_matter["id"])
    return found


def resolve_function(reference: str) -> Any:
    """Return the function named by `path/to/module.py::function`."""
    path, _, name = reference.partition("::")
    assert (REPO_ROOT / path).is_file(), f"no file {path}"
    module = importlib.import_module(
        Path(path).with_suffix("").as_posix().replace("/", ".")
    )
    return getattr(module, name)


@functools.cache
def generated_texts() -> dict[str, str]:
    return mv.generate()


# ---------------------------------------------------------------------------
# Shape of the files
# ---------------------------------------------------------------------------


def test_there_are_vector_files() -> None:
    assert vector_paths()


def test_the_folder_holds_exactly_the_generated_files() -> None:
    assert {p.name for p in vector_paths()} == set(generated_texts())


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_file_equals_the_generator_output(path: Path) -> None:
    assert path.read_text(encoding="utf-8") == generated_texts()[path.name]


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_file_parses_to_the_generator_data(path: Path) -> None:
    section = path.name.removesuffix(".yaml")
    assert (
        yaml.safe_load(path.read_text(encoding="utf-8"))
        == mv.build_all()[section].data()
    )


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_file_has_the_documented_top_level_keys(path: Path) -> None:
    data = load(path.name)
    verification = "verified_against" if "verified_against" in data else "unverified"
    assert ("verified_against" in data) != ("unverified" in data)
    assert list(data) == [
        "section",
        "spec_revision",
        "generated_by",
        verification,
        "cases",
    ]
    assert data["spec_revision"] == "vNEXT"
    assert data["generated_by"] == "tools/make_vectors.py"


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_section_matches_the_file_name_and_an_existing_section(path: Path) -> None:
    section = load(path.name)["section"]
    assert path.name == f"{section}.yaml"
    assert section in section_ids()


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_unverified_gives_a_reason(path: Path) -> None:
    data = load(path.name)
    if "unverified" in data:
        assert isinstance(data["unverified"], str)
        assert len(data["unverified"]) > 20


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_verified_against_names_a_function_that_exists(path: Path) -> None:
    data = load(path.name)
    references = list(data.get("verified_against", []))
    for case in data["cases"]:
        references.extend(case.get("verified_against", []))
    assert all(callable(resolve_function(reference)) for reference in references)


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_cases_have_the_documented_shape(path: Path) -> None:
    cases = load(path.name)["cases"]
    assert cases
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids))
    for case in cases:
        assert REQUIRED_CASE_KEYS <= set(case) <= CASE_KEYS, case["id"]
        assert all(isinstance(case[key], dict) for key in ("params", "input", "expect"))
        has_fraction = mv.has_fraction(case["expect"]) or mv.has_fraction(
            case.get("unproject")
        )
        assert has_fraction == ("tolerance" in case), case["id"]


@pytest.mark.parametrize("path", vector_paths(), ids=lambda p: p.name)
def test_file_is_small(path: Path) -> None:
    assert path.stat().st_size < 16 * 1024


# ---------------------------------------------------------------------------
# Hand-computed anchors (from the section text, not from the generator)
# ---------------------------------------------------------------------------


def test_letterbox_anchors() -> None:
    section = "pre.resize.letterbox"
    landscape = case_named(section, "center-half-even-landscape")
    assert landscape["expect"] == {"n_w": 640, "n_h": 360, "left": 0, "top": 140}
    assert landscape["unproject"] == {"model_xy": [320, 320], "source_xy": [960, 540]}
    even = case_named(section, "center-rounding-tie-half-even")
    assert (even["expect"]["n_h"], even["expect"]["top"]) == (50, 295)
    up = case_named(section, "center-rounding-tie-half-up")
    assert (up["expect"]["n_h"], up["expect"]["top"]) == (51, 294)
    assert case_named(section, "center-odd-remainder-bottom")["expect"]["top"] == 80
    assert case_named(section, "center-odd-remainder-right")["expect"]["left"] == 80
    assert case_named(section, "center-scale-exactly-one")["expect"] == {
        "n_w": 640,
        "n_h": 640,
        "left": 0,
        "top": 0,
    }
    guard = case_named(section, "center-width-guard")["expect"]
    assert (guard["n_w"], guard["left"], guard["n_h"]) == (1, 319, 640)
    noise = case_named(section, "center-float-noise-below-integer")["expect"]
    assert (noise["n_w"], noise["n_h"]) == (416, 312)
    assert case_named(section, "top-left-fraction-above-half")["expect"]["n_h"] == 360
    assert {c["params"]["pad_position"] for c in cases_of(section)} == {
        "center",
        "top_left",
    }
    assert {c["params"]["rounding"] for c in cases_of(section)} == {
        "half_even",
        "half_up",
    }


def test_stretch_anchors() -> None:
    portrait = case_named("pre.resize.stretch", "portrait-target")
    assert (portrait["expect"]["dst_w"], portrait["expect"]["dst_h"]) == (384, 640)
    assert portrait["unproject"]["source_xy"] == [1920, 1080]
    fractional = case_named("pre.resize.stretch", "unproject-fractional")
    assert fractional["unproject"]["source_xy"] == [300, 168.75]


def test_fit_anchors() -> None:
    section = "pre.resize.fit"
    fractional = case_named(section, "fractional-offset")
    assert fractional["expect"] == {"scale": 0.64, "left": 0, "top": 213.44}
    assert fractional["unproject"]["source_xy"] == [500, 166.5]
    assert case_named(section, "half-pixel-offset-scale-one")["expect"]["top"] == 80.5
    padding = case_named(section, "unproject-in-the-padding")
    assert padding["unproject"]["source_xy"] == [0, -420]
    assert case_named(section, "one-pixel-wide-source")["expect"]["left"] == 316.8


def test_affine_person_crop_anchors() -> None:
    section = "pre.resize.affine_person_crop"
    tall = case_named(section, "tall-box-grows-width")["expect"]
    assert tall["center"] == [200, 250]
    assert (tall["crop_w"], tall["crop_h"]) == (375, 500)
    assert tall["matrix"] == [[0.512, 0, -6.4], [0, 0.512, 0]]
    wide = case_named(section, "wide-box-grows-height")["expect"]
    assert (wide["crop_w"], wide["crop_h"]) == (500, pytest.approx(666.666667))
    distorted = case_named(section, "aspect-ratio-not-kept")["expect"]
    assert distorted["matrix"][0][0] == 0.768
    assert distorted["matrix"][1][1] == 0.512


def test_unprojection_anchors() -> None:
    """Letterbox with `center` on 1920x1080 -> 640x640: s = 1/3, n_h = 360, top = 140."""
    section = "post.unprojection"
    corner = case_named(section, "normalized-01-top-left-corner")["expect"]
    assert corner == {"model_xy": [0, 0], "source_xy": [0, -420]}
    far = case_named(section, "normalized-01-bottom-right-corner")["expect"]
    assert far == {"model_xy": [640, 640], "source_xy": [1920, 1500]}
    # normalized_11 maps -1 and 1 to the edges 0 and the width, not to pixel centres.
    left = case_named(section, "normalized-11-left-edge")["expect"]
    right = case_named(section, "normalized-11-right-edge")["expect"]
    assert left["model_xy"] == [0, 320]
    assert right["model_xy"] == [640, 320]
    assert (left["source_xy"], right["source_xy"]) == ([0, 540], [1920, 540])
    off = case_named(section, "normalized-11-off-centre")["expect"]
    assert off == {"model_xy": [160, 480], "source_xy": [480, 1020]}
    # target_size [384, 640]: x uses the width 640 and y uses the height 384; top = 12.
    wide = case_named(section, "normalized-01-non-square-input")["expect"]
    assert wide == {"model_xy": [320, 192], "source_xy": [960, 540]}
    assert case_named(section, "normalized-11-non-square-input")["expect"] == {
        "model_xy": [640, 0],
        "source_xy": [1920, -36],
    }
    # The scale conversion comes before the unprojection: 0.5 and 320 give one result.
    pixel = case_named(section, "pixel-is-the-model-input-position")["expect"]
    assert case_named(section, "normalized-01-centre")["expect"] == pixel
    assert case_named(section, "normalized-11-centre")["expect"] == pixel
    stretch = case_named(section, "normalized-01-stretch")["expect"]
    assert stretch == {"model_xy": [160, 480], "source_xy": [480, 810]}
    affine = case_named(section, "pixel-affine-person-crop")["expect"]
    assert affine == {"model_xy": [96, 128], "source_xy": [148, 264]}
    assert case_named(section, "normalized-11-affine-person-crop")["expect"] == affine


def test_unprojection_clamp_anchors() -> None:
    section = "post.unprojection"
    clamped = case_named(section, "box-clamp-default-is-true")
    assert "clamp_boxes" not in clamped["params"]
    assert clamped["expect"]["source_xyxy"] == [-60, -120, 600, 780]
    assert clamped["expect"]["output_xyxy"] == [0, 0, 600, 780]
    assert case_named(section, "box-clamp-boxes-true")["expect"]["output_xyxy"] == [
        0,
        0,
        600,
        780,
    ]
    kept = case_named(section, "box-clamp-boxes-false-keeps-negative-values")
    assert kept["params"]["clamp_boxes"] is False
    assert kept["expect"]["output_xyxy"] == [-60, -120, 600, 780]
    padding = case_named(section, "box-clamp-after-the-scale-conversion")["expect"]
    assert padding["source_xyxy"] == [0, -420, 960, 540]
    assert padding["output_xyxy"] == [0, 0, 960, 540]
    inside = case_named(section, "box-normalized-01-inside-the-image")["expect"]
    assert inside["source_xyxy"] == inside["output_xyxy"] == [480, 420, 1440, 660]


def test_normalize_anchors_come_from_the_published_imagenet_statistics() -> None:
    """The torchvision mean and std (0..1 range) give the 0..255 statistics."""
    mean = np.array([0.485, 0.456, 0.406])  # R, G, B
    std = np.array([0.229, 0.224, 0.225])
    section = "pre.normalize"
    rgb = case_named(section, "imagenet-rgb")
    bgr = case_named(section, "imagenet-bgr")
    legacy = case_named(section, "imagenet-bgr-legacy")
    assert rgb["expect"]["channel_order"] == "rgb"
    assert bgr["expect"]["channel_order"] == "bgr"
    assert legacy["expect"]["channel_order"] == "bgr"
    assert legacy["params"]["schema_version"] == "< vNEXT"
    assert bgr["params"]["schema_version"] == "vNEXT"
    for index, (b, g, r) in enumerate(rgb["input"]["pixels_bgr"]):
        expected_rgb = (np.array([r, g, b]) / 255 - mean) / std
        expected_bgr = (np.array([b, g, r]) / 255 - mean[::-1]) / std[::-1]
        expected_legacy = (np.array([b, g, r]) / 255 - mean) / std
        assert rgb["expect"]["values"][index] == pytest.approx(expected_rgb, abs=1e-5)
        assert bgr["expect"]["values"][index] == pytest.approx(expected_bgr, abs=1e-5)
        assert legacy["expect"]["values"][index] == pytest.approx(
            expected_legacy, abs=1e-5
        )
    assert bgr["expect"]["values"] != legacy["expect"]["values"]
    # An all-black pixel: the well-known first row of ImageNet-normalized black.
    assert rgb["expect"]["values"][0] == pytest.approx(
        [-2.117904, -2.035714, -1.804444]
    )


def test_normalize_channel_order_follows_color_format() -> None:
    section = "pre.normalize"
    pixel = case_named(section, "none-rgb")["input"]["pixels_bgr"][2]  # B, G, R
    assert pixel == [10, 128, 250]
    assert case_named(section, "none-rgb")["expect"]["values"][2] == [250, 128, 10]
    assert case_named(section, "none-bgr")["expect"]["values"][2] == [10, 128, 250]
    assert case_named(section, "unit-float-rgb")["expect"]["values"][1] == [1, 1, 1]
    assert case_named(section, "default-is-imagenet-bgr")["expect"][
        "resolved_mode"
    ] == ("imagenet_bgr")
    assert (
        case_named(section, "precision-override")["expect"]["resolved_mode"] == "none"
    )
    assert case_named(section, "precision-without-override")["expect"][
        "resolved_mode"
    ] == ("unit_float")
    custom_rgb = case_named(section, "custom-rgb")["expect"]["values"]
    custom_bgr = case_named(section, "custom-bgr")["expect"]["values"]
    assert np.allclose(np.array(custom_bgr)[:, ::-1], np.array(custom_rgb), atol=1e-5)


def test_selection_none_anchors() -> None:
    section = "post.det.selection.none"
    strict = case_named(section, "threshold-is-strict")["expect"]
    assert strict["kept_rows"] == [1, 4]
    mapped = case_named(section, "class-id-map-drops-minus-one")["expect"]
    assert mapped["kept_rows"] == [0, 2, 3, 5]
    assert mapped["class_ids"] == [2, 0, 5, 5]
    assert case_named(section, "default-confidence-threshold")["expect"][
        "kept_rows"
    ] == [0, 2]
    assert case_named(section, "no-nms-for-overlapping-boxes")["expect"][
        "kept_rows"
    ] == [0, 1]
    assert case_named(section, "max-detections-does-not-pad")["expect"][
        "kept_rows"
    ] == [0, 1]
    corners = case_named(section, "box-format-cxcywh")["expect"]["boxes_xyxy"]
    assert corners == [[40, 35, 60, 45]]


def test_selection_top_k_anchors() -> None:
    section = "post.det.selection.top_k"
    several = case_named(section, "several-classes-on-one-row")["expect"]
    assert several["kept_rows"] == [2, 0, 0]
    assert several["class_ids"] == [1, 0, 1]
    assert several["scores"] == [0.95, 0.9, 0.8]
    ties = case_named(section, "ties-keep-the-lower-flat-index")["expect"]
    assert (ties["kept_rows"], ties["class_ids"]) == ([0, 0, 1], [0, 1, 0])
    lowered = case_named(section, "class-id-map-lowers-the-count")["expect"]
    assert (lowered["kept_rows"], lowered["class_ids"]) == ([0], [7])
    sigmoid = case_named(section, "sigmoid-and-strict-threshold")["expect"]
    assert sigmoid["kept_rows"] == [1, 0]
    assert sigmoid["scores"] == pytest.approx([0.982014, 0.880797], abs=1e-6)
    assert (
        len(case_named(section, "top-k-larger-than-the-candidates")["expect"]["scores"])
        == 4
    )


def test_selection_nms_anchors() -> None:
    section = "post.det.selection.nms"
    example = case_named(section, "suppress-overlap-and-threshold")
    assert example["expect"]["kept_rows"] == [0, 2]
    assert example["expect"]["scores"] == [0.9, 0.7]
    assert case_named(section, "iou-equal-to-threshold-is-kept")["expect"][
        "kept_rows"
    ] == [0, 1]
    assert case_named(section, "iou-above-threshold-is-suppressed")["expect"][
        "kept_rows"
    ] == [0]
    assert case_named(section, "box-area-adds-nothing")["expect"]["kept_rows"] == [0, 1]
    assert case_named(section, "equal-scores-lower-row-wins")["expect"][
        "kept_rows"
    ] == [0, 2]
    assert case_named(section, "output-is-sorted-by-score")["expect"]["kept_rows"] == [
        1,
        2,
        0,
    ]
    assert case_named(section, "per-class-nms-keeps-both")["expect"]["kept_rows"] == [
        0,
        1,
    ]
    assert case_named(section, "class-agnostic-suppresses-across-classes")["expect"][
        "kept_rows"
    ] == [0]
    assert case_named(section, "post-nms-top-k-keeps-the-highest")["expect"][
        "kept_rows"
    ] == [1, 2]
    assert case_named(section, "post-nms-top-k-counts-survivors")["expect"][
        "kept_rows"
    ] == [0, 2]
    assert case_named(section, "class-id-map-drop-comes-before-nms")["expect"][
        "kept_rows"
    ] == [1]
    assert case_named(section, "is-person-only-drop-comes-before-nms")["expect"][
        "kept_rows"
    ] == [1]
    assert case_named(section, "no-class-source-uses-person-class-id")["expect"][
        "class_ids"
    ] == [2, 2]


# ---------------------------------------------------------------------------
# Properties of the selection results (independent of the greedy algorithm)
# ---------------------------------------------------------------------------


def _iou(a: list[float], b: list[float]) -> float:
    width = min(a[2], b[2]) - max(a[0], b[0])
    height = min(a[3], b[3]) - max(a[1], b[1])
    inter = max(width, 0) * max(height, 0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union


@pytest.mark.parametrize("case", case_params("post.det.selection.nms"))
def test_nms_result_obeys_the_rules(case: dict[str, Any]) -> None:
    params, expect = case["params"], case["expect"]
    boxes = [
        mv.to_xyxy(row, params.get("box_format", "xyxy"))
        for row in (
            case["input"].get("boxes") or [r[:4] for r in case["input"]["rows"]]
        )
    ]
    rows, scores, classes = expect["kept_rows"], expect["scores"], expect["class_ids"]
    assert len(rows) == len(set(rows)) == len(scores) == len(classes)
    assert scores == sorted(scores, reverse=True)
    assert all(s > params["score_threshold"] for s in scores)
    assert all(s > params.get("confidence_threshold_default", 0.7) for s in scores)
    if "post_nms_top_k" in params:
        assert len(rows) <= params["post_nms_top_k"]
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if params.get("class_agnostic", False) or classes[i] == classes[j]:
                assert _iou(boxes[rows[i]], boxes[rows[j]]) <= params["iou_threshold"]


@pytest.mark.parametrize("case", case_params("post.det.selection.top_k"))
def test_top_k_result_obeys_the_rules(case: dict[str, Any]) -> None:
    params, expect = case["params"], case["expect"]
    scores = expect["scores"]
    assert len(scores) <= params["top_k"]
    assert scores == sorted(scores, reverse=True)
    assert all(s > params.get("confidence_threshold_default", 0.7) for s in scores)
    pairs = [
        (r, c) for r, c in zip(expect["kept_rows"], expect["class_ids"], strict=True)
    ]
    assert len(pairs) == len(set(pairs))


@pytest.mark.parametrize("case", case_params("post.det.selection.none"))
def test_none_result_obeys_the_rules(case: dict[str, Any]) -> None:
    params, expect = case["params"], case["expect"]
    rows = expect["kept_rows"]
    assert rows == sorted(set(rows))
    assert all(
        s > params.get("confidence_threshold_default", 0.7) for s in expect["scores"]
    )
    if "max_detections" in params:
        # The graph gives a fixed number of rows; the host neither pads nor truncates.
        assert len(case["input"]["rows"]) == params["max_detections"]
        assert len(rows) <= params["max_detections"]


# ---------------------------------------------------------------------------
# The resize unprojection inverts the forward map (checked with OpenCV)
# ---------------------------------------------------------------------------


def _forward_matrix(section: str, case: dict[str, Any]) -> np.ndarray:
    src_w, src_h = case["input"].get("src_w"), case["input"].get("src_h")
    expect = case["expect"]
    if section == "pre.resize.letterbox":
        scale_x, scale_y = expect["n_w"] / src_w, expect["n_h"] / src_h
        return np.array(
            [[scale_x, 0, expect["left"]], [0, scale_y, expect["top"]]], dtype=float
        )
    if section == "pre.resize.stretch":
        return np.array(
            [[expect["scale_x"], 0, 0], [0, expect["scale_y"], 0]], dtype=float
        )
    if section == "pre.resize.fit":
        s = expect["scale"]
        return np.array([[s, 0, expect["left"]], [0, s, expect["top"]]], dtype=float)
    return np.array(expect["matrix"], dtype=float)


UNPROJECTION_SECTIONS = [
    "pre.resize.letterbox",
    "pre.resize.stretch",
    "pre.resize.fit",
    "pre.resize.affine_person_crop",
]


@pytest.mark.parametrize(
    ("section", "case"),
    [
        pytest.param(section, case, id=f"{section}:{case['id']}")
        for section in UNPROJECTION_SECTIONS
        for case in cases_of(section)
    ],
)
def test_unprojection_inverts_the_forward_map(
    section: str, case: dict[str, Any]
) -> None:
    forward = _forward_matrix(section, case)
    inverse = cv2.invertAffineTransform(forward)
    model_x, model_y = case["unproject"]["model_xy"]
    source = inverse @ np.array([model_x, model_y, 1.0])
    # `scale`, `left` and `top` are rounded to 6 decimals in the file, so the
    # inverse of the file's matrix differs from `source_xy` by about 1e-5 relative.
    expected = case["unproject"]["source_xy"]
    assert source == pytest.approx(expected, rel=1e-5, abs=case.get("tolerance", 0))


# ---------------------------------------------------------------------------
# post.unprojection: the scale, the inverse of the resize and the clamp
# ---------------------------------------------------------------------------

UNPROJECTION = "post.unprojection"
SCALE_RANGES = {"normalized_01": (0.0, 1.0), "normalized_11": (-1.0, 1.0)}


def points_of(values: Any) -> np.ndarray:
    """Return a flat list [x, y] or [x1, y1, x2, y2] as an (N, 2) array."""
    return np.array(values, dtype=float).reshape(-1, 2)


def decoded_points(case: dict[str, Any]) -> np.ndarray:
    data = case["input"]
    return points_of(
        data["decoded_xy"] if "decoded_xy" in data else data["decoded_xyxy"]
    )


def expect_points(case: dict[str, Any], name: str) -> np.ndarray:
    """Return `model_xy` or `model_xyxy` (name `model`), or the `source` pair."""
    expect = case["expect"]
    return points_of(
        expect[f"{name}_xy"] if f"{name}_xy" in expect else expect[f"{name}_xyxy"]
    )


def forward_matrix(case: dict[str, Any]) -> np.ndarray:
    """Return the map from source pixels to model-input pixels, from the resize fields of a case."""
    resize = case["params"]["resize"]
    method = resize["method"]
    if method == "none":
        return np.array([[1, 0, 0], [0, 1, 0]], dtype=float)
    t_h, t_w = resize["target_size"]
    if method == "affine_person_crop":
        x1, y1, x2, y2 = case["input"]["bbox_xyxy"]
        width = (x2 - x1) * resize["expand_ratio"]
        height = (y2 - y1) * resize["expand_ratio"]
        if resize["maintain_aspect_ratio"]:
            if width / height > t_w / t_h:
                height = width * t_h / t_w
            else:
                width = height * t_w / t_h
        scale_x, scale_y = t_w / width, t_h / height
        return np.array(
            [
                [scale_x, 0, t_w / 2 - scale_x * (x1 + x2) / 2],
                [0, scale_y, t_h / 2 - scale_y * (y1 + y2) / 2],
            ]
        )
    src_w, src_h = case["input"]["src_w"], case["input"]["src_h"]
    if method == "stretch":
        return np.array([[t_w / src_w, 0, 0], [0, t_h / src_h, 0]])
    s = min(t_w / src_w, t_h / src_h)
    if method == "fit":
        return np.array([[s, 0, (t_w - src_w * s) / 2], [0, s, (t_h - src_h * s) / 2]])
    assert method == "letterbox"
    if resize["rounding"] == "half_even":
        n_w, n_h = round(src_w * s), round(src_h * s)
    else:
        n_w, n_h = math.floor(src_w * s + 0.5), math.floor(src_h * s + 0.5)
    n_w, n_h = max(1, n_w), max(1, n_h)
    left, top = (
        (0, 0)
        if resize["pad_position"] == "top_left"
        else ((t_w - n_w) // 2, (t_h - n_h) // 2)
    )
    return np.array([[n_w / src_w, 0, left], [0, n_h / src_h, top]])


@pytest.mark.parametrize("case", case_params(UNPROJECTION))
def test_the_decoded_value_is_converted_to_model_input_pixels(
    case: dict[str, Any],
) -> None:
    """`normalized_01` maps [0, 1] and `normalized_11` maps [-1, 1] linearly to [0, size]."""
    in_h, in_w = case["params"]["input_size"]
    decoded = decoded_points(case)
    scale = case["params"]["scale"]
    if scale == "pixel":
        expected = decoded
    else:
        low, high = SCALE_RANGES[scale]
        expected = np.stack(
            [
                np.interp(decoded[:, 0], [low, high], [0, in_w]),
                np.interp(decoded[:, 1], [low, high], [0, in_h]),
            ],
            axis=1,
        )
    assert expect_points(case, "model") == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("case", case_params(UNPROJECTION))
def test_the_unprojection_inverts_the_resize_of_the_case(case: dict[str, Any]) -> None:
    inverse = cv2.invertAffineTransform(forward_matrix(case))
    model = expect_points(case, "model")
    source = np.hstack([model, np.ones((len(model), 1))]) @ inverse.T
    assert source == pytest.approx(expect_points(case, "source"), abs=1e-6)


BOX_CASES = [
    pytest.param(case, id=case["id"])
    for case in cases_of(UNPROJECTION)
    if "decoded_xyxy" in case["input"]
]


@pytest.mark.parametrize("case", BOX_CASES)
def test_the_output_box_is_the_clamped_source_box_unless_clamp_boxes_is_false(
    case: dict[str, Any],
) -> None:
    expect = case["expect"]
    source = np.array(expect["source_xyxy"], dtype=float)
    if case["params"].get("clamp_boxes", True):
        assert expect["output_xyxy"] == np.maximum(source, 0).tolist()
    else:
        assert expect["output_xyxy"] == expect["source_xyxy"]


@pytest.mark.parametrize("case", BOX_CASES)
def test_no_box_case_depends_on_the_open_questions_of_the_clamp(
    case: dict[str, Any],
) -> None:
    """The spec leaves the upper bound (W or W - 1) and a box without area undefined."""
    source = np.array(case["expect"]["source_xyxy"], dtype=float)
    assert source[0::2].max() <= case["input"]["src_w"] - 1
    assert source[1::2].max() <= case["input"]["src_h"] - 1
    x1, y1, x2, y2 = np.maximum(source, 0)
    assert x2 > x1 and y2 > y1


def test_the_unprojection_cases_cover_every_scale_method_and_clamp_setting() -> None:
    cases = cases_of(UNPROJECTION)
    assert {c["params"]["scale"] for c in cases} == {
        "pixel",
        "normalized_01",
        "normalized_11",
    }
    assert {c["params"]["resize"]["method"] for c in cases} == {
        "letterbox",
        "stretch",
        "fit",
        "none",
        "affine_person_crop",
    }
    boxes = [c for c in cases if "decoded_xyxy" in c["input"]]
    assert {c["params"].get("clamp_boxes") for c in boxes} == {None, True, False}


def test_the_unprojection_file_is_unverified_because_no_function_runs_it() -> None:
    assert "unverified" in load(f"{UNPROJECTION}.yaml")


# ---------------------------------------------------------------------------
# skellytracker functions named in `verified_against`
# ---------------------------------------------------------------------------

SOURCE_VALUE = 200
LETTERBOX_PAD = 114


def package_letterbox_geometry(case: dict[str, Any]) -> dict[str, int] | None:
    """Run `letterbox_preprocess` on a flat image; None when it cannot run the case.

    The function reports only a scale factor, so the geometry is read from the
    padded image: the source value (200) differs from the padding (114).
    """
    function = resolve_function(mv.LETTERBOX_FUNCTION)
    params = case["params"]
    if params["pad_position"] != "top_left":
        return None  # the function has no `center`
    image = np.full(
        (case["input"]["src_h"], case["input"]["src_w"], 3),
        SOURCE_VALUE,
        dtype=np.uint8,
    )
    try:
        padded, _ratio = function(
            image, tuple(params["target_size"]), pad_value=LETTERBOX_PAD
        )
    except cv2.error:
        return None
    covered = (padded != LETTERBOX_PAD).any(axis=2)
    columns, rows = np.flatnonzero(covered.any(axis=0)), np.flatnonzero(
        covered.any(axis=1)
    )
    return {
        "n_w": len(columns),
        "n_h": len(rows),
        "left": int(columns[0]) if len(columns) else 0,
        "top": int(rows[0]) if len(rows) else 0,
    }


@pytest.mark.parametrize("case", case_params("pre.resize.letterbox"))
def test_letterbox_preprocess_agrees_exactly_where_the_case_says(
    case: dict[str, Any],
) -> None:
    geometry = package_letterbox_geometry(case)
    listed = mv.LETTERBOX_FUNCTION in case.get("verified_against", [])
    if geometry is None:
        assert not listed, "a case the function cannot run is not verified"
    else:
        assert (geometry == case["expect"]) == listed, geometry


def test_letterbox_file_claims_no_more_than_the_function_gives() -> None:
    data = load("pre.resize.letterbox.yaml")
    if "verified_against" in data:
        assert all(package_letterbox_geometry(c) == c["expect"] for c in data["cases"])
    else:
        listed = [
            mv.LETTERBOX_FUNCTION in c.get("verified_against", [])
            for c in data["cases"]
        ]
        assert any(listed), "the function reproduces some cases"
        assert not all(listed), "the function does not reproduce every case"


def _axis_extent(mask_axis: np.ndarray) -> tuple[int, int]:
    indexes = np.flatnonzero(mask_axis)
    return int(indexes[0]), int(indexes[-1])


def test_fit_file_names_its_function() -> None:
    assert load("pre.resize.fit.yaml")["verified_against"] == [mv.FIT_FUNCTION]


@pytest.mark.parametrize("case", case_params("pre.resize.fit"))
def test_fit_preprocess_agrees_with_the_case(case: dict[str, Any]) -> None:
    function = resolve_function(mv.FIT_FUNCTION)
    t_h, t_w = case["params"]["target_size"]
    src_w, src_h = case["input"]["src_w"], case["input"]["src_h"]
    image = np.full((src_h, src_w, 3), SOURCE_VALUE, dtype=np.uint8)
    padded, (scale, left, top) = function(image, (t_h, t_w), pad_value=0)

    expect = case["expect"]
    assert (scale, left, top) == (
        approx(expect["scale"], case),
        approx(expect["left"], case),
        approx(expect["top"], case),
    )

    # The warped image agrees with the reported geometry. The edges blend with
    # the border, so allow the blend zone of one source pixel (`scale` pixels).
    assert padded.shape == (t_h, t_w, 3)
    margin = math.ceil(scale) + 1
    covered = (padded > 0).any(axis=2)
    for axis, size, start, length in ((0, t_w, left, src_w), (1, t_h, top, src_h)):
        first, last = _axis_extent(covered.any(axis=axis))
        low, high = max(start, 0.0), min(start + length * scale, size)
        assert math.floor(low) - margin <= first <= math.ceil(low) + 1
        assert math.floor(high) - 2 <= last <= math.ceil(high) + margin

    # The unprojection is the exact inverse of the warp matrix of the function.
    matrix = np.array([[scale, 0, left], [0, scale, top]], dtype=float)
    model_x, model_y = case["unproject"]["model_xy"]
    source = cv2.invertAffineTransform(matrix) @ np.array([model_x, model_y, 1.0])
    assert source == pytest.approx(
        case["unproject"]["source_xy"], abs=case.get("tolerance", 0)
    )
