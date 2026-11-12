"""Reference implementation of the section pre.resize.affine_crop, as the proposal changes it.

This file uses ASD-STE100 Simplified Technical English.

Section ID: pre.resize.affine_crop (proposed). The current ID is pre.resize.affine_person_crop. The
proposed section file is specs/model-sidecar/pre/resize-affine-crop.md. The current file is
specs/model-sidecar/pre/resize-affine-person-crop.md.
Proposal: proposal-affine-crop-rotated-roi@openmmlab-exporter (slug affine-crop-rotated-roi). It is
a follow-up of proposal-affine-crop-matrix@openmmlab-exporter (skellytracker ADR-3S5G).
Target file in skellytracker: specs/model-sidecar/reference/pre_resize_affine_crop.py. It replaces
specs/model-sidecar/reference/pre_resize_affine_person_crop.py.

source commit: none (no host code). The OpenMMLab-Exporter host code implements the current text
for a box with rotation 0: OpenMMLab-Exporter onnx_runtime/preprocess.py::affine_crop_geometry at
2c554cb817ec1cce82af0c97f46e96eef15e3cb6. No host code implements a rotated ROI. The functions come
from the text of part 2 of the proposal. The rotated warp points have the form of mmpose v1.3.2
(5408bc76f5b848cf925a0d1857899011d8c5b497) get_warp_matrix and _rotate_point. The file does not
import mmpose.

Full section. This file is the landed file specs/model-sidecar/reference/pre_resize_affine_person_crop.py
at skellytracker 924c9773e48432a7ef7162b26942f69692615fbe with the change of the proposal:
- the crop takes an ROI (c_x, c_y, w, h, rotation) in source pixels. A box [x1, y1, x2, y2] gives
  the ROI with rotation 0 (roi_from_box);
- the expansion and the aspect fix apply along the ROI axes;
- the warp points P1 and P2 turn with the rotation;
- the rename: the method affine_crop, the section ID pre.resize.affine_crop and the rule IDs
  V-pre.resize.affine_crop-1 to -3.
For rotation 0, M is bit for bit the M of the current text.

Imports of other sections: pre.resize.interpolation (pre_resize_interpolation, the values
INTERPOLATION_FLAGS and COMPUTE_DTYPES). Fixtures: none.

The function crop_size refuses an ROI that gives an empty crop (w <= 0 or h <= 0, or NaN) with
ValueError. The function roi_values refuses a value that is not finite. The ROI is a host value,
not a sidecar value, so the refusals have no rule ID.

Vector results: fill of skellytracker tools/make_vectors.py (924c9773e48432a7ef7162b26942f69692615fbe)
wrote the expect of the cases of part 4 with this file.
Parity result: to run (part 5 of the proposal).

Uses only NumPy, OpenCV, the Python standard library and the module pre_resize_interpolation.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import cv2
import numpy as np
import pre_resize_interpolation

SECTION_ID = "pre.resize.affine_crop"
METHOD = "affine_crop"
DEFAULT_EXPAND_RATIO = 1.25
DEFAULT_MAINTAIN_ASPECT_RATIO = True
DEFAULT_PAD_VALUE = 0
# Rule V-pre.resize.affine_crop-3: the fields that an affine_crop resize must not declare.
NOT_ALLOWED_RESIZE_FIELDS = ("pad_value", "pad_position", "rounding")


def roi_from_box(bbox_xyxy: Sequence[float]) -> tuple[np.float32, np.float32, np.float32, np.float32, float]:
    """pre.resize.affine_crop, Behaviour: the ROI of a box, in float32.

    bbox_xyxy is [x1, y1, x2, y2] in source pixels. Each value rounds to float32, and each operation
    rounds its result to float32. Returns (c_x, c_y, w, h, rotation) with rotation 0.
    """
    x1, y1, x2, y2 = (np.float32(float(value)) for value in bbox_xyxy)
    half = np.float32(0.5)
    return (x1 + x2) * half, (y1 + y2) * half, x2 - x1, y2 - y1, 0.0


def roi_values(roi: Sequence[float]) -> tuple[np.float32, np.float32, np.float32, np.float32, float]:
    """pre.resize.affine_crop, Behaviour: the ROI (c_x, c_y, w, h, rotation) as the steps use it.

    c_x, c_y, w and h round to float32. The rotation is float64, in radians. Each value must be
    finite: the host gives the ROI, so a value that is not finite is refused with ValueError.
    """
    values = [float(value) for value in roi]
    if len(values) != 5:
        raise ValueError("an ROI has five values: c_x, c_y, w, h and rotation")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("each ROI value must be finite")
    c_x, c_y, w, h, rotation = values
    return np.float32(c_x), np.float32(c_y), np.float32(w), np.float32(h), rotation


def crop_size(
    roi: tuple[np.float32, np.float32, np.float32, np.float32, float],
    target_size: Sequence[int],
    expand_ratio: float = DEFAULT_EXPAND_RATIO,
    maintain_aspect_ratio: bool = DEFAULT_MAINTAIN_ASPECT_RATIO,
) -> tuple[np.float32, np.float32, np.float32, np.float32]:
    """pre.resize.affine_crop, Behaviour: the centre and the crop size, in float32.

    w is the size along the ROI x axis and h is the size along the ROI y axis. Each operation rounds
    its result to float32. The order: expand, then fix the aspect ratio. The h branch divides by
    a = f32(T_w / T_h). The comparison is a strict >. Returns (c_x, c_y, w, h).
    """
    c_x, c_y, w, h, _ = roi
    t_h, t_w = (int(value) for value in target_size)
    e = np.float32(float(expand_ratio))
    w = np.float32(w) * e
    h = np.float32(h) * e
    if maintain_aspect_ratio:
        a = np.float32(t_w / t_h)
        if w > h * a:
            h = w / a
        else:
            w = h * a
    if not (w > 0 and h > 0):
        raise ValueError("the ROI gives an empty crop")
    return np.float32(c_x), np.float32(c_y), w, h


def warp_points(
    center_and_size: tuple[np.float32, np.float32, np.float32, np.float32],
    rotation: float,
    target_size: Sequence[int],
    maintain_aspect_ratio: bool = DEFAULT_MAINTAIN_ASPECT_RATIO,
) -> tuple[np.ndarray, np.ndarray]:
    """pre.resize.affine_crop, Behaviour: the three float32 point pairs that define M.

    src holds P0, P1 and P2 in source pixels. dst holds Q0, Q1 and Q2 in model-input pixels.
    cs = cos(rotation) and sn = sin(rotation) are float64. P1 is half the crop width from the centre,
    against the ROI x axis (cs, sn): each coordinate is one float64 expression, rounded once to
    float32. With maintain_aspect_ratio true, P2 turns P0 - P1 by +90 degrees around P1, in float32,
    so M uses w and not h. With maintain_aspect_ratio false, P2 is half the crop height from the
    centre, against the ROI y axis (-sn, cs), in float64 and rounded once to float32. With rotation
    0, cs is 1 and sn is 0, and the points are those of the current text.
    Returns (src, dst), each a float32 array of shape (3, 2).
    """
    c_x, c_y, w, h = center_and_size
    t_h, t_w = (int(value) for value in target_size)
    half = np.float32(0.5)
    cs = math.cos(float(rotation))
    sn = math.sin(float(rotation))
    half_w = float(w * half)
    half_h = float(h * half)
    src = np.zeros((3, 2), dtype=np.float32)
    dst = np.zeros((3, 2), dtype=np.float32)
    src[0] = (c_x, c_y)
    dst[0] = (t_w * 0.5, t_h * 0.5)
    src[1] = (float(c_x) - half_w * cs, float(c_y) - half_w * sn)
    dst[1] = (0.0, t_h * 0.5)
    if maintain_aspect_ratio:
        d_x = src[0, 0] - src[1, 0]
        d_y = src[0, 1] - src[1, 1]
        src[2] = (src[1, 0] - d_y, src[1, 1] + d_x)
        dst[2] = (0.0, t_h * 0.5 + t_w * 0.5)
    else:
        src[2] = (float(c_x) + half_h * sn, float(c_y) - half_h * cs)
        dst[2] = (t_w * 0.5, 0.0)
    return src, dst


def warp_matrix(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """pre.resize.affine_crop, Behaviour: M, the affine map that takes src onto dst.

    cv2.getAffineTransform solves it in float64 from the float32 points. Returns a float64 (2, 3) array.
    """
    return cv2.getAffineTransform(np.asarray(src, np.float32), np.asarray(dst, np.float32))


def policy_values(crop_policy: Mapping[str, Any] | None) -> tuple[float, bool, Any]:
    """pre.resize.affine_crop, Fields: crop_policy with its defaults.

    Returns (expand_ratio, maintain_aspect_ratio, pad_value).
    """
    policy = dict(crop_policy or {})
    return (
        policy.get("expand_ratio", DEFAULT_EXPAND_RATIO),
        policy.get("maintain_aspect_ratio", DEFAULT_MAINTAIN_ASPECT_RATIO),
        policy.get("pad_value", DEFAULT_PAD_VALUE),
    )


def crop_geometry(
    roi: Sequence[float],
    target_size: Sequence[int],
    crop_policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """pre.resize.affine_crop, Behaviour: the centre, the crop size, the points and M of one ROI.

    roi is (c_x, c_y, w, h, rotation) in source pixels, with the rotation in radians. target_size is
    [T_h, T_w].
    """
    expand_ratio, maintain_aspect_ratio = policy_values(crop_policy)[:2]
    values = roi_values(roi)
    size = crop_size(values, target_size, expand_ratio, maintain_aspect_ratio)
    src, dst = warp_points(size, values[4], target_size, maintain_aspect_ratio)
    c_x, c_y, w, h = size
    return {
        "center": [float(c_x), float(c_y)],
        "crop_w": float(w),
        "crop_h": float(h),
        "src_points": src.astype(np.float64).tolist(),
        "dst_points": dst.astype(np.float64).tolist(),
        "matrix": warp_matrix(src, dst).tolist(),
    }


def border_value(pad_value: float | Sequence[float], channels: int) -> tuple[float, ...]:
    """pre.resize.affine_crop, Behaviour: the border value of each channel.

    A scalar pad_value s gives [s] * channels (ADR-BJF9). An array gives one value for each channel,
    in the channel order of the image. cv2.warpAffine takes 4 values, so the tuple ends with zeros.
    """
    if isinstance(pad_value, bool):
        raise ValueError("pad_value must be a number or one number for each channel")
    if isinstance(pad_value, (int, float)):
        values = [float(pad_value)] * channels
    else:
        values = [float(value) for value in pad_value]
        if len(values) != channels:
            raise ValueError("a pad_value array must have one value for each channel")
    return tuple(values) + (0.0,) * (4 - len(values))


def warp_image(
    image: np.ndarray,
    matrix: Sequence[Sequence[float]],
    target_size: Sequence[int],
    interpolation: str = "linear",
    pad_value: float | Sequence[float] = DEFAULT_PAD_VALUE,
    compute_dtype: str = "uint8",
) -> np.ndarray:
    """pre.resize.affine_crop, Behaviour: warp the image with M to (T_w, T_h).

    The image is HWC (or HW), in the channel order of input.color_format. The warp runs in
    compute_dtype (section pre.resize.interpolation). The border mode is constant. The
    destination pixel (x, y) samples the source at M^-1 (x, y, 1) (ADR-G79P).
    """
    t_h, t_w = (int(value) for value in target_size)
    source = np.ascontiguousarray(np.asarray(image).astype(pre_resize_interpolation.COMPUTE_DTYPES[compute_dtype]))
    channels = 1 if source.ndim == 2 else int(source.shape[2])
    return cv2.warpAffine(
        source,
        np.asarray(matrix, dtype=np.float64),
        (t_w, t_h),
        flags=pre_resize_interpolation.INTERPOLATION_FLAGS[interpolation],
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_value(pad_value, channels),
    )


def affine_crop(
    image: np.ndarray,
    roi: Sequence[float],
    resize: Mapping[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    """pre.resize.affine_crop, Behaviour: the full forward step for one ROI.

    roi is (c_x, c_y, w, h, rotation). For a box, give roi_from_box(bbox_xyxy). resize is the
    resolved input.resize block: target_size, and optional interpolation, compute_dtype and
    crop_policy. Returns the crop and the geometry. The Inverse uses the matrix.
    """
    if resize.get("method", METHOD) != METHOD:
        raise ValueError("the resize method is not affine_crop")
    target_size = resize["target_size"]
    geometry = crop_geometry(roi, target_size, resize.get("crop_policy"))
    pad_value = policy_values(resize.get("crop_policy"))[2]
    crop = warp_image(
        image,
        geometry["matrix"],
        target_size,
        resize.get("interpolation", "linear"),
        pad_value,
        resize.get("compute_dtype", "uint8"),
    )
    return crop, geometry


def unproject(model_xy: Sequence[float], matrix: Sequence[Sequence[float]]) -> list[float]:
    """pre.resize.affine_crop, Inverse: model-input pixels to source pixels.

    Apply the inverse of M, in float64. The positions are pixel indices of cv2.warpAffine. The
    Inverse adds no 0.5 offset (ADR-G79P).
    """
    inverse_matrix = cv2.invertAffineTransform(np.asarray(matrix, dtype=np.float64))
    x, y = (float(value) for value in model_xy)
    point = inverse_matrix @ np.array([x, y, 1.0], dtype=np.float64)
    return [float(point[0]), float(point[1])]


def is_number(value: Any) -> bool:
    """True for a finite int or float that is not a bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


TOP_DOWN = ("top_down_single_person", "top_down_multi_person")


def check_rules(sidecar: Mapping[str, Any]) -> list[str]:
    """pre.resize.affine_crop, Validation rules: the sorted IDs of the rules that fail.

    sidecar holds the input, sizes and keypoint blocks. The resize of a size is the top-level
    input.resize with the input.resize of the size on top of it.
    -1: crop_policy.expand_ratio is a positive number; crop_policy.maintain_aspect_ratio is a boolean.
    -2: a top-down keypoint.estimator_type needs input.resize.method affine_crop.
    -3: each size declares input.resize.target_size; no pad_value, pad_position or rounding.
    Rules -1 and -3 apply to an affine_crop resize. Rule -2 applies to each sidecar.
    """
    failed: set[str] = set()
    top = dict(((sidecar.get("input") or {}).get("resize")) or {})
    sizes = sidecar.get("sizes") or {}
    resolved = []
    for size in sizes.values():
        own = dict((((size or {}).get("input") or {}).get("resize")) or {})
        resolved.append((own, {**top, **own}))
    if not resolved:
        resolved.append(({}, top))
    for own, resize in resolved:
        if resize.get("method") == METHOD:
            policy = resize.get("crop_policy") or {}
            if "expand_ratio" in policy:
                ratio = policy["expand_ratio"]
                if not (is_number(ratio) and ratio > 0):
                    failed.add(f"V-{SECTION_ID}-1")
            if "maintain_aspect_ratio" in policy and not isinstance(policy["maintain_aspect_ratio"], bool):
                failed.add(f"V-{SECTION_ID}-1")
            if "target_size" not in own:
                failed.add(f"V-{SECTION_ID}-3")
            if any(name in resize for name in NOT_ALLOWED_RESIZE_FIELDS):
                failed.add(f"V-{SECTION_ID}-3")
        if (sidecar.get("keypoint") or {}).get("estimator_type") in TOP_DOWN and resize.get("method") != METHOD:
            failed.add(f"V-{SECTION_ID}-2")
    return sorted(failed)


def case_policy(params: Mapping[str, Any]) -> dict[str, Any]:
    """The crop_policy of a vector case: the crop_policy keys of params."""
    return {key: params[key] for key in ("expand_ratio", "maintain_aspect_ratio", "pad_value") if key in params}


def case_roi(input: Mapping[str, Any]) -> tuple[Any, ...]:
    """The ROI of a vector case: input.roi, or the ROI of input.bbox_xyxy. A case gives one of them."""
    if ("roi" in input) == ("bbox_xyxy" in input):
        raise ValueError("a case gives roi or bbox_xyxy, not both and not neither")
    if "roi" in input:
        return tuple(input["roi"])
    return roi_from_box(input["bbox_xyxy"])


def run(params: Mapping[str, Any], input: Mapping[str, Any]) -> dict[str, Any]:
    """pre.resize.affine_crop, Behaviour: the centre, the crop size and M of one ROI or one box."""
    geometry = crop_geometry(case_roi(input), params["target_size"], case_policy(params))
    return {
        "center": geometry["center"],
        "crop_w": geometry["crop_w"],
        "crop_h": geometry["crop_h"],
        "matrix": geometry["matrix"],
    }


def inverse(params: Mapping[str, Any], input: Mapping[str, Any]) -> dict[str, list[float]]:
    """pre.resize.affine_crop, Inverse: model_xy of the crop of the case to source pixels."""
    matrix = run(params, input)["matrix"]
    return {"source_xy": unproject(input["model_xy"], matrix)}


def border(params: Mapping[str, Any], input: Mapping[str, Any]) -> dict[str, list[float]]:
    """pre.resize.affine_crop, Behaviour: the value of crop pixel (0, 0) for a 3-channel image.

    The case puts pixel (0, 0) outside the source image, so the value is the border value.
    """
    geometry = crop_geometry(case_roi(input), params["target_size"], case_policy(params))
    image = np.zeros((int(input["src_h"]), int(input["src_w"]), 3), dtype=np.uint8)
    pad_value = policy_values(case_policy(params))[2]
    crop = warp_image(image, geometry["matrix"], params["target_size"], "linear", pad_value)
    return {"border": [value.item() for value in crop[0, 0]]}
