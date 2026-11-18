"""Evidence of the proposal resize-pixel-tolerance: the alternating-picture race test of the nvJPEG hand-over.

Run from a checkout with the nvImageCodec wheels and the EP packs installed:

    uv run --no-sync python -B specs/model-sidecar/decisions/scripts/gpu_preprocess_race.py \
        --photo <photo> [--ep cuda trt-rtx] [--model-root ...] [--wait 1000] [--no-wait 300]

The sample of the proposal: one 720x1280 (W x H) photo of the package test images. Picture A is the
photo, B is its vertical flip, both JPEG quality 90, 4:2:2. Frame k of iteration i gets picture
(i + k) % 2, so each frame changes on each iteration. Old decoded batches stay alive at random, so
fresh and reused VRAM both occur. The model session is built before the preprocess session.

Two paths: letterbox -> yolox-person, and affine_crop (one fixed ROI) -> rtmw-wholebody133.
Each path runs with the wait (`cudaStreamSynchronize` of the decode stream) and without it.

- Hand-over 1 (decode -> graph) is wrong when the graph output differs from the CPU preprocess of
  the nvJPEG pixels of the given picture by more than 1.5 uint8 steps. The kind of a wrong frame:
  `stale` (it is the other picture), `zeros` (it is a black frame) or `partial`.
- Hand-over 2 (graph -> model) is wrong when the model output from the VRAM tensor differs by more
  than 1e-2 from a model run on a host copy of that tensor, made after the device runs.

It writes no file.
"""

from __future__ import annotations

import argparse
import faulthandler
from pathlib import Path

import cv2
import numpy as np
from gpu_preprocess_graphs import (
    BATCH,
    PRECISION,
    RTMW,
    SIZE,
    YOLOX,
    DeviceDecoder,
    add_common_arguments,
    bind_run,
    frame_inputs,
    load_cudart,
    model_file,
    preprocess_graph,
    session,
    thetas,
    versions,
)

from skellytracker.core.detectors.catalog import load_detector_sidecar
from skellytracker.core.detectors.processing.pre import resize_affine_crop
from skellytracker.core.detectors.processing.pre.normalize import IMAGENET_STD_RGB
from skellytracker.core.detectors.processing.pre.preprocess import preprocess_image

TOL1, TOL2 = 1.5, 1e-2
ROI_BOX = [100.0, 200.0, 620.0, 1100.0]


def race(decoder, pre, model, jpegs, refs, steps, theta, iterations, wait) -> str:
    """refs: the CPU tensors of picture A, picture B and a black frame."""
    m_in, m_names = model.get_inputs()[0].name, [o.name for o in model.get_outputs()]
    rng = np.random.default_rng(1234)
    alive, bad1, bad2, kinds, worst1, worst2 = [], 0, 0, {}, 0.0, 0.0
    for i in range(iterations):
        content = [(i + k) % 2 for k in range(BATCH)]
        images = decoder.decode([jpegs[c] for c in content], wait=wait)
        inputs = frame_inputs(images) | ({} if theta is None else {"theta": theta})
        tensor = bind_run(pre, inputs)[0]
        device_out = [v.numpy() for v in bind_run(model, {m_in: tensor})]
        host_in = tensor.numpy()  # the host copy for the check, after the device runs
        wrong = False
        for k, c in enumerate(content):
            error = float(np.abs((host_in[k] - refs[c]) * steps).max())
            if error > TOL1:
                wrong = True
                near = {kind: float(np.abs((host_in[k] - refs[j]) * steps).max()) for kind, j in (("stale", 1 - c), ("zeros", 2))}
                kind = next((kind for kind, e in near.items() if e <= TOL1), "partial")
                kinds[kind] = kinds.get(kind, 0) + 1
            else:
                worst1 = max(worst1, error)
        bad1 += wrong
        error2 = max(float(np.abs(a - b).max()) for a, b in zip(device_out, model.run(m_names, {m_in: host_in}), strict=True))
        if error2 > TOL2:
            bad2 += 1
        else:
            worst2 = max(worst2, error2)
        if rng.random() < 0.5:
            alive = [*alive, images][-4:]
        else:
            alive = []
    return (f"hand-over 1 wrong {bad1}/{iterations} iterations (wrong frames by kind {kinds}; worst passing "
            f"{worst1:.3f} steps); hand-over 2 wrong {bad2}/{iterations} (worst passing {worst2:.2e})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    add_common_arguments(parser)
    parser.add_argument("--photo", type=Path, required=True)
    parser.add_argument("--wait", type=int, default=1000, help="iterations with the wait")
    parser.add_argument("--no-wait", type=int, default=300, help="iterations without the wait")
    parser.add_argument("--watchdog", type=float, help="after this many seconds, print the stack of each thread and exit")
    args = parser.parse_args()
    if args.watchdog:
        faulthandler.dump_traceback_later(args.watchdog, exit=True)
    print(versions())
    photo = cv2.imread(str(args.photo))
    h, w = photo.shape[:2]
    flags = [cv2.IMWRITE_JPEG_QUALITY, 90, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, cv2.IMWRITE_JPEG_SAMPLING_FACTOR_422]
    jpegs = [cv2.imencode(".jpg", image, flags)[1].tobytes() for image in (photo, cv2.flip(photo, 0))]
    decoder = DeviceDecoder(load_cudart(args.cudart))
    pictures = [decoder.host_bgr(j) for j in jpegs] + [np.zeros_like(photo)]  # A, B, black
    yolox, rtmw = load_detector_sidecar(YOLOX, None), load_detector_sidecar(RTMW, None)
    roi = resize_affine_crop.roi_from_box(ROI_BOX)
    paths = {
        "letterbox": (yolox, None, 1.0),
        "affine_crop": (rtmw, roi, np.array(IMAGENET_STD_RGB).reshape(3, 1, 1)),
    }
    print(f"photo {w}x{h}, JPEG quality 90, 4:2:2, batch {BATCH}, A and its vertical flip B")
    for ep in args.ep:
        for name, (sidecar, crop_roi, steps) in paths.items():
            model, _ = session(model_file(sidecar, args.model_root), ep, sidecar.model_id)  # model first
            pre, _ = session(preprocess_graph(sidecar, w, h), ep, f"{name} graph")
            refs = [preprocess_image(p, sidecar, SIZE, PRECISION, crop_roi)[0] for p in pictures]
            theta = None if crop_roi is None else thetas(sidecar, [crop_roi] * BATCH, w, h)
            print(f"  A vs B reference: tensor max {np.abs((refs[0] - refs[1]) * steps).max():.0f} steps")
            for wait, iterations in ((True, args.wait), (False, args.no_wait)):
                result = race(decoder, pre, model, jpegs, refs, steps, theta, iterations, wait)
                print(f"RESULT {ep} {name} {'wait' if wait else 'no wait'}: {result}", flush=True)
    print("main returned; the process exits next", flush=True)


if __name__ == "__main__":
    main()
