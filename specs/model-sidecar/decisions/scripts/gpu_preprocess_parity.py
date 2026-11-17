"""Evidence of the proposal resize-pixel-tolerance: the GPU preprocess path against the CPU reference.

Run from a checkout with the nvImageCodec wheels (`nvidia-nvimgcodec-cu13`, `nvidia-nvjpeg`) and
the EP packs installed:

    uv run --no-sync python -B specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py \
        --frames <videos folder> <photo> [--configs uint8:linear float32:linear uint8:cubic ...] \
        [--ep cuda trt-rtx] [--model-root <checkout>/skellytracker/core/model_zoo/detectors]

The sample of the proposal: 12 frames spread over each of the 3 camera videos of the freemocap test
recording (`synchronized_videos` of the package test data cache), and one photo of the package test
images, all 720x1280 (W x H). Each frame is also upscaled with `INTER_CUBIC` to 1080x1920. Each size
is encoded at JPEG quality 90 with 4:2:2 and with 4:2:0 chroma.

The models are yolox-person (letterbox) and rtmw-wholebody133 (affine_crop), size m, fp32, b3.
A config `<compute_dtype>:<interpolation>` overrides `input.resize` of both sidecars in memory.
The three paths of each frame:

    ref  cv2.imdecode -> package CPU preprocess -> model session -> package decode
    dec  nvJPEG pixels copied to the host -> package CPU preprocess -> same session -> package decode
    gpu  nvJPEG in VRAM -> preprocess graph -> same session (IO binding) -> package decode

decode only = dec - ref; graph only = gpu - dec (the same decoded pixels); end to end = gpu - ref.
The tensor differences are in uint8 steps (the 0-255 scale before the normalization). The package
decode runs on the GPU-path outputs through `Canned`, so the postprocess is the package code. The
rtmw ROIs are the boxes of the ref path, on all three paths. It writes no file.
"""

from __future__ import annotations

import argparse
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
    affine_crop_graph,
    bind_run,
    frame_inputs,
    letterbox_graph,
    load_cudart,
    model_file,
    session,
    thetas,
    versions,
    with_resize,
)

from skellytracker.core.detectors.catalog import load_detector_sidecar
from skellytracker.core.detectors.generic.keypoint_detector import GenericKeypointDetector
from skellytracker.core.detectors.generic.object_detector import GenericObjectDetector
from skellytracker.core.detectors.processing.pre import resize_affine_crop
from skellytracker.core.detectors.processing.pre.normalize import IMAGENET_STD_RGB
from skellytracker.core.detectors.processing.pre.preprocess import preprocess_image

VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}
CHROMA = {"422": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_422, "420": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_420}
STEPS = {"letterbox": 1.0, "affine_crop": np.array(IMAGENET_STD_RGB, np.float64).reshape(1, 3, 1, 1)}


def load_frames(paths: list[Path], per_video: int) -> list[np.ndarray]:
    """`per_video` frames spread over each video, and each image, of the given files and folders."""
    files = [f for p in paths for f in (sorted(p.iterdir()) if p.is_dir() else [p])]
    frames = []
    for path in files:
        if path.suffix.lower() in VIDEO_SUFFIXES:
            capture = cv2.VideoCapture(str(path))
            count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            for index in np.linspace(0, count - 1, per_video).round().astype(int):
                capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
                ok, frame = capture.read()
                if not ok:
                    raise SystemExit(f"cannot read frame {index} of {path.name}")
                frames.append(frame)
        elif path.suffix.lower() in IMAGE_SUFFIXES:
            frames.append(cv2.imread(str(path)))
    if not frames:
        raise SystemExit("no frames in --frames")
    return frames


class Steps:
    """A histogram of |d| (bin 1/1024), with the max, the mean and the share of values over 0.01 and 0.5."""

    BIN = 1 / 1024

    def __init__(self):
        self.h = np.zeros(256 * 1024 + 2, np.int64)
        self.max = self.sum = 0.0
        self.n = self.over_small = self.over_half = 0

    def add(self, d) -> None:
        d = np.abs(np.asarray(d, np.float64)).ravel()
        self.max = max(self.max, float(d.max()))
        self.sum += float(d.sum())
        self.n += d.size
        self.over_small += int((d > 0.01).sum())
        self.over_half += int((d > 0.5).sum())
        self.h += np.bincount(np.minimum((d / self.BIN).astype(np.int64), len(self.h) - 1), minlength=len(self.h))

    def merge(self, other: Steps) -> None:
        self.h += other.h
        self.max = max(self.max, other.max)
        self.sum += other.sum
        self.n += other.n
        self.over_small += other.over_small
        self.over_half += other.over_half

    def line(self) -> str:
        q = np.searchsorted(np.cumsum(self.h), 0.999 * self.n)
        return (f"max {self.max:.3f}  p99.9 <= {(q + 1) * self.BIN:.3f}  mean {self.sum / self.n:.5f}  "
                f">0.01 {self.over_small / self.n * 100:.4f}%  >0.5 {self.over_half / self.n * 100:.4f}%  of {self.n}")


def add(stats: dict, graph: str, gpu, dec, ref) -> None:
    stats[(graph, "decode")].add((dec - ref) * STEPS[graph])
    stats[(graph, "graph")].add((gpu - dec) * STEPS[graph])
    stats[(graph, "e2e")].add((gpu - ref) * STEPS[graph])


class Canned:
    """A session that gives fixed outputs: the package decode then runs on the GPU-path outputs."""

    def __init__(self, real, outputs):
        self.real, self.outputs = real, outputs

    def get_inputs(self):
        return self.real.get_inputs()

    def run(self, names, feed):
        return [self.outputs[n] for n in names]


def groups(items: list):
    """Lists of BATCH items; the last list repeats its last item. Yields (list, real count)."""
    for start in range(0, len(items), BATCH):
        part = list(items[start:start + BATCH])
        yield part + [part[-1]] * (BATCH - len(part)), len(part)


def match(ref_boxes, got_boxes, threshold=0.5):
    """Greedy IoU match: the pairs (i_ref, j_got) and the counts of unmatched boxes."""
    if len(ref_boxes) == 0 or len(got_boxes) == 0:
        return [], len(ref_boxes), len(got_boxes)
    a, b = np.asarray(ref_boxes)[:, None, :], np.asarray(got_boxes)[None, :, :]
    w = np.clip(np.minimum(a[..., 2], b[..., 2]) - np.maximum(a[..., 0], b[..., 0]), 0, None)
    h = np.clip(np.minimum(a[..., 3], b[..., 3]) - np.maximum(a[..., 1], b[..., 1]), 0, None)
    area = lambda x: (x[..., 2] - x[..., 0]) * (x[..., 3] - x[..., 1])  # noqa: E731
    iou = w * h / (area(a) + area(b) - w * h)
    pairs = []
    while iou.size and iou.max() > threshold:
        i, j = np.unravel_index(iou.argmax(), iou.shape)
        pairs.append((int(i), int(j)))
        iou[i, :] = iou[:, j] = -1
    return pairs, len(ref_boxes) - len(pairs), len(got_boxes) - len(pairs)


def box_line(ref_dets, got_dets) -> str:
    corner, score, ref_only, other_only = [], [], 0, 0
    for ref, got in zip(ref_dets, got_dets, strict=True):
        pairs, r, g = match(ref.boxes, got.boxes)
        ref_only, other_only = ref_only + r, other_only + g
        corner += [np.abs(ref.boxes[i] - got.boxes[j]) for i, j in pairs]
        score += [abs(ref.scores[i] - got.scores[j]) for i, j in pairs]
    c, s = (np.concatenate(corner), np.array(score)) if score else (np.zeros(1), np.zeros(1))
    return (f"matched {len(score)}, ref-only {ref_only}, other-only {other_only} | box corner |d| px: max {c.max():.3f}  "
            f"p99 {np.quantile(c, 0.99):.3f}  mean {c.mean():.4f} | score |d|: max {s.max():.5f}  mean {s.mean():.6f}")


def keypoint_lines(ref, got) -> list[str]:
    """ref and got: (keypoints (P, K, 2), scores (P, K)) of the same ROIs."""
    d = np.linalg.norm(ref[0] - got[0], axis=-1).ravel()
    s = ref[1].ravel()
    lines = [f"persons {len(ref[0])}, NaN mismatches {int((np.isnan(ref[0][..., 0]) != np.isnan(got[0][..., 0])).sum())}"]
    for name, mask in (("all", np.ones_like(s, bool)), ("score>0.3", s > 0.3), ("score>0.5", s > 0.5)):
        x = d[mask & ~np.isnan(d)]
        lines.append(f"{name:9s} n {x.size:6d}: dist px max {x.max():.3f}  p99 {np.quantile(x, 0.99):.3f}  "
                     f"mean {x.mean():.4f}  >1px {int((x > 1).sum())}  >3px {int((x > 3).sum())}")
    return lines


def measure(ep, config, yolox, rtmw, models, frames, sizes, decoder) -> None:
    compute_dtype, interpolation = config.split(":")
    yolox = with_resize(yolox, compute_dtype=compute_dtype, interpolation=interpolation)
    rtmw = with_resize(rtmw, compute_dtype=compute_dtype, interpolation=interpolation)
    y_model, r_model = models
    detector = GenericObjectDetector(yolox, SIZE, PRECISION, y_model)
    keypointer = GenericKeypointDetector(rtmw, SIZE, PRECISION, r_model)
    y_in, y_names = y_model.get_inputs()[0].name, [o.name for o in y_model.get_outputs()]
    r_in, r_names = r_model.get_inputs()[0].name, [o.name for o in r_model.get_outputs()]
    print(f"\n=== {ep} {config} ===", flush=True)
    tensors, results, redecode_diff = {}, [], 0
    for w, h in sizes:
        pre = {"letterbox": session(letterbox_graph(yolox, w, h), ep, f"letterbox {w}x{h}"),
               "affine_crop": session(affine_crop_graph(rtmw, w, h), ep, f"affine_crop {w}x{h}")}
        sized = [f if f.shape[:2] == (h, w) else cv2.resize(f, (w, h), interpolation=cv2.INTER_CUBIC) for f in frames]
        for chroma, flag in CHROMA.items():
            variant = f"{w}x{h} {chroma}"
            jpegs = [cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 90, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, flag])[1].tobytes()
                     for f in sized]
            ref_pix = [cv2.imdecode(np.frombuffer(j, np.uint8), cv2.IMREAD_COLOR) for j in jpegs]
            nv_pix = [decoder.host_bgr(j) for j in jpegs]
            stats = {(g, c): Steps() for g in STEPS for c in ("decode", "graph", "e2e")}

            # yolox: letterbox graph, BATCH frames for each call
            gpu_det = []
            for idx, count in groups(list(range(len(jpegs)))):
                (tensor,) = bind_run(pre["letterbox"], frame_inputs(decoder.decode([jpegs[i] for i in idx])))
                outs = {n: v.numpy() for n, v in zip(y_names, bind_run(y_model, {y_in: tensor}), strict=True)}
                ref = np.stack([preprocess_image(ref_pix[i], yolox, SIZE, PRECISION)[0] for i in idx[:count]])
                dec = np.stack([preprocess_image(nv_pix[i], yolox, SIZE, PRECISION)[0] for i in idx[:count]])
                add(stats, "letterbox", tensor.numpy()[:count], dec, ref)
                canned = GenericObjectDetector(yolox, SIZE, PRECISION, Canned(y_model, outs))
                gpu_det += canned.detect([ref_pix[i] for i in idx])[:count]
            ref_det, dec_det = detector.detect(ref_pix), detector.detect(nv_pix)

            # rtmw: affine_crop graph on the ROIs of the ref-path boxes
            crops = [(i, resize_affine_crop.roi_from_box(box.tolist())) for i in range(len(jpegs)) for box in ref_det[i].boxes]
            gpu_kp, gpu_s = [], []
            for part, count in groups(crops):
                images = decoder.decode([jpegs[i] for i, _ in part])
                redecode_diff += sum(int(np.any(np.asarray(images[k].cpu())[..., ::-1] != nv_pix[part[k][0]])) for k in range(count))
                inputs = frame_inputs(images) | {"theta": thetas(rtmw, [roi for _, roi in part], w, h)}
                (tensor,) = bind_run(pre["affine_crop"], inputs)
                outs = {n: v.numpy() for n, v in zip(r_names, bind_run(r_model, {r_in: tensor}), strict=True)}
                ref = np.stack([preprocess_image(ref_pix[i], rtmw, SIZE, PRECISION, roi)[0] for i, roi in part[:count]])
                dec = np.stack([preprocess_image(nv_pix[i], rtmw, SIZE, PRECISION, roi)[0] for i, roi in part[:count]])
                add(stats, "affine_crop", tensor.numpy()[:count], dec, ref)
                found = GenericKeypointDetector(rtmw, SIZE, PRECISION, Canned(r_model, outs)).detect(
                    [ref_pix[i] for i, _ in part], [roi for _, roi in part])
                gpu_kp.append(found.keypoints[:count])
                gpu_s.append(found.scores[:count])
            rois = [roi for _, roi in crops]
            ref_k, dec_k = (keypointer.detect([pix[i] for i, _ in crops], rois) for pix in (ref_pix, nv_pix))
            kp = {"ref": (ref_k.keypoints, ref_k.scores), "dec": (dec_k.keypoints, dec_k.scores),
                  "gpu": (np.concatenate(gpu_kp), np.concatenate(gpu_s))}
            tensors[variant] = stats
            results.append((variant, {"ref": ref_det, "dec": dec_det, "gpu": gpu_det}, kp))
    print(f"  nvJPEG re-decode differs from the first decode: {redecode_diff} crops")
    for graph in STEPS:
        print(f"[{ep} {config}] {graph} input tensor |d| in uint8 steps")
        for comp in ("decode", "graph", "e2e"):
            total = Steps()
            for variant, stats in tensors.items():
                total.merge(stats[(graph, comp)])
                print(f"    {comp:6s} {variant:14s} {stats[(graph, comp)].line()}")
            print(f"    {comp:6s} {'ALL':14s} {total.line()}")
    comparisons = (("decode", "ref", "dec"), ("graph", "dec", "gpu"), ("e2e", "ref", "gpu"))
    print(f"[{ep} {config}] yolox final detections (after the package filter, min_score {yolox.object.decode.min_score})")
    for comp, a, b in comparisons:
        for variant, boxes, _ in results:
            print(f"    {comp:6s} {variant:14s} {box_line(boxes[a], boxes[b])}")
        every = [(x, y) for _, boxes, _ in results for x, y in zip(boxes[a], boxes[b], strict=True)]
        print(f"    {comp:6s} {'ALL':14s} {box_line([x for x, _ in every], [y for _, y in every])}")
    print(f"[{ep} {config}] rtmw keypoints, the same ROIs (the ref-path boxes)")
    for comp, a, b in comparisons:
        joined = {k: tuple(np.concatenate([kp[k][i] for _, _, kp in results]) for i in (0, 1)) for k in (a, b)}
        print(f"    {comp:6s} ALL " + "\n                ".join(keypoint_lines(joined[a], joined[b])))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    add_common_arguments(parser)
    parser.add_argument("--frames", type=Path, nargs="+", required=True, help="videos, images or folders of them")
    parser.add_argument("--per-video", type=int, default=12)
    parser.add_argument("--sizes", nargs="+", default=["720x1280", "1080x1920"], help="W x H of the encoded frames")
    parser.add_argument("--configs", nargs="+", default=["uint8:linear"], help="<compute_dtype>:<interpolation>")
    args = parser.parse_args()
    sizes = [tuple(int(v) for v in s.split("x")) for s in args.sizes]
    frames = load_frames(args.frames, args.per_video)
    print(versions())
    print(f"sample: {len(frames)} frames, sizes {args.sizes}, chroma {list(CHROMA)}, JPEG quality 90")
    yolox, rtmw = load_detector_sidecar(YOLOX, None), load_detector_sidecar(RTMW, None)
    decoder = DeviceDecoder(load_cudart(args.cudart))
    for ep in args.ep:
        models = (session(model_file(yolox, args.model_root), ep, "yolox"),
                  session(model_file(rtmw, args.model_root), ep, "rtmw"))  # model sessions first: the order that raced
        for config in args.configs:
            measure(ep, config, yolox, rtmw, models, frames, sizes, decoder)


if __name__ == "__main__":
    main()
