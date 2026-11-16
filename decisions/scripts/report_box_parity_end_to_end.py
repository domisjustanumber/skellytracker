"""Report B of the box parity: the built-in `yolox-rtmw-wholebody` with the real models against the recording of sfn26.

This script made the end-to-end numbers for ADR-RA0E
(decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md). It is a report with no pass limit. No
test runs it. Run it in the environment of this checkout:

    uv run --no-sync python -I -B decisions/scripts/report_box_parity_end_to_end.py <fixture> <video> --ep cpu

- `<fixture>` is `skellytracker/tests/pipelines/data/sfn26_box_parity.npz`
  (`record_sfn26_box_parity.py` gives its arrays).
- `<video>` is the video of the fixture: the first video of the test recording that
  `skellytracker/tests/conftest.py` downloads. The metadata of the fixture gives its name.
- `--ep` is the EP key of the run. The ONNX files of the two models must be in
  `skellytracker/core/model_zoo/`.

The script loads the built-in, sets `precision: fp32` on its two `onnx_model` nodes in the loaded
config, and runs it in `video` with one camera on the frames of the fixture, with the timestamps of
the fixture. It makes the blank frames of the fixture black, as the record step did. It prints:

- the count of frames where `node_ran` of the node `person` differs from `detector_ran`;
- the IoU of `person_roi` and `smoothed_box` on the frames where both sides have a box, and the
  count of frames where only one side has a box;
- the distance in pixels between the points with a score of 0.4 or more on both sides.

The values differ by design: the crop pixels, the re-exported models, the points below 0.4 and the
confidence of a carried box (ADR-RA0E, Consequences).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from skellytracker.core.pipelines import Frame, load_pipeline, start_pipeline

BUILT_IN = "yolox-rtmw-wholebody@skellytracker"
MIN_SCORE = 0.4


def iou(a: np.ndarray, b: np.ndarray) -> float:
    """Give the IoU of two `x1, y1, x2, y2` boxes."""
    width = min(a[2], b[2]) - max(a[0], b[0])
    height = min(a[3], b[3]) - max(a[1], b[1])
    inter = max(0.0, width) * max(0.0, height)
    return float(inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter))


def main() -> None:
    """Run the built-in on the frames of the fixture and print the report."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("fixture", type=Path, help="the path of the fixture file")
    parser.add_argument("video", type=Path, help="the video of the fixture")
    parser.add_argument("--ep", default="cpu", help="the EP key of the run")
    args = parser.parse_args()

    data = np.load(args.fixture, allow_pickle=False)
    metadata = json.loads(str(data["metadata"]))
    if args.video.name != metadata["video"]:
        sys.exit(f"The fixture is from the video {metadata['video']}, not from {args.video.name}.")
    blank_start, blank_end = metadata["blank_frames"]
    frames = len(data["frame_index"])

    config = load_pipeline(BUILT_IN)
    for node in config.nodes:
        if node.type == "onnx_model":
            node.params.precision = "fp32"  # the old tracker ran fp32 models

    flag_differs: list[int] = []
    only_one_box: list[int] = []
    ious: list[float] = []
    distances: list[np.ndarray] = []
    capture = cv2.VideoCapture(str(args.video))
    with start_pipeline(config, camera_ids=[0], running_mode="video", execution_provider=args.ep) as run:
        print("precision:", {node_id: plan.precision for node_id, plan in run._executor.plans.items()})  # noqa: SLF001
        print("warnings:", [warning.code for warning in run.warnings])
        for i in range(frames):
            ok, image = capture.read()
            if not ok:
                sys.exit(f"The video has only {i} frames.")
            if blank_start <= i < blank_end:
                image[:] = 0
            result = run.process(Frame(image, int(data["frame_index"][i]), float(data["timestamp_ms"][i])))
            if result["node_ran"]["person"] != data["detector_ran"][i]:
                flag_differs.append(i)
            roi, points = result["person_roi"], result["wholebody"]
            if bool(roi.present[0]) != bool(data["box_present"][i]):
                only_one_box.append(i)
            elif roi.present[0]:
                cx, cy, w, h = roi.rois[0, :4]
                ious.append(iou(np.array([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]), data["smoothed_box"][i]))
            if points.present[0] and data["keypoints_ran"][i]:
                both = (points.score[0] >= MIN_SCORE) & (data["keypoints_score"][i] >= MIN_SCORE)
                distances.append(np.linalg.norm(points.xyz[0, both, :2] - data["keypoints_xy"][i][both], axis=1))
    capture.release()

    print(f"frames: {frames}, execution provider: {args.ep}")
    print(f"frames where node_ran.person differs from detector_ran: {len(flag_differs)} {flag_differs}")
    print(f"frames where only one side has a box: {len(only_one_box)} {only_one_box}")
    if ious:
        print(f"IoU of person_roi and smoothed_box, {len(ious)} frames: min {min(ious):.4f}, median {np.median(ious):.4f}, mean {np.mean(ious):.4f}")
    found = np.concatenate(distances) if distances else np.zeros(0)
    if len(found):
        print(
            f"distance of the points with a score of {MIN_SCORE} or more on both sides, {len(found)} points: "
            f"median {np.median(found):.3f} px, 95th percentile {np.percentile(found, 95):.3f} px, max {found.max():.3f} px"
        )


if __name__ == "__main__":
    main()
