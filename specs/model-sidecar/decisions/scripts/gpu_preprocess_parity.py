"""Evidence of the proposal resize-pixel-tolerance: the GPU preprocess path against the CPU reference.

Run from a checkout with the nvImageCodec wheels (`nvidia-nvimgcodec-cu13`, `nvidia-nvjpeg`) and
the EP packs installed:

    uv run --no-sync python -B specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py \
        --frames <videos folder> <photo> [--configs fit:uint8:linear:default ...] \
        [--ep cuda trt-rtx] [--model-root <checkout>/skellytracker/core/model_zoo/detectors]

The sample of the proposal: 12 frames spread over each of the 3 camera videos of the freemocap test
recording (`synchronized_videos` of the package test data cache), and one photo of the package test
images, all 720x1280 (W x H). Each frame is also upscaled with `INTER_CUBIC` to 1080x1920. Each size
is encoded at JPEG quality 90 with 4:2:2 and with 4:2:0 chroma.

A config `<method>:<compute_dtype>:<interpolation>:<pad>` overrides `input.resize` of a landed
sidecar in memory (size m, fp32, b3). `letterbox`, `stretch` and `fit` go in front of yolox-person,
and `affine_crop` in front of rtmw-wholebody133 on the ROIs of the ref-path yolox boxes. `<pad>` is
`default` (letterbox 114, fit 114, affine_crop 0) or three values, for example `10,128,240`. The
default list is every method, compute_dtype and interpolation with the default pad, and letterbox,
fit and affine_crop with the pad `10,128,240`. The three paths of each frame:

    ref  cv2.imdecode -> package CPU resize
    dec  nvJPEG pixels copied to the host -> package CPU resize
    gpu  nvJPEG in VRAM -> preprocess graph (output `pixels`)

decode only = dec - ref; graph only = gpu - dec (the same decoded pixels); end to end = gpu - ref.
The values are the resize result before the normalization, on the 0-255 scale, with the pad and the
border. The gates G1 and G2 apply to the graph only differences, over the whole result. The script
prints one `IMAGE` line with the graph-only maximum of each image (the maximum over its crops for
affine_crop), and one `GATE` line with PASS or FAIL for each config.

The model results are only a control: the model runs on the graph output `tensor`, and the package
decode runs on its outputs through `Canned`. They compare yolox boxes (letterbox, stretch, fit) or
rtmw keypoints (affine_crop) of the gpu path with the dec path. It writes no file.
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
    bind_run,
    frame_inputs,
    load_cudart,
    model_file,
    preprocess_graph,
    session,
    thetas,
    versions,
    with_resize,
)

from skellytracker.core.detectors.catalog import load_detector_sidecar
from skellytracker.core.detectors.generic.keypoint_detector import GenericKeypointDetector
from skellytracker.core.detectors.generic.object_detector import GenericObjectDetector
from skellytracker.core.detectors.processing.pre import resize_affine_crop
from skellytracker.core.detectors.processing.pre.preprocess import resize_image

# The gates, set before the run. They cover the graph-only difference of the whole resize result.
G1_MAX_ABS_UINT8 = 1.0  # compute_dtype uint8: each value an integer from 0 to 255, and max |d| <= 1
G2_MAX_ABS_FLOAT32 = 0.05  # compute_dtype float32: each value finite, and max |d| <= 0.05 (0-255 scale, float64)
METHODS = ("letterbox", "stretch", "fit", "affine_crop")
PAD_ARRAY = "10,128,240"
DEFAULT_CONFIGS = [f"{m}:{d}:{i}:{p}" for p in ("default", PAD_ARRAY) for m in METHODS
                   for d in ("uint8", "float32") for i in ("linear", "cubic", "nearest")
                   if p == "default" or m != "stretch"]
VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}
CHROMA = {"422": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_422, "420": cv2.IMWRITE_JPEG_SAMPLING_FACTOR_420}


def load_frames(paths: list[Path], per_video: int) -> tuple[list[np.ndarray], list[str]]:
    """`per_video` frames spread over each video, and each image, of the given files and folders."""
    files = [f for p in paths for f in (sorted(p.iterdir()) if p.is_dir() else [p])]
    frames, names = [], []
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
                names.append(f"{path.stem[-4:]}#{index}")
        elif path.suffix.lower() in IMAGE_SUFFIXES:
            frames.append(cv2.imread(str(path)))
            names.append(path.stem)
    if not frames:
        raise SystemExit("no frames in --frames")
    return frames, names


def configure(config: str, yolox, rtmw):
    """The sidecar of a config, with its resize overridden in memory."""
    method, compute_dtype, interpolation, pad = config.split(":")
    if method not in METHODS:
        raise SystemExit(f"unknown method in the config {config!r}")
    pad_value = None if pad == "default" else [float(v) for v in pad.split(",")]
    common = {"compute_dtype": compute_dtype, "interpolation": interpolation}
    if method == "affine_crop":
        if pad_value is not None:
            common["crop_policy"] = rtmw.input.resize.crop_policy.model_copy(update={"pad_value": pad_value})
        return with_resize(rtmw, **common)
    if method != "letterbox":  # fit has no default pad_value: 114, as letterbox; stretch has no pad
        common |= {"pad_position": None, "rounding": None, "pad_value": None if method == "stretch" else 114}
    if pad_value is not None:
        common["pad_value"] = pad_value
    return with_resize(yolox, method=method, **common)


class Steps:
    """A histogram of |d| (bin 1/1024), with the max, the mean and the share of values over 0.01 and 0.5."""

    BIN = 1 / 1024

    def __init__(self):
        self.h = np.zeros(256 * 1024 + 2, np.int64)
        self.max = self.sum = 0.0
        self.n = self.over_small = self.over_half = 0

    def add(self, d) -> None:
        d = np.abs(np.asarray(d, np.float64)).ravel()
        self.max = max(self.max, float(np.nanmax(d)))
        self.sum += float(np.nansum(d))
        self.n += d.size
        self.over_small += int((d > 0.01).sum())
        self.over_half += int((d > 0.5).sum())
        self.h += np.bincount(np.minimum(np.nan_to_num(d / self.BIN, nan=1e9).astype(np.int64), len(self.h) - 1),
                              minlength=len(self.h))

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


def reference(image, sidecar, roi) -> np.ndarray:
    """The package CPU resize of one host frame, as float64 CHW in the channel order of the model."""
    resized, _ = resize_image(image, sidecar.input.resize, sidecar.size(SIZE).target_size, sidecar.input.color_format, roi)
    return (resized[..., ::-1] if sidecar.input.color_format == "rgb" else resized).transpose(2, 0, 1).astype(np.float64)


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


def encode(frames, w, h, flag) -> list[bytes]:
    sized = [f if f.shape[:2] == (h, w) else cv2.resize(f, (w, h), interpolation=cv2.INTER_CUBIC) for f in frames]
    return [cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 90, cv2.IMWRITE_JPEG_SAMPLING_FACTOR, flag])[1].tobytes()
            for f in sized]


def measure(ep, config, landed, models, frames, names, sizes, decoder, roi_cache) -> str:
    """Measure one config on all variants. Return its GATE line."""
    yolox, rtmw = landed
    sidecar = configure(config, yolox, rtmw)
    crops = sidecar.input.resize.method == "affine_crop"
    model = models[1] if crops else models[0]
    m_in, m_names = model.get_inputs()[0].name, [o.name for o in model.get_outputs()]
    compute_dtype = sidecar.input.resize.compute_dtype
    print(f"\n=== {ep} {config} ===", flush=True)
    stats, per_image, bad_values, cpu_nodes, control = {}, {}, 0, 0, []
    for w, h in sizes:
        pre, nodes = session(preprocess_graph(sidecar, w, h), ep, f"{config} {w}x{h}")
        cpu_nodes += nodes
        for chroma, flag in CHROMA.items():
            variant = f"{w}x{h} {chroma}"
            jpegs = encode(frames, w, h, flag)
            ref_pix = [cv2.imdecode(np.frombuffer(j, np.uint8), cv2.IMREAD_COLOR) for j in jpegs]
            nv_pix = [decoder.host_bgr(j) for j in jpegs]
            if crops and variant not in roi_cache:  # the ROIs of the ref-path boxes of the landed yolox
                found = GenericObjectDetector(yolox, SIZE, PRECISION, models[0]).detect(ref_pix)
                roi_cache[variant] = [(i, resize_affine_crop.roi_from_box(b.tolist())) for i in range(len(jpegs))
                                      for b in found[i].boxes]
            items = roi_cache[variant] if crops else [(i, None) for i in range(len(jpegs))]
            stats[variant] = {c: Steps() for c in ("decode", "graph", "e2e")}
            gpu_results = []
            for part, count in groups(items):
                inputs = frame_inputs(decoder.decode([jpegs[i] for i, _ in part]))
                if crops:
                    inputs["theta"] = thetas(sidecar, [roi for _, roi in part], w, h)
                tensor, pixels = bind_run(pre, inputs)
                gpu = pixels.numpy()[:count].astype(np.float64)
                ref = np.stack([reference(ref_pix[i], sidecar, roi) for i, roi in part[:count]])
                dec = np.stack([reference(nv_pix[i], sidecar, roi) for i, roi in part[:count]])
                for comp, d in (("decode", dec - ref), ("graph", gpu - dec), ("e2e", gpu - ref)):
                    stats[variant][comp].add(d)
                bad_values += int((~np.isfinite(gpu)).sum())
                if compute_dtype == "uint8":
                    bad_values += int(((gpu != np.round(gpu)) | (gpu < 0) | (gpu > 255)).sum())
                for k, (i, _) in enumerate(part[:count]):
                    key = (variant, names[i])
                    per_image[key] = max(per_image.get(key, 0.0), float(np.nanmax(np.abs(gpu[k] - dec[k]))))
                outs = {n: v.numpy() for n, v in zip(m_names, bind_run(model, {m_in: tensor}), strict=True)}
                if crops:
                    found = GenericKeypointDetector(sidecar, SIZE, PRECISION, Canned(model, outs)).detect(
                        [ref_pix[i] for i, _ in part], [roi for _, roi in part])
                    gpu_results.append((found.keypoints[:count], found.scores[:count]))
                else:
                    gpu_results += GenericObjectDetector(sidecar, SIZE, PRECISION, Canned(model, outs)).detect(
                        [ref_pix[i] for i, _ in part])[:count]
            if crops:
                dec_k = GenericKeypointDetector(sidecar, SIZE, PRECISION, model).detect(
                    [nv_pix[i] for i, _ in items], [roi for _, roi in items])
                got = tuple(np.concatenate([r[j] for r in gpu_results]) for j in (0, 1))
                control.append(((dec_k.keypoints, dec_k.scores), got))
            else:
                control.append((GenericObjectDetector(sidecar, SIZE, PRECISION, model).detect(nv_pix), gpu_results))
    for comp in ("decode", "graph", "e2e"):
        total = Steps()
        for variant, by_comp in stats.items():
            total.merge(by_comp[comp])
            if comp == "graph":
                print(f"    {comp:6s} {variant:14s} {by_comp[comp].line()}")
        print(f"    {comp:6s} {'ALL':14s} {total.line()}")
        if comp == "graph":
            graph_total = total
    if crops:
        joined = [tuple(np.concatenate([c[side][j] for c in control]) for j in (0, 1)) for side in (0, 1)]
        print("    control rtmw keypoints, graph only: " + "\n        ".join(keypoint_lines(*joined)))
    else:
        dec_all = [d for c in control for d in c[0]]
        gpu_all = [d for c in control for d in c[1]]
        print(f"    control yolox boxes, graph only: {box_line(dec_all, gpu_all)}")
    for (variant, name), value in per_image.items():
        print(f"IMAGE {ep} {config} {variant} {name} {value:.4f}")
    limit = G1_MAX_ABS_UINT8 if compute_dtype == "uint8" else G2_MAX_ABS_FLOAT32
    verdict = "PASS" if graph_total.max <= limit and bad_values == 0 else "FAIL"
    worst = max(per_image.items(), key=lambda kv: kv[1])
    nonzero = sum(v > 0 for v in per_image.values())
    return (f"GATE {ep} {config}: {verdict} ({'G1' if compute_dtype == 'uint8' else 'G2'} <= {limit}) max {graph_total.max:.4f} "
            f">0.5 {graph_total.over_half / graph_total.n * 100:.4f}% >0.01 {graph_total.over_small / graph_total.n * 100:.4f}% "
            f"bad values {bad_values}; images with max > 0: {nonzero}/{len(per_image)}; worst {worst[0][1]} {worst[0][0]} "
            f"{worst[1]:.4f}; CPU nodes {cpu_nodes}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    add_common_arguments(parser)
    parser.add_argument("--frames", type=Path, nargs="+", required=True, help="videos, images or folders of them")
    parser.add_argument("--per-video", type=int, default=12)
    parser.add_argument("--sizes", nargs="+", default=["720x1280", "1080x1920"], help="W x H of the encoded frames")
    parser.add_argument("--configs", nargs="+", default=DEFAULT_CONFIGS, help="<method>:<compute_dtype>:<interpolation>:<pad>")
    args = parser.parse_args()
    sizes = [tuple(int(v) for v in s.split("x")) for s in args.sizes]
    frames, names = load_frames(args.frames, args.per_video)
    print(versions())
    print(f"sample: {len(frames)} frames, sizes {args.sizes}, chroma {list(CHROMA)}, JPEG quality 90")
    print(f"gates: G1 uint8 integer 0-255 and max |d| <= {G1_MAX_ABS_UINT8}; G2 float32 finite and max |d| <= {G2_MAX_ABS_FLOAT32}")
    landed = load_detector_sidecar(YOLOX, None), load_detector_sidecar(RTMW, None)
    decoder = DeviceDecoder(load_cudart(args.cudart))
    for ep in args.ep:
        models = tuple(session(model_file(s, args.model_root), ep, s.model_id)[0] for s in landed)  # models first
        roi_cache: dict = {}
        gates = [measure(ep, config, landed, models, frames, names, sizes, decoder, roi_cache) for config in args.configs]
        print(f"\n[{ep}] gates")
        print("\n".join(gates), flush=True)


if __name__ == "__main__":
    main()
