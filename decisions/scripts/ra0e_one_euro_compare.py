"""Compare the One Euro filter of the reference `node_smooth_roi` with the code of the branch sfn26.

This script made the comparison in the evidence of ADR-RA0E
(decisions/evidence/RA0E-sfn26-box-behaviour.md). It is a one-off script. No test runs it.

The old side is `one_euro_step` of `skellytracker/core/temporal_processing/one_euro_array.py` at
the skellytracker commit 2d356a6c (branch sfn26). That branch is not in this checkout, so the
caller gives a copy of the file:

    git show upstream/sfn26:skellytracker/core/temporal_processing/one_euro_array.py > <folder>/one_euro_array.py
    uv run --no-sync python -I decisions/scripts/ra0e_one_euro_compare.py <folder>/one_euro_array.py

`old_sequence` is a copy of the steps of `apply_bbox_one_euro`
(`skellytracker/core/temporal_processing/bbox_smoothing.py:38-64` at that commit) and of
`_dt_from_context` (`skellytracker/core/tracker/detection_stage.py:835-845`), on plain arrays. The
new side is `specs/pipeline/reference/node_smooth_roi.py` with the filter `one_euro`.

The script prints the number of sequences and the largest difference of a corner, in pixels. It
fails when one sequence has a box on one side only.
"""

from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np

REFERENCE = Path(__file__).resolve().parents[2] / "specs" / "pipeline" / "reference"
SEQUENCES = 3000
RESET_AFTER_MS = 500.0


def load(path: Path) -> ModuleType:
    """Load one module by its path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def old_sequence(old: ModuleType, boxes: list[Any], times: list[float], cfg: dict[str, float]) -> list[Any]:
    """Run the steps of `apply_bbox_one_euro` on a sequence of [x1, y1, x2, y2] boxes or None."""
    work, last_t, out = None, None, []
    for box, t in zip(boxes, times, strict=True):
        dt = None if last_t is None or t <= last_t else (t - last_t) / 1000.0
        last_t = t
        if box is None:
            work = None
            out.append(None)
            continue
        reset = work is None or dt is None or dt > RESET_AFTER_MS / 1000.0
        if work is None:
            work = old.OneEuroWorkspace.create((2, 2))
        raw = np.array([[box[0], box[1]], [box[2], box[3]]], dtype=np.float64)
        if reset:
            np.copyto(work.filtered_values, raw)
            work.derivative_values.fill(0.0)
        else:
            old.one_euro_step(
                raw, work.filtered_values, work.derivative_values, dt=dt, min_cutoff=cfg["min_cutoff"],
                beta=cfg["beta"], d_cutoff=cfg["d_cutoff"], workspace=work,
            )
        work.filtered_values.sort(axis=0)
        f = work.filtered_values
        out.append([float(f[0, 0]), float(f[0, 1]), float(f[1, 0]), float(f[1, 1])])
    return out


def main(argv: list[str]) -> int:
    old = load(Path(argv[1]))
    load(REFERENCE / "node_roi_from_points.py")
    new = load(REFERENCE / "node_smooth_roi.py")
    rng = random.Random(7)  # noqa: S311 (test data, not a secret)
    worst = 0.0
    for _ in range(SEQUENCES):
        cfg = {
            "min_cutoff": rng.choice([3.0, 0.5, 1.0, 10.0]),
            "beta": rng.choice([0.02, 0.0, 0.5]),
            "d_cutoff": rng.choice([1.0, 0.3, 5.0]),
        }
        t, boxes, times = 0.0, [], []
        cx, cy, w, h = rng.uniform(100, 900), rng.uniform(100, 900), rng.uniform(5, 600), rng.uniform(5, 600)
        for _ in range(rng.randint(2, 25)):
            t += rng.choice([33.333333, 16.0, 40.0, 100.0, 499.0, 500.0, 501.0, 900.0])
            if rng.random() < 0.3:
                cx, cy = cx + rng.uniform(-600, 600), cy + rng.uniform(-600, 600)
                w, h = rng.uniform(1, 800), rng.uniform(1, 800)
            else:
                cx, cy = cx + rng.uniform(-9, 9), cy + rng.uniform(-9, 9)
                w, h = abs(w + rng.uniform(-9, 9)), abs(h + rng.uniform(-9, 9))
            boxes.append(None if rng.random() < 0.1 else [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2])
            times.append(t)
        frames: list[Any] = [
            None if b is None else [[(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, b[2] - b[0], b[3] - b[1], 0.0]] for b in boxes
        ]
        # Half of the sequences use a row that is not present in place of an empty input.
        if rng.random() < 0.5:
            frames = [[None] if frame is None else frame for frame in frames]
        params = {"filter": "one_euro", "reset_after_ms": RESET_AFTER_MS, **cfg}
        rois = new.run(params, {"running_mode": "video", "frames": frames, "timestamps_ms": times})["rois"]
        for given, expected in zip(rois, old_sequence(old, boxes, times, cfg), strict=True):
            row = None if given is None else given[0]
            if (row is None) != (expected is None):
                raise AssertionError("one side has a box and the other side has none")
            if row is None:
                continue
            corners = [row[0] - row[2] / 2, row[1] - row[3] / 2, row[0] + row[2] / 2, row[1] + row[3] / 2]
            worst = max(worst, *(abs(a - b) for a, b in zip(corners, expected, strict=True)))
    print(f"sequences {SEQUENCES}, largest corner difference {worst} px")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
