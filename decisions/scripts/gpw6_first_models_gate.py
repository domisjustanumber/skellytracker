"""Model gate of `yolox-person` and `rtmw-wholebody133` at the detector level (entry GPW6).

This script made the evidence of entry GPW6. It runs the generic detectors of the package on the
real exports in `core/model_zoo/` and compares them with the upstream reference output of the parity
workers of OpenMMLab-Exporter (mmdet 3.3.0 and mmpose 1.3.2). It reads the worker files as data
(`numpy.load` with `allow_pickle=False`). It runs no exporter code.

    uv run python decisions/scripts/gpw6_first_models_gate.py yolox --parity <folder> --out <json>
    uv run python decisions/scripts/gpw6_first_models_gate.py rtmw --parity <folder> --out <json>
    uv run python decisions/scripts/gpw6_first_models_gate.py timing --out <json>

`--parity` is the folder that holds `worker/decoded.npz` and `worker/upstream_<size>.npz`. `--eps`
gives the EP keys (default `cpu`). `--precisions` and `--sizes` select a part of the run. The script
stops when a worker file does not have the SHA-256 of `WORKER_SHA256`. These are the hashes that
the two intakes record.

The gates were set on 2026-11-16, before the first run. Each gate is the gate of the parity script
of the exporter with the same number, on the package code. The source of each gate is the parity
rules (`specs/model-sidecar/model-addition-workflow/parity.md`).

`yolox` (18 images for each size):

- Y1 [step 4, floor]: the tensor of `preprocess_image` equals the upstream canvas. The largest
  difference is 0, and the letterbox size equals the upstream resized size.
- Y4 [step 5, the decode alone, floor]: `decode_nms` on the upstream anchor rows against the
  upstream person detections (label 0). The kept anchors are equal, except an upstream anchor with
  a score equal to float32(`nms.score_threshold`). Each score is equal bit for bit. Each box
  coordinate is within 4 float32 spacings. It runs with `min_score` 0 and with the sidecar value.
- Y5a [step 5, floor]: `detect()` of the detector equals, bit for bit, `decode_nms` on the outputs
  of the same session for the upstream tensors.
- Y5c [step 5, floor from the export error of the same run]: that decode against the upstream
  person detections. An anchor that both sides keep has a box difference of at most its row
  difference times the unprojection scale times 1.000001, plus 4 float32 spacings. An anchor that
  one side keeps needs a cause in the row difference: the threshold, an IoU on two sides of
  `nms.iou_threshold` or within 1e-5 of it, a changed score order against an overlapping
  candidate, or an overlap with another such anchor. With the sidecar `min_score`, an anchor that
  both sides keep at `min_score` 0 can also have its two scores on two sides of `min_score`.

`rtmw` (49 persons on 10 images for each size):

- R1 [step 4, floor]: the matrix `M` of `resize_geometry` equals the upstream `M` bit for bit.
- R1b [step 4, floor]: `normalize` on the upstream crop equals the upstream tensor. Difference 0.
- R4 [step 5, the decode alone, floor]: `decode_simcc` on the upstream raw rows against the mmpose
  decode. Each score is equal bit for bit. Each coordinate is within 1 float32 spacing.
- R4b [step 5, the unprojection alone, floor]: `resize_inverse` on the mmpose keypoints against the
  upstream final keypoints, within `B = 16 * spacing(float32(m))`. `m` is the largest of the crop
  centre, the crop size and the upstream keypoints of the person.
- R5 [step 5, floor from the export error of the same run]: the upstream tensors through
  `run_batches`, `decode_simcc` and `resize_inverse`, against the upstream final output. `r` is the
  largest difference of the two raw rows of a keypoint. The score differs by at most `r`. On an
  axis with the upstream bin, the coordinate is within `B`. On an axis with an other bin, the two
  upstream row values differ by at most `2 * r` of that axis.
- R7 [step 1, the measured gate G7 of the exporter, 0.15]: `detect()` on the decoded images and the
  upstream boxes against the upstream final keypoints. A keypoint is an outlier when its bin
  differs by more than 1 on an axis, or when it is missing on one side only. For each session, the
  median over the persons of the outlier fraction is at most 0.15. The exporter set this value
  with three negative controls. This script does not run the controls again.

For a GPU EP, the gate also needs 0 nodes on the CPU EP (`SessionReport.cpu_nodes`).

`timing` measures, for each artifact, the median time of `model_batch_convert` to batch 1 and of
`create_detector` with the batch of the sidecar and with batch 1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np

from skellytracker.core.detectors import get_detector, load_detector_sidecar
from skellytracker.core.detectors.generic import create_detector
from skellytracker.core.detectors.generic.batch_conversion import model_batch_convert
from skellytracker.core.detectors.generic.inference import run_batches
from skellytracker.core.detectors.generic.keypoint_detector import GenericKeypointDetector
from skellytracker.core.detectors.generic.object_detector import GenericObjectDetector
from skellytracker.core.detectors.generic.session import open_session
from skellytracker.core.detectors.processing.post.keypoint_decode_simcc import decode_simcc
from skellytracker.core.detectors.processing.post.object_selection_nms import box_iou, decode_nms
from skellytracker.core.detectors.processing.post.unprojection import resize_inverse
from skellytracker.core.detectors.processing.pre.normalize import normalize
from skellytracker.core.detectors.processing.pre.preprocess import preprocess_image, resize_geometry
from skellytracker.core.detectors.processing.pre.resize_affine_crop import roi_from_box

YOLOX = "yolox-person@openmmlab-exporter"
RTMW = "rtmw-wholebody133@openmmlab-exporter"
IOU_NOISE = 1e-5

WORKER_SHA256 = {
    YOLOX: {
        "decoded.npz": "bae7112dbe97ee2e6605efe78e215736bedadbfefcf9a195549e7d3c81c7c676",
        "upstream_n.npz": "618909a06f88f486b9bb33df31272bdbe2ec15b486d75172fe58243577876474",
        "upstream_t.npz": "b97adcd6226ecba8fabab393ac3f9244372342dbe04b66208e583b52eaebd55c",
        "upstream_s.npz": "9e709c42f4a0e75388c9848b3b3cbb734377ce5460d0638f9232985c1aae7ae9",
        "upstream_m.npz": "b9104c995fa1f95408cf94ceee2c463ee0472c0fdb57747bf6237b42ec78f704",
        "upstream_l.npz": "5164209a283d2e062097d03d959b4d6328e0ec729343d0828e0a21cbfe033781",
        "upstream_x.npz": "f9d2cc3b6c909d6a2fcff43f94b044f8ea91adc5aefdfb97a7f11cf30f437d82",
    },
    RTMW: {
        "decoded.npz": "73ed0f11450ad1192e680a09bfb9d49c60036e39ae5b9ba4ba4e4eab1662e0d0",
        "upstream_m.npz": "5e394b0a29944c28af9655c5324fb9f64fef16cc888a83a7bc0b9e912cd41851",
        "upstream_l-256.npz": "f69172e4bdbad04ee0a562703f2a4eba1b6057bcd0780e9a54bcca6ac879ad9b",
        "upstream_x-256.npz": "8f1b5142e731e99509bf6443d0ef5aa10ab159a2bc5ea3d46c56ed891ff2f046",
        "upstream_l-384.npz": "066e247b10e49249407fa5ec0c493a4073f79e7b4e32e442e63dd7cc3288387d",
        "upstream_x-384.npz": "faf82c2e8ce8d19d901e0bd7eb29ed49d13db0e883ef4c775257524b640f9952",
    },
}


def load_worker(parity: Path, key: str, name: str) -> dict[str, np.ndarray]:
    path = parity / "worker" / name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != WORKER_SHA256[key][name]:
        raise SystemExit(f"{name} has the SHA-256 {digest}, not {WORKER_SHA256[key][name]}")
    with np.load(path, allow_pickle=False) as data:
        return {item: data[item] for item in data.files}


def spacings(values: np.ndarray, count: int) -> np.ndarray:
    return count * np.spacing(np.maximum(np.abs(values), 1).astype(np.float32)).astype(np.float64)


def build(key: str, size: str, precision: str, ep: str) -> tuple[Any, dict[str, Any]]:
    """Return the detector and the facts of its session. The CPU EP uses `create_detector`."""
    sidecar = load_detector_sidecar(key)
    start = time.perf_counter()
    if ep == "cpu":
        return create_detector(key, execution_provider=ep, size=size, precision=precision), {
            "start_s": time.perf_counter() - start
        }
    session, report = open_session(get_detector(key), sidecar, size, precision, execution_provider=ep)
    make = GenericObjectDetector if key == YOLOX else GenericKeypointDetector
    facts = {
        "start_s": time.perf_counter() - start,
        "used_ep": report.used_ep,
        "cpu_nodes": report.cpu_nodes,
        "cpu_op_types": list(report.cpu_op_types),
    }
    return make(sidecar, size, precision, session), facts


# ---------------------------------------------------------------------------------------------
# yolox-person
# ---------------------------------------------------------------------------------------------


def upstream_persons(up: dict[str, np.ndarray], image: str, min_score: float) -> dict[str, np.ndarray]:
    """The upstream person detections of one image, with the anchor of each row."""
    anchors = up[f"{image}__cand_index"][up[f"{image}__keep"]]
    keep = (up[f"{image}__det_labels"] == 0) & (up[f"{image}__det_scores"].astype(np.float64) > min_score)
    return {"anchors": anchors[keep], "boxes": up[f"{image}__det_boxes"][keep], "scores": up[f"{image}__det_scores"][keep]}


def decode_rows(boxes: np.ndarray, scores: np.ndarray, sidecar: Any, geometry: Any, min_score: float) -> dict[str, np.ndarray]:
    found = decode_nms(boxes, scores, None, sidecar.object.decode, sidecar.object.classes, geometry.input_size, geometry, min_score)
    return {"anchors": found["rows"], "boxes": found["boxes"], "scores": found["scores"]}


def decode_alone(side: dict[str, np.ndarray], up: dict[str, np.ndarray], threshold: float) -> dict[str, Any]:
    """Y4: the same anchors, bit-equal scores, boxes within 4 float32 spacings."""
    side_at = {int(anchor): index for index, anchor in enumerate(side["anchors"])}
    up_at = {int(anchor): index for index, anchor in enumerate(up["anchors"])}
    only_up = [a for a in up_at if a not in side_at and up["scores"][up_at[a]] != np.float32(threshold)]
    only_side = [a for a in side_at if a not in up_at]
    bad_score = bad_box = 0
    largest = 0.0
    for anchor in set(side_at) & set(up_at):
        mine, theirs = side_at[anchor], up_at[anchor]
        bad_score += int(np.float32(side["scores"][mine]) != up["scores"][theirs])
        difference = np.abs(side["boxes"][mine] - up["boxes"][theirs].astype(np.float64))
        largest = max(largest, float(difference.max()))
        bad_box += int(np.any(difference > spacings(up["boxes"][theirs], 4)))
    passed = not only_up and not only_side and bad_score == 0 and bad_box == 0
    return {"pass": passed, "rows": len(side_at), "rows_upstream": len(up_at), "max_box_px": largest}


def causes(anchor: int, rows_a: tuple[np.ndarray, np.ndarray], rows_b: tuple[np.ndarray, np.ndarray], decode: Any, unpaired: set[int]) -> list[str]:
    """Y5c: the causes in the row difference of an anchor that one side keeps. `a` is the upstream (`>=`)."""
    (boxes_a, scores_a), (boxes_b, scores_b) = rows_a, rows_b
    threshold = np.float32(decode.nms.score_threshold)
    pass_a, pass_b = scores_a >= threshold, scores_b > threshold
    found = ["threshold"] if pass_a[anchor] != pass_b[anchor] else []
    others = np.flatnonzero(pass_a | pass_b)
    others = others[others != anchor]
    if others.size:
        limit = decode.nms.iou_threshold
        iou_a = box_iou(boxes_a[anchor].astype(np.float64), boxes_a[others].astype(np.float64))
        iou_b = box_iou(boxes_b[anchor].astype(np.float64), boxes_b[others].astype(np.float64))
        if (((iou_a > limit) != (iou_b > limit)) | (np.abs(iou_a - limit) < IOU_NOISE) | (np.abs(iou_b - limit) < IOU_NOISE)).any():
            found.append("iou")
        overlap = (iou_a > limit) | (iou_b > limit)
        order_a = np.sign(scores_a[anchor].astype(np.float64) - scores_a[others])
        order_b = np.sign(scores_b[anchor].astype(np.float64) - scores_b[others])
        if (overlap & (order_a != order_b)).any():
            found.append("order")
        if (overlap & np.isin(others, list(unpaired))).any():
            found.append("cascade")
    return found


def export_change(
    side: dict[str, np.ndarray], up: dict[str, np.ndarray],
    rows_side: tuple[np.ndarray, np.ndarray], rows_up: tuple[np.ndarray, np.ndarray],
    decode: Any, scale: float, both_at_zero: set[int] | None, min_score: float,
) -> dict[str, Any]:
    """Y5c: the decode of the session rows against the upstream person detections."""
    side_at = {int(anchor): index for index, anchor in enumerate(side["anchors"])}
    up_at = {int(anchor): index for index, anchor in enumerate(up["anchors"])}
    unpaired = set(side_at) ^ set(up_at)
    bad_box, largest, largest_score = 0, 0.0, 0.0
    for anchor in set(side_at) & set(up_at):
        mine, theirs = side_at[anchor], up_at[anchor]
        row = float(np.abs(rows_side[0][anchor].astype(np.float64) - rows_up[0][anchor]).max())
        difference = np.abs(side["boxes"][mine] - up["boxes"][theirs].astype(np.float64))
        bad_box += int(np.any(difference > row * scale * 1.000001 + spacings(up["boxes"][theirs], 4)))
        largest = max(largest, float(difference.max()))
        largest_score = max(largest_score, abs(float(side["scores"][mine]) - float(up["scores"][theirs])))
    unexplained = []
    for anchor in sorted(unpaired):
        straddle = (
            both_at_zero is not None and anchor in both_at_zero
            and (float(rows_side[1][anchor]) > min_score) != (float(rows_up[1][anchor]) > min_score)
        )
        if not straddle and not causes(anchor, rows_up, rows_side, decode, unpaired):
            unexplained.append(anchor)
    return {
        "pass": bad_box == 0 and not unexplained, "rows": len(side_at), "rows_upstream": len(up_at),
        "unpaired": len(unpaired), "unexplained": unexplained, "box_over_bound": bad_box,
        "max_box_px": largest, "max_score": largest_score,
    }


def run_yolox(args: argparse.Namespace) -> dict[str, Any]:
    sidecar = load_detector_sidecar(YOLOX)
    decode = sidecar.object.decode
    images = load_worker(args.parity, YOLOX, "decoded.npz")
    result: dict[str, Any] = {}
    for size in args.sizes or list(sidecar.sizes):
        up = load_worker(args.parity, YOLOX, f"upstream_{size}.npz")
        prepared = {name: preprocess_image(image, sidecar, size, "fp32") for name, image in images.items()}
        y1 = max(float(np.abs(tensor - up[f"{name}__canvas"].transpose(2, 0, 1)).max()) for name, (tensor, _) in prepared.items())
        y1_size = all(
            [geometry.values["n_h"], geometry.values["n_w"]] == up[f"{name}__resized_hw"].tolist()
            for name, (_, geometry) in prepared.items()
        )
        record: dict[str, Any] = {"Y1": {"pass": y1 == 0 and y1_size, "max_abs_diff": y1, "size_equal": y1_size}}
        for label, min_score in (("min_score 0", 0.0), ("min_score sidecar", float(decode.min_score))):
            parts = [
                decode_alone(
                    decode_rows(up[f"{name}__boxes"], up[f"{name}__scores"], sidecar, geometry, min_score),
                    upstream_persons(up, name, min_score), decode.nms.score_threshold,
                )
                for name, (_, geometry) in prepared.items()
            ]
            record[f"Y4 {label}"] = {
                "pass": all(part["pass"] for part in parts), "rows": sum(part["rows"] for part in parts),
                "rows_upstream": sum(part["rows_upstream"] for part in parts), "max_box_px": max(part["max_box_px"] for part in parts),
            }
        for ep in args.eps:
            for precision in args.precisions:
                detector, facts = build(YOLOX, size, precision, ep)
                names = list(images)
                tensors = [np.ascontiguousarray(up[f"{name}__canvas"].transpose(2, 0, 1)).astype(np.float32) for name in names]
                outputs = run_batches(detector.session, sidecar, tensors)
                for label, min_score in (("min_score 0", 0.0), ("min_score sidecar", float(decode.min_score))):
                    detected = detector.detect([images[name] for name in names], min_score)
                    equal, parts = True, []
                    for index, name in enumerate(names):
                        geometry = prepared[name][1]
                        rows_side = (outputs["boxes"][index], outputs["scores"][index])
                        rows_up = (up[f"{name}__boxes"], up[f"{name}__scores"])
                        side = decode_rows(*rows_side, sidecar, geometry, min_score)
                        equal &= np.array_equal(side["boxes"], detected[index].boxes) and np.array_equal(side["scores"], detected[index].scores)
                        both = None
                        if min_score > 0:
                            zero = decode_rows(*rows_side, sidecar, geometry, 0.0)["anchors"]
                            both = set(zero.tolist()) & set(upstream_persons(up, name, 0.0)["anchors"].tolist())
                        scale = max(geometry.src_w / geometry.values["n_w"], geometry.src_h / geometry.values["n_h"])
                        parts.append(export_change(side, upstream_persons(up, name, min_score), rows_side, rows_up, decode, scale, both, min_score))
                    facts[f"Y5a {label}"] = {"pass": bool(equal)}
                    facts[f"Y5c {label}"] = {
                        "pass": all(part["pass"] for part in parts),
                        **{item: sum(part[item] for part in parts) for item in ("rows", "rows_upstream", "unpaired", "box_over_bound")},
                        "unexplained": sum(len(part["unexplained"]) for part in parts),
                        "max_box_px": max(part["max_box_px"] for part in parts), "max_score": max(part["max_score"] for part in parts),
                    }
                detector.close()
                record[f"{ep}/{precision}"] = facts
                print(size, ep, precision, json.dumps(facts), flush=True)
        result[size] = record
        print(size, json.dumps({name: value for name, value in record.items() if name[0] == "Y"}), flush=True)
    return result


# ---------------------------------------------------------------------------------------------
# rtmw-wholebody133
# ---------------------------------------------------------------------------------------------


def run_rtmw(args: argparse.Namespace) -> dict[str, Any]:
    sidecar = load_detector_sidecar(RTMW)
    images = load_worker(args.parity, RTMW, "decoded.npz")
    result: dict[str, Any] = {}
    for size in args.sizes or list(sidecar.sizes):
        up = load_worker(args.parity, RTMW, f"upstream_{size}.npz")
        target = sidecar.size(size).target_size
        persons = [name[: -len("__matrix")] for name in up if name.endswith("__matrix") and not name.startswith("crafted")]
        frames = [images[max((image for image in images if person.startswith(image + "_")), key=len)] for person in persons]
        rois = [roi_from_box(up[f"{person}__box"].tolist()) for person in persons]
        geometries = [
            resize_geometry(sidecar.input.resize, target, frame.shape[1], frame.shape[0], roi)
            for frame, roi in zip(frames, rois, strict=True)
        ]
        r1 = sum(not np.array_equal(geometry.values["matrix"], up[f"{person}__matrix"]) for person, geometry in zip(persons, geometries, strict=True))
        r1b = max(
            float(np.abs(
                normalize(up[f"{person}__crop"], sidecar.input.normalization_for("fp32"), sidecar.input.color_format, "float32").transpose(2, 0, 1)
                - up[f"{person}__tensor"]
            ).max())
            for person in persons
        )
        raw_x = np.stack([up[f"{person}__raw_x"] for person in persons])
        raw_y = np.stack([up[f"{person}__raw_y"] for person in persons])
        crop_points = np.stack([up[f"{person}__kpt_crop"] for person in persons]).astype(np.float64)
        crop_scores = np.stack([up[f"{person}__score"] for person in persons])
        final = np.stack([up[f"{person}__kpt_src"] for person in persons]).astype(np.float64)
        final_scores = np.stack([up[f"{person}__score_src"] for person in persons])
        alone = decode_simcc(raw_x, raw_y, target)
        r4_score = int(np.count_nonzero(alone["scores"] != crop_scores))
        r4_point = int(np.count_nonzero(np.abs(alone["keypoints"] - crop_points) > spacings(crop_points, 1)))
        bound = np.stack([
            16 * float(np.spacing(np.float32(max(
                *np.abs(geometry.values["center"]), geometry.values["crop_w"], geometry.values["crop_h"], float(np.abs(points).max())
            ))))
            for geometry, points in zip(geometries, final, strict=True)
        ])[:, None, None]
        unprojected = np.stack([resize_inverse(points, geometry) for points, geometry in zip(crop_points, geometries, strict=True)])
        r4b = float((np.abs(unprojected - final) / bound).max())
        up_bins = alone["bins"]
        record: dict[str, Any] = {
            "persons": len(persons),
            "R1": {"pass": r1 == 0, "matrix_not_equal": r1},
            "R1b": {"pass": r1b == 0, "max_abs_diff": r1b},
            "R4": {"pass": r4_score == 0 and r4_point == 0, "score_not_equal": r4_score, "point_over_bound": r4_point},
            "R4b": {"pass": r4b <= 1, "max_fraction_of_bound": r4b, "score_equal": bool(np.array_equal(final_scores, crop_scores))},
        }
        for ep in args.eps:
            for precision in args.precisions:
                detector, facts = build(RTMW, size, precision, ep)
                # R5: the upstream tensors through the session, the decode and the unprojection.
                outputs = run_batches(detector.session, sidecar, [up[f"{person}__tensor"] for person in persons])
                decoded = decode_simcc(outputs["simcc_x"], outputs["simcc_y"], target)
                points = np.stack([resize_inverse(row, geometry) for row, geometry in zip(decoded["keypoints"], geometries, strict=True)])
                r_axis = np.stack([np.abs(outputs["simcc_x"] - raw_x).max(-1), np.abs(outputs["simcc_y"] - raw_y).max(-1)], -1).astype(np.float64)
                r = r_axis.max(-1)
                bad_score = int(np.count_nonzero(np.abs(decoded["scores"].astype(np.float64) - final_scores) > r))
                same_bin = decoded["bins"] == up_bins
                bad_point = int(np.count_nonzero(same_bin & (np.abs(points - final) > bound)))
                moved = np.argwhere(~same_bin)
                bad_bin = 0
                for person, point, axis in moved:
                    row = (raw_x, raw_y)[axis][person, point]
                    mine, theirs = decoded["bins"][person, point, axis], up_bins[person, point, axis]
                    if mine < 0 or theirs < 0:
                        bad_bin += int(abs(float(final_scores[person, point])) > r[person, point])
                    else:
                        bad_bin += int(abs(float(row[mine]) - float(row[theirs])) > 2 * r_axis[person, point, axis])
                facts["R5"] = {
                    "pass": bad_score == 0 and bad_point == 0 and bad_bin == 0, "score_over_r": bad_score,
                    "point_over_bound": bad_point, "bin_changes": int(len(moved)), "bin_change_over_2r": bad_bin, "max_r": float(r.max()),
                }
                # R7: the detector on the decoded images and the upstream boxes.
                found = detector.detect(frames, rois)
                missing = np.isnan(found.keypoints).any(-1)
                model = np.stack([
                    np.nan_to_num(row) @ geometry.values["matrix"][:, :2].T + geometry.values["matrix"][:, 2]
                    for row, geometry in zip(found.keypoints, geometries, strict=True)
                ])
                bins = np.rint(model * [raw_x.shape[-1] / target[1], raw_y.shape[-1] / target[0]])
                outlier = (np.abs(bins - up_bins) > 1).any(-1) | (missing != (up_bins < 0).any(-1))
                outlier[missing & (up_bins < 0).any(-1)] = False
                fractions = outlier.mean(-1)
                distance = np.linalg.norm(found.keypoints - final, axis=-1)
                facts["R7"] = {
                    "pass": bool(np.median(fractions) <= 0.15) and len(found.keypoints) == len(persons),
                    "median_outlier_fraction": float(np.median(fractions)), "all_keypoints_outlier_fraction": float(outlier.mean()),
                    "median_px": float(np.nanmedian(distance)), "max_score_diff": float(np.abs(found.scores - final_scores).max()),
                }
                detector.close()
                record[f"{ep}/{precision}"] = facts
                print(size, ep, precision, json.dumps(facts), flush=True)
        result[size] = record
        print(size, json.dumps({name: value for name, value in record.items() if name[0] == "R"}), flush=True)
    return result


# ---------------------------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------------------------


def median_seconds(action: Any, runs: int) -> float:
    values = []
    for _ in range(runs):
        start = time.perf_counter()
        made = action()
        values.append(time.perf_counter() - start)
        if hasattr(made, "close"):
            made.close()
    return statistics.median(values)


def run_timing(args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in (YOLOX, RTMW):
        sidecar, entry = load_detector_sidecar(key), get_detector(key)
        profile = sidecar.batching.batch_conversion.profile_id
        for size in args.sizes or list(sidecar.sizes):
            if size not in sidecar.sizes:
                continue
            for precision in args.precisions:
                path = entry.artifact(size, precision).path
                facts: dict[str, Any] = {
                    "file_bytes": path.stat().st_size,
                    "convert_to_b1_s": median_seconds(
                        partial(model_batch_convert, path, source_batch=sidecar.batching.batch, target_batch=1, profile_id=profile), args.runs
                    ),
                }
                for ep in args.eps:
                    for label, batch in (("b3", None), ("b1", 1)):
                        facts[f"create_detector {ep} {label}_s"] = median_seconds(
                            partial(create_detector, key, execution_provider=ep, size=size, precision=precision, batch=batch),
                            args.runs,
                        )
                result[f"{key} {size}/{precision}"] = facts
                print(key, size, precision, json.dumps(facts), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("yolox", "rtmw", "timing"))
    parser.add_argument("--parity", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--eps", nargs="+", default=["cpu"])
    parser.add_argument("--precisions", nargs="+", default=["fp32", "fp16"])
    parser.add_argument("--sizes", nargs="+")
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    result = {"yolox": run_yolox, "rtmw": run_rtmw, "timing": run_timing}[args.command](args)
    passes = [value["pass"] for record in result.values() for value in _walk(record) if "pass" in value]
    summary = {"all_pass": all(passes), "gates": len(passes), "failed": passes.count(False)}
    args.out.write_text(json.dumps({"summary": summary, "result": result}, indent=1), encoding="utf-8")
    print(json.dumps(summary))


def _walk(record: Any) -> Any:
    if isinstance(record, dict):
        yield record
        for value in record.values():
            yield from _walk(value)


if __name__ == "__main__":
    main()
