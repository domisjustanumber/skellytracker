"""Tests for the MediaPipe Holistic runner (stage 1.8 of the implementation plan)."""
from __future__ import annotations

import pathlib
import subprocess
import sys

import cv2
import numpy as np
import pytest

from skellytracker.core.detectors.mediapipe_holistic import (
    GROUPS,
    POINT_NAMES,
    HolisticKeypoints,
    HolisticRunner,
)

_ALL_GROUPS = {"body", "right_hand", "left_hand", "face"}


def _found_groups(kpts: HolisticKeypoints) -> set[str]:
    return {
        name for name, start, count in GROUPS
        if np.isfinite(kpts.xyz[0, start:start + count]).all()
    }


def test_point_names_and_groups():
    assert len(POINT_NAMES) == 33 + 21 + 21 + 478
    assert GROUPS == (("body", 0, 33), ("right_hand", 33, 21), ("left_hand", 54, 21), ("face", 75, 478))
    assert POINT_NAMES[0] == "body/nose"
    assert POINT_NAMES[33] == "right_hand/wrist"
    assert POINT_NAMES[54] == "left_hand/wrist"
    assert POINT_NAMES[75] == "face/face_0000"
    assert POINT_NAMES[-1] == "face/face_0477"
    assert len(set(POINT_NAMES)) == len(POINT_NAMES)


def test_image_gives_each_group(test_image):
    with HolisticRunner("image") as runner:
        kpts = runner.run(test_image)
    h, w = test_image.shape[:2]
    assert kpts.xyz.shape == (1, len(POINT_NAMES), 3)
    assert kpts.score.shape == (1, len(POINT_NAMES))
    assert _found_groups(kpts) == _ALL_GROUPS
    assert kpts.present.tolist() == [True]
    assert kpts.instance_score.tolist() == [1.0]
    assert (kpts.xyz[0, :, 0] >= 0).all() and (kpts.xyz[0, :, 0] <= w).all()
    assert (kpts.xyz[0, :, 1] >= 0).all() and (kpts.xyz[0, :, 1] <= h).all()
    assert ((kpts.score >= 0) & (kpts.score <= 1)).all()


def test_empty_image_gives_padding_row():
    with HolisticRunner("image") as runner:
        kpts = runner.run(np.zeros((240, 320, 3), np.uint8))
    assert kpts.present.tolist() == [False]
    assert kpts.instance_score.tolist() == [0.0]
    assert np.isnan(kpts.xyz).all()
    assert (kpts.score == 0).all()


def test_video_timestamps_must_increase(test_image):
    with HolisticRunner("video") as runner:
        runner.run(test_image, 0.0)
        runner.run(test_image, 0.5)  # less than 1 ms later: MediaPipe still gets an increasing integer
        with pytest.raises(ValueError, match="timestamp_ms must increase"):
            runner.run(test_image, 0.5)
        with pytest.raises(ValueError, match="timestamp_ms must increase"):
            runner.run(test_image, None)
        runner.run(test_image, 1.0)  # a refused call changes no state


def test_close_twice_and_run_after_close(test_image):
    runner = HolisticRunner("image")
    runner.close()
    runner.close()
    with pytest.raises(RuntimeError, match="closed"):
        runner.run(test_image)


_GC_ON_WORKER_THREAD = """
import gc, threading
import numpy as np
from skellytracker.core.detectors.mediapipe_holistic import HolisticRunner
runner = HolisticRunner("image")
runner.cycle = runner
runner.run(np.zeros((64, 64, 3), np.uint8))
executor = runner._landmarker._lib._executor  # the one worker thread of the landmarker
del runner
gc.disable()
future = executor.submit(gc.collect)
waiter = threading.Thread(target=future.result, daemon=True)
waiter.start()
waiter.join(30)
print("HANG" if waiter.is_alive() else "ok", flush=True)
import os
os._exit(0)
"""


def test_gc_on_the_landmarker_worker_thread_does_not_hang():
    # A runner in a reference cycle that the garbage collector frees on the worker thread of its own
    # landmarker: a direct close() there waits on that same thread for ever.
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", _GC_ON_WORKER_THREAD],
        capture_output=True, text=True, timeout=120,
    )
    assert result.stdout.strip().splitlines()[-1] == "ok", result.stderr[-2000:]


@pytest.mark.video
def test_video_gives_each_group(test_video_path: pathlib.Path):
    cap = cv2.VideoCapture(str(test_video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    per_frame: list[set[str]] = []
    try:
        with HolisticRunner("video") as runner:
            for frame_index in range(20):
                ok, frame = cap.read()
                if not ok:
                    break
                per_frame.append(_found_groups(runner.run(frame, frame_index * 1000.0 / fps)))
    finally:
        cap.release()
    assert len(per_frame) == 20
    assert all({"body", "face"} <= groups for groups in per_frame)
    assert set().union(*per_frame) == _ALL_GROUPS
