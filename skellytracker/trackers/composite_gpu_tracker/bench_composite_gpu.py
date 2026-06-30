"""
Microbench for CompositeGPUSession — validates batched inference throughput.

Run:
    uv run python -m skellytracker.trackers.composite_gpu_tracker.bench_composite_gpu
        --provider cuda --batch-sizes 1 2 3 4

Measures single-image and batched latency for the composite GPU pipeline.
Each batch size N uses its own session (session create + warmup excluded from
timed loops). Pipeline-level validation requires running the full freemocap app.

Note: this bench does NOT require ONNX models to be downloaded. It measures
the framework overhead and ROI crop throughput. Set body/hand/face ONNX paths
via environment variables to test with real models:
  SKEL_GPU_BODY_ONNX=/path/to/rtmo.onnx
  SKEL_GPU_HAND_ONNX=/path/to/rtmpose_hand.onnx
  SKEL_GPU_FACE_ONNX=/path/to/rtmpose_face.onnx
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from typing import get_args

import numpy as np

from skellytracker.utilities.gpu_utils.model_registry import ModelSource, ModelSpec
from skellytracker.utilities.gpu_utils.ort_session_utils import ExecutionProviderName
from skellytracker.trackers.composite_gpu_tracker.composite_gpu_session import (
    CompositeGPUSession,
    CompositeGPUSessionConfig,
)

logger = logging.getLogger(__name__)


def _summary(label: str, samples_ms: list[float]) -> str:
    arr = np.asarray(samples_ms)
    return (
        f"{label:32s}  n={len(arr):4d}  "
        f"mean={arr.mean():7.2f}ms  "
        f"p50={np.percentile(arr, 50):7.2f}ms  "
        f"p95={np.percentile(arr, 95):7.2f}ms  "
        f"max={arr.max():7.2f}ms"
    )


def _make_synthetic_image(h: int, w: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, size=(h, w, 3), dtype=np.uint8)


def run(
    *,
    provider: ExecutionProviderName,
    batch_sizes: list[int],
    iterations: int,
    image_h: int,
    image_w: int,
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(name)s | %(message)s")

    print(
        f"\nCompositeGPUSession bench — provider={provider!r}, "
        f"image_shape=({image_h}, {image_w}), iters_per_size={iterations}\n"
        f"(one session per batch size; create/warmup excluded from timed loops)\n"
    )

    body_spec = ModelSpec.rtmo_medium()
    hand_spec = ModelSpec.mediapipe_hand_landmark()
    face_spec = ModelSpec.rtmpose_face()
    body_env = os.environ.get("SKEL_GPU_BODY_ONNX")
    hand_env = os.environ.get("SKEL_GPU_HAND_ONNX")
    face_env = os.environ.get("SKEL_GPU_FACE_ONNX")

    has_models = bool(body_env or hand_env or face_env)
    if not has_models:
        print("No SKEL_GPU_*_ONNX env vars set — models will be auto-downloaded.\n")

    if body_env:
        body_spec = body_spec.model_copy(update={"source": ModelSource(local_path=body_env)})
    if hand_env:
        hand_spec = hand_spec.model_copy(update={"source": ModelSource(local_path=hand_env)})
    if face_env:
        face_spec = face_spec.model_copy(update={"source": ModelSource(local_path=face_env)})

    print(f"Models: body={'local' if body_env else 'download'}, "
          f"hand={'local' if hand_env else 'download'}, "
          f"face={'local' if face_env else 'download'}")

    pool = [_make_synthetic_image(image_h, image_w, seed=i) for i in range(max(batch_sizes) * 2)]

    single_session = CompositeGPUSession.create(
        CompositeGPUSessionConfig(
            execution_provider=provider,
            batch_size=1,
            body_spec=body_spec,
            hand_spec=hand_spec,
            face_spec=face_spec,
            detect_hands=True,
            detect_face=True,
        ),
    )
    print(f"active provider (batch_size=1): {single_session.active_provider!r}\n")

    single_samples_ms: list[float] = []
    for i in range(iterations):
        t0 = time.perf_counter()
        single_session.predict_single(pool[i % len(pool)])
        single_samples_ms.append((time.perf_counter() - t0) * 1e3)
    print(_summary("predict_single (batch_size=1)", single_samples_ms))
    del single_session

    for n in batch_sizes:
        if n < 1:
            continue
        session = CompositeGPUSession.create(
            CompositeGPUSessionConfig(
                execution_provider=provider,
                batch_size=n,
                body_spec=body_spec,
                hand_spec=hand_spec,
                face_spec=face_spec,
                detect_hands=True,
                detect_face=True,
            ),
        )
        batch_samples_ms: list[float] = []
        for i in range(iterations):
            batch = [pool[(i + k) % len(pool)] for k in range(n)]
            t0 = time.perf_counter()
            session.predict_batch(batch)
            batch_samples_ms.append((time.perf_counter() - t0) * 1e3)

        per_image = np.asarray(batch_samples_ms) / n
        arr = np.asarray(batch_samples_ms)
        print(
            f"predict_batch(N={n:<2d})            "
            f"  n={len(arr):4d}  "
            f"mean={arr.mean():7.2f}ms  "
            f"p50={np.percentile(arr, 50):7.2f}ms  "
            f"p95={np.percentile(arr, 95):7.2f}ms  "
            f"per_image_mean={per_image.mean():6.2f}ms"
        )
        del session

    print(
        f"\nReference: target < 33 ms/frame per camera for real-time (30 FPS).\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=list(get_args(ExecutionProviderName)),
        default="cuda",
    )
    parser.add_argument("--batch-sizes", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--image-h", type=int, default=720)
    parser.add_argument("--image-w", type=int, default=1280)
    args = parser.parse_args()
    run(
        provider=args.provider,  # type: ignore[arg-type]
        batch_sizes=args.batch_sizes,
        iterations=args.iterations,
        image_h=args.image_h,
        image_w=args.image_w,
    )


if __name__ == "__main__":
    main()
