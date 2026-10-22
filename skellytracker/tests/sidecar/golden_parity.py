"""Shared helpers for golden-fixture parity tests.

The fixtures under ``fixtures/golden/`` capture the pre-migration detector
output. They were produced on a different machine than CI/dev boxes (possibly
a different ONNX Runtime execution provider), so parity is asserted at the
precision the model itself has, not at bit-exact float tolerance:

* boxes (YOLOX): ``BOX_ATOL_PX`` pixels, confidence ``CONFIDENCE_ATOL``;
* SimCC keypoints: one SimCC bin, see :func:`simcc_bin_size_px`.

Each fixture's provenance is recorded in ``fixtures/golden/environments.json``
(fixtures are bare name->xy dicts or box lists, so there is no room for the
metadata inside them without breaking the loaders).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from skellytracker.core.detectors.processing.simcc_decode import (
    _SIMCC_SPLIT_RATIO,
    _stable_softmax,
)

GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden"
ENVIRONMENTS_PATH = GOLDEN_DIR / "environments.json"

# Provider the parity tests run on, so results do not depend on what
# auto-detection finds on the machine running the tests.
PARITY_EXECUTION_PROVIDER = "cpu"

# Object-detector boxes are in source-image pixels. Different execution
# providers / ORT versions move a box edge by a fraction of a pixel (observed
# up to ~0.4 px); half a pixel is below any meaningful localisation change.
BOX_ATOL_PX = 0.5
# Detector confidence is a sigmoid score in [0, 1]; 0.01 is one percentage point.
CONFIDENCE_ATOL = 0.01

# SimCC keypoints are an argmax over discrete bins, so numerical noise can
# move a keypoint by exactly one bin and by nothing smaller.
_BIN_FLOAT_EPS_PX = 1e-6


def load_golden(golden_path: Path) -> Any:
    return json.loads(golden_path.read_text())


def golden_environment(golden_path: Path) -> dict[str, Any]:
    """Provenance record (os, provider, onnxruntime, author, commit) of a fixture."""
    return json.loads(ENVIRONMENTS_PATH.read_text())[golden_path.name]


def simcc_bin_size_px(
    scale: NDArray, model_input_size_wh: tuple[int, int]
) -> tuple[float, float]:
    """Size of one SimCC bin, in source-image pixels, as ``(x, y)``.

    The model predicts a 1-D classification over ``input_size * split_ratio``
    bins per axis, so one bin is ``1 / split_ratio`` model-input pixels. The
    decoder maps model-input pixels back to the source image by multiplying by
    ``crop_scale / input_size`` (``crop_scale`` is the width/height of the
    source region that was warped to the model input). Hence per axis::

        bin_px = crop_scale / (input_size * split_ratio)

    ``split_ratio`` is the decoder's ``_SIMCC_SPLIT_RATIO``.
    """
    scale = np.asarray(scale, dtype=np.float64)
    in_w, in_h = model_input_size_wh
    return (
        float(scale[0]) / (in_w * _SIMCC_SPLIT_RATIO),
        float(scale[1]) / (in_h * _SIMCC_SPLIT_RATIO),
    )


# Where the golden bin is not within one bin of the current argmax, it must at
# least have been a near-peak candidate: its probability must be at least this
# fraction of the winning bin's probability (see SimccParityRun).
MIN_GOLDEN_BIN_PEAK_FRACTION = 0.5


class SimccParityRun:
    """One detector run plus the SimCC softmax needed to judge golden keypoints.

    RTMW/RTMPose SimCC distributions are often very flat (peak softmax
    probability 0.05-0.2 for RTMW), so which of several nearly-equal bins wins
    the argmax can differ between execution providers / ORT versions by more
    than one bin (observed up to 4 bins). A golden keypoint therefore passes if
    EITHER of these holds on each axis:

    * it is within one SimCC bin of the current output (see
      :func:`simcc_bin_size_px`), or
    * the golden location's bin has probability >=
      ``MIN_GOLDEN_BIN_PEAK_FRACTION`` x the peak probability in the current
      model output, i.e. the golden answer is still a plausible argmax of
      the model, just not the one picked on this machine.
    """

    def __init__(self, detector: Any, image: NDArray) -> None:
        # Same pipeline as detector.detect(), with the raw SimCC output kept.
        tensor, metadata = detector.preprocess(image)
        model_name = detector.config.model_name
        ort_session = detector.session.get_session(model_name)
        input_name = ort_session.get_inputs()[0].name
        raw = detector.session.run(
            model_name, {input_name: np.ascontiguousarray(tensor[np.newaxis])}
        )
        self.keypoints = detector.postprocess(raw, metadata)
        self._center = np.asarray(metadata.center, dtype=np.float64)
        self._scale = np.asarray(metadata.scale, dtype=np.float64)
        in_h, in_w = detector.config.input_size
        self._input_wh = (in_w, in_h)
        self.bin_xy = simcc_bin_size_px(self._scale, self._input_wh)
        simcc_x, simcc_y = raw
        self._prob_x = _stable_softmax(np.asarray(simcc_x)[0])
        self._prob_y = _stable_softmax(np.asarray(simcc_y)[0])
        # Per-keypoint confidence exactly as the decoder defines it (mean of
        # the x/y peak probabilities). Unlike ``keypoints.visibility`` it is
        # not zeroed for points below the detector's confidence threshold.
        self.scores = 0.5 * (self._prob_x.max(axis=-1) + self._prob_y.max(axis=-1))

    def _golden_bin(self, golden_xy: NDArray) -> NDArray:
        """Inverse of ``decode_simcc``: source-image xy -> (float) SimCC bin."""
        unit = (np.asarray(golden_xy) - self._center + self._scale / 2) / self._scale
        return unit * np.asarray(self._input_wh) * _SIMCC_SPLIT_RATIO

    def assert_keypoint_matches(
        self, index: int, name: str, actual_xy: NDArray, golden_xy: NDArray
    ) -> None:
        assert np.all(np.isfinite(actual_xy)), (
            f"{name}: detector returned {actual_xy} (below threshold) but the "
            f"golden fixture has {golden_xy}"
        )
        diff = np.abs(np.asarray(actual_xy) - np.asarray(golden_xy))
        within_one_bin = diff <= np.asarray(self.bin_xy) + _BIN_FLOAT_EPS_PX
        golden_bin = np.rint(self._golden_bin(golden_xy)).astype(int)
        plausible = []
        for axis, probs in enumerate((self._prob_x[index], self._prob_y[index])):
            b = int(np.clip(golden_bin[axis], 0, probs.shape[0] - 1))
            plausible.append(
                probs[b] >= MIN_GOLDEN_BIN_PEAK_FRACTION * probs.max()
            )
        ok = within_one_bin | np.asarray(plausible)
        assert np.all(ok), (
            f"{name}: actual={actual_xy}, expected={golden_xy}, |diff|={diff}; "
            f"one SimCC bin={self.bin_xy}, per-axis within-one-bin="
            f"{within_one_bin}, golden-bin-plausible={plausible}"
        )
