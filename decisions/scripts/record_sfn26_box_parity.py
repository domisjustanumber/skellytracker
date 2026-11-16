"""Record the box behaviour of the branch sfn26 with the early redetect, for the box parity test.

This script made the fixture `skellytracker/tests/pipelines/data/sfn26_box_parity.npz` for
ADR-RA0E (decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md). It is a one-off script. No
test runs it.

    python -B decisions/scripts/record_sfn26_box_parity.py <work folder> <fixture path>

The work folder must be outside this repository. The script does these steps:

1. It clones this repository to `<work folder>/skellytracker-2d356a6c` and checks out the
   skellytracker commit 2d356a6c (branch sfn26). The commit must be in the local object store
   (`git fetch upstream sfn26`).
2. It applies `sfn26_early_redetect.patch`: the early redetect of the commit 03b9c1dc, ported by
   hand (`BBoxPolicy.needs_recovery`, `StageState.needs_redetection`, its use in `should_redetect`
   and in `DetectionStage`).
3. It builds the environment of the clone with `uv sync` (Python 3.12, no dev group, the extras `onnx` and
   `onnx-cpu`) and runs itself there with `--record`. The old code downloads its ONNX models to
   the model cache of the user on first use.
4. The record step runs `human_tracker_config(preset="rtmpose", video_fps=30.0)` of the old code
   on the first video of the test recording (`skellytracker/tests/conftest.py`), with one camera,
   `Tracker.process_image` and `timestamp_ms = int(frame_index / 30 * 1000)`. The old code refuses
   a timestamp that is not an `int`, and its video runner uses this formula
   (`skellytracker/core/io/process_video.py:106`). It replaces the frames of `--blank` with black
   frames, because the first frames of the recording show a person in each frame.

The script does not import the package of this checkout. The record step stops if the package
`skellytracker` is not the package of the clone.

The fixture is one compressed `.npz` file with plain arrays (no pickle). `F` is the frame count.

| Array | Shape, dtype | Content |
|---|---|---|
| `frame_index` | `(F,)` int64 | The frame number |
| `timestamp_ms` | `(F,)` float64 | The timestamp that the tracker got. Each value is a whole number |
| `image_size` | `(2,)` int64 | Height, width |
| `detector_ran` | `(F,)` bool | `StageObservation.detector_ran` |
| `yolox_found` | `(F,)` bool | The detector ran and gave a box |
| `yolox_box` | `(F, 4)` float64 | The first YOLOX box, `x1, y1, x2, y2`. NaN when `yolox_found` is false |
| `yolox_score` | `(F,)` float64 | The confidence of that box. NaN when `yolox_found` is false |
| `keypoints_ran` | `(F,)` bool | RTMW ran. It does not run when the frame has no box |
| `keypoints_xy` | `(F, 133, 2)` float64 | The decoded points in full-frame pixels, in the order of the model output, before the score mask. NaN when `keypoints_ran` is false |
| `keypoints_score` | `(F, 133)` float64 | The decoded scores, in the same order. NaN when `keypoints_ran` is false |
| `model_to_schema_perm` | `(133,)` int64 | `tracker_points = model_points[model_to_schema_perm]` |
| `box_present` | `(F,)` bool | The frame has a box |
| `box_before_filter` | `(F, 4)` float64 | The input of the box filter: the YOLOX box, or the carried box after the floors. NaN when `box_present` is false |
| `smoothed_box` | `(F, 4)` float64 | The output of the box filter, before the clip. NaN when `box_present` is false |
| `bounding_box` | `(F, 4)` int64 | `bounding_boxes[0]`: the clipped box. -1 when `box_present` is false |
| `metadata` | `()` str | A JSON object: the commit, the patch hash, the video, the blank frames and the config values |

The tracker itself gives the points in the schema order, and it sets a point with a score below
`confidence_threshold` to NaN and its visibility to 0. The record step checks on each frame that
the tracker points are equal to the points that this rule gives from `keypoints_xy` and
`keypoints_score`. It also checks the clip rule: `bounding_box` is `int()` of `smoothed_box` after
a clamp of each `x` to `[0, width]` and of each `y` to `[0, height]`.

`patch_sha256` in the metadata is the SHA-256 of the patch file with LF line endings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

COMMIT = "2d356a6c41f831484251677050fafb2576193060"
EARLY_REDETECT_COMMIT = "03b9c1dc10dfa14fd49ca15b35d17ac71c569345"
REPO = Path(__file__).resolve().parents[2]
PATCH = Path(__file__).with_name("sfn26_early_redetect.patch")
RECORDING_URL = (
    "https://github.com/freemocap/skellysamples/releases/download/test_data_v06_09_25/freemocap_test_data.zip"
)
FPS = 30.0


def run(*command: str) -> None:
    """Run one command and stop on a failure."""
    print("+", *command, flush=True)
    subprocess.run(command, check=True)  # noqa: S603


def must(ok: object, *info: object) -> None:
    """Stop when a self-check of the record step fails."""
    if not ok:
        raise RuntimeError(f"The self-check failed: {info}")


def patch_sha256() -> str:
    """Give the SHA-256 of the patch file with LF line endings."""
    return hashlib.sha256(PATCH.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def find_video(work: Path) -> Path:
    """Give the first video of the test recording. Download the recording if no copy exists."""
    tail = Path("freemocap_test_data") / "synchronized_videos"
    for folder in (
        Path.home() / "freemocap_data" / "recordings" / tail,
        Path.home() / ".cache" / "skellytracker" / "test_data" / tail,
        work / "test_data" / tail,
    ):
        videos = sorted(folder.glob("*.mp4"))
        if videos:
            return videos[0]
    target = work / "test_data"
    target.mkdir(parents=True, exist_ok=True)
    zip_path, _ = urllib.request.urlretrieve(RECORDING_URL, target / "freemocap_test_data.zip")  # noqa: S310
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(target)  # noqa: S202
    return sorted(next(target.rglob("synchronized_videos")).glob("*.mp4"))[0]


def prepare(args: argparse.Namespace) -> None:
    """Make the clone with the patch and its environment, then run the record step there."""
    work = args.work.resolve()
    if work == REPO or REPO in work.parents:
        sys.exit("The work folder must be outside the repository.")
    work.mkdir(parents=True, exist_ok=True)
    clone = work / f"skellytracker-{COMMIT[:8]}"
    if not clone.exists():
        # core.autocrlf=false keeps LF files, so the patch applies on each machine.
        run("git", "clone", "--no-checkout", "-c", "core.autocrlf=false", str(REPO), str(clone))
        run("git", "-C", str(clone), "checkout", "--detach", COMMIT)
        run("git", "-C", str(clone), "apply", str(PATCH))
    head = subprocess.run(  # noqa: S603
        ("git", "-C", str(clone), "rev-parse", "HEAD"), check=True, capture_output=True, text=True  # noqa: S607
    ).stdout.strip()
    if head != COMMIT:
        sys.exit(f"The clone is at {head}, not at {COMMIT}.")
    run("git", "-C", str(clone), "apply", "--reverse", "--check", str(PATCH))  # the patch is applied
    video = args.video or find_video(work)
    uv = ("--project", str(clone), "--python", "3.12", "--frozen", "--no-dev", "--extra", "onnx", "--extra", "onnx-cpu")
    run("uv", "sync", *uv)
    run(
        "uv", "run", *uv, "--no-sync", "python", "-I", "-B", str(Path(__file__).resolve()),
        "--record", str(clone), str(args.fixture.resolve()), "--video", str(video),
        "--frames", str(args.frames), "--blank", args.blank,
    )  # fmt: skip


def record(args: argparse.Namespace) -> None:
    """Run the old tracker on the video and write the fixture. This step runs in the clone environment."""
    import cv2
    import numpy as np
    import onnxruntime
    import skellytracker
    from skellytracker.core.detectors.keypoint_detectors.rtmw.wholebody import rtmw_wholebody_detector as rtmw
    from skellytracker.core.tracker.tracker_factory import build_tracker
    from skellytracker.core.tracker.tracker_presets import human_tracker_config
    from skellytracker.core.tracker.tracker_state import TrackerState

    clone = args.work.resolve()
    if clone not in Path(skellytracker.__file__).resolve().parents:
        sys.exit(f"The package skellytracker is not the package of the clone: {skellytracker.__file__}")
    blank_start, blank_end = (int(part) for part in args.blank.split(":"))
    frames = args.frames

    config = human_tracker_config(preset="rtmpose", video_fps=FPS)
    stage_config = config.stages[0]
    tracker = build_tracker(config)
    stage = tracker.stages[0]
    seen: dict = {}

    decode = rtmw.simcc_pose_decode

    def decode_and_keep(*a, **k):  # noqa: ANN002, ANN003, ANN202
        xy, scores = decode(*a, **k)
        seen["decode"] = (np.array(xy, dtype=np.float64), np.array(scores, dtype=np.float64), scores.dtype.name)
        return xy, scores

    detect = stage.object_detector.detect

    def detect_and_keep(*a, **k):  # noqa: ANN002, ANN003, ANN202
        seen["yolox"] = detect(*a, **k)
        return seen["yolox"]

    smooth = stage._smooth_bbox  # noqa: SLF001

    def smooth_and_keep(raw_bbox, bbox_state, dt):  # noqa: ANN001, ANN202
        smoothed, bbox_state = smooth(raw_bbox, bbox_state, dt)
        seen["filter"] = (corners(raw_bbox), corners(smoothed))
        return smoothed, bbox_state

    def corners(box) -> list[float]:  # noqa: ANN001
        return [np.nan] * 4 if box is None else [box.x1, box.y1, box.x2, box.y2]

    rtmw.simcc_pose_decode = decode_and_keep
    stage.object_detector.detect = detect_and_keep
    stage._smooth_bbox = smooth_and_keep  # noqa: SLF001

    perm = np.asarray(rtmw._MODEL_TO_SCHEMA_PERM, dtype=np.int64)  # noqa: SLF001
    threshold = stage_config.keypoint_detectors[0].confidence_threshold
    points = len(perm)
    out = {
        "frame_index": np.arange(frames, dtype=np.int64),
        "timestamp_ms": np.array([int(i / FPS * 1000) for i in range(frames)], dtype=np.float64),
        "detector_ran": np.zeros(frames, dtype=bool),
        "yolox_found": np.zeros(frames, dtype=bool),
        "yolox_box": np.full((frames, 4), np.nan),
        "yolox_score": np.full(frames, np.nan),
        "keypoints_ran": np.zeros(frames, dtype=bool),
        "keypoints_xy": np.full((frames, points, 2), np.nan),
        "keypoints_score": np.full((frames, points), np.nan),
        "model_to_schema_perm": perm,
        "box_present": np.zeros(frames, dtype=bool),
        "box_before_filter": np.full((frames, 4), np.nan),
        "smoothed_box": np.full((frames, 4), np.nan),
        "bounding_box": np.full((frames, 4), -1, dtype=np.int64),
    }
    score_dtype = ""
    state = TrackerState.empty()
    capture = cv2.VideoCapture(str(args.video))
    for i in range(frames):
        ok, image = capture.read()
        if not ok:
            sys.exit(f"The video has only {i} frames.")
        if blank_start <= i < blank_end:
            image[:] = 0
        height, width = image.shape[:2]
        seen.clear()
        observation, state = tracker.process_image(image, i, state, timestamp_ms=int(out["timestamp_ms"][i]))
        body = observation.stages["body"]
        out["detector_ran"][i] = body.detector_ran
        must(body.detector_ran == ("yolox" in seen))
        if seen.get("yolox"):
            box = seen["yolox"][0]
            out["yolox_found"][i] = True
            out["yolox_box"][i] = corners(box)
            out["yolox_score"][i] = box.confidence
        out["box_before_filter"][i], out["smoothed_box"][i] = seen["filter"]
        out["box_present"][i] = bool(body.bounding_boxes)
        must(out["box_present"][i] == np.isfinite(out["smoothed_box"][i]).all())
        must(len(body.bounding_boxes) <= 1)
        offset = np.zeros(2)
        if body.bounding_boxes:
            box = body.bounding_boxes[0]
            out["bounding_box"][i] = corners(box)
            must(corners(box) == out["bounding_box"][i].tolist())
            # The clip rule of the old code: a clamp to the image, then int() (toward zero).
            x1, y1, x2, y2 = out["smoothed_box"][i]
            clip = [int(min(max(0.0, v), float(limit))) for v, limit in ((x1, width), (y1, height), (x2, width), (y2, height))]
            must(clip == out["bounding_box"][i].tolist(), (i, clip, box))
            offset = np.array([box.x1, box.y1])
        # The tracker points are the decoded points in the schema order, with the score mask.
        expected_xy = np.full((points, 2), np.nan)
        expected_visibility = np.zeros(points)
        if "decode" in seen:
            xy, scores, score_dtype = seen["decode"]
            out["keypoints_ran"][i] = True
            out["keypoints_xy"][i] = xy + offset
            out["keypoints_score"][i] = scores
            keep = scores[perm] >= np.float32(threshold) if score_dtype == "float32" else scores[perm] >= threshold
            expected_xy[keep] = out["keypoints_xy"][i][perm][keep]
            expected_visibility[keep] = scores[perm][keep]
        must(out["keypoints_ran"][i] == out["box_present"][i])
        must(np.array_equal(body.keypoints.xyz[:, :2], expected_xy, equal_nan=True), i)
        must(np.array_equal(body.keypoints.visibility, expected_visibility), i)
    capture.release()
    tracker.close()

    policy = stage_config.bbox_policy
    out["image_size"] = np.array([height, width], dtype=np.int64)
    out["metadata"] = np.array(json.dumps({
        "source": "skellytracker (freemocap/skellytracker), branch sfn26",
        "commit": COMMIT,
        "early_redetect_commit": EARLY_REDETECT_COMMIT,
        "patch": PATCH.name,
        "patch_sha256": patch_sha256(),
        "preset": "rtmpose",
        "call": "Tracker.process_image, one camera",
        "video": args.video.name,
        "recording_url": RECORDING_URL,
        "video_fps": FPS,
        "timestamp_ms": "int(frame_index / 30 * 1000)",
        "frames": frames,
        "blank_frames": [blank_start, blank_end],
        "blank_frames_note": "start is in, end is out; each pixel is 0",
        "box_order": "x1, y1, x2, y2",
        "image_size_order": "height, width",
        "keypoints": "decoded points before the score mask, model output order, full-frame pixels",
        "keypoints_score_dtype_in_old_code": score_dtype,
        "keypoint_confidence_threshold": threshold,
        "keypoint_model": stage_config.keypoint_detectors[0].model_name,
        "object_detector": stage_config.object_detector.model_dump(mode="json"),
        "bbox_policy": policy.model_dump(mode="json"),
        "bbox_smoothing": stage_config.bbox_smoothing.model_dump(mode="json"),
        "keypoint_smoothing": None if stage_config.keypoint_smoothing is None else "set",
        "clip": "int(min(max(0, v), limit)); limit is the width for x and the height for y",
        "execution_provider": tracker.sessions["onnx"].execution_provider if "onnx" in tracker.sessions else "unknown",
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__,
                     "onnxruntime": onnxruntime.__version__, "opencv": cv2.__version__},
    }, indent=1))  # fmt: skip
    args.fixture.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.fixture, **out)
    print(f"Wrote {args.fixture.name}: {frames} frames, {args.fixture.stat().st_size} bytes.")
    print("detector_ran:", np.flatnonzero(out["detector_ran"]).tolist())
    print("no box:", np.flatnonzero(~out["box_present"]).tolist())


def main() -> None:
    """Read the arguments and run one of the two steps."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("work", type=Path, help="the work folder, outside the repository")
    parser.add_argument("fixture", type=Path, help="the path of the fixture file")
    parser.add_argument("--video", type=Path, help="one camera video; the default is the test recording")
    parser.add_argument("--frames", type=int, default=200, help="the frame count")
    parser.add_argument("--blank", default="160:170", help="START:END of the black frames; END is out")
    parser.add_argument("--record", action="store_true", help="internal: the step in the clone environment")
    args = parser.parse_args()
    if args.record:
        record(args)
    else:
        prepare(args)


if __name__ == "__main__":
    main()
