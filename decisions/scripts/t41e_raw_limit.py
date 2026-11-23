"""Raw output of this package against a plain ONNX Runtime CPU session on the same ONNX file (entry T41E).

This script made the evidence of entry T41E. It reads the worker files of the exporter as data and runs no exporter code.

E      = plain session (default options), upstream tensors: the stand-in for the exporter's ONNX run.
P_up   = package session, upstream tensors: session difference only.
P_own  = package session, package preprocess from the decoded images: what the raw check will see.
E_off  = plain session, no graph optimization, 1 thread: a proxy for another CPU kernel order.

usage: uv run python -B decisions/scripts/t41e_raw_limit.py yolox|rtmw <parity folder> [size ...]
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort

from skellytracker.core.detectors import get_detector, load_detector_sidecar
from skellytracker.core.detectors.generic import create_detector
from skellytracker.core.detectors.generic.inference import run_batches
from skellytracker.core.detectors.generic.session import ensure_artifact
from skellytracker.core.detectors.processing.pre.preprocess import BatchPreprocessor
from skellytracker.core.detectors.processing.pre.resize_affine_crop import roi_from_box

spec = importlib.util.spec_from_file_location("gate", "decisions/scripts/gpw6_first_models_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

which, parity = sys.argv[1], Path(sys.argv[2])
key = gate.YOLOX if which == "yolox" else gate.RTMW
sidecar = load_detector_sidecar(key)
names = [output.name for output in sidecar.outputs]
images = gate.load_worker(parity, key, "decoded.npz")


def plain(path, optimize=True):
    options = ort.SessionOptions()
    if not optimize:
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
        options.intra_op_num_threads = 1
    return ort.InferenceSession(str(path), sess_options=options, providers=["CPUExecutionProvider"])


def run_plain(session, tensors):
    batch = session.get_inputs()[0].shape[0]
    batch = batch if isinstance(batch, int) and batch > 0 else len(tensors)
    parts = [[] for _ in names]
    for start in range(0, len(tensors), batch):
        group = np.stack(tensors[start:start + batch])
        count = len(group)
        if count < batch:
            group = np.concatenate([group, np.zeros((batch - count, *group.shape[1:]), group.dtype)])
        for part, output in zip(parts, session.run(names, {sidecar.input.name: group}), strict=True):
            part.append(output[:count].astype(np.float32))
    return {name: np.concatenate(part) for name, part in zip(names, parts, strict=True)}


def diff(a, b):
    return {name: float(np.abs(a[name].astype(np.float64) - b[name]).max()) for name in names}


for size in sys.argv[3:] or list(sidecar.sizes):
    up = gate.load_worker(parity, key, f"upstream_{size}.npz")
    if which == "yolox":
        items = list(images)
        frames, rois = [images[item] for item in items], None
        up_float = [up[f"{item}__canvas"].transpose(2, 0, 1) for item in items]
    else:
        items = [name[: -len("__matrix")] for name in up if name.endswith("__matrix") and not name.startswith("crafted")]
        frames = [images[max((image for image in images if item.startswith(image + "_")), key=len)] for item in items]
        rois = [roi_from_box(up[f"{item}__box"].tolist()) for item in items]
        up_float = [up[f"{item}__tensor"] for item in items]
    for precision in ("fp32", "fp16"):
        dtype = sidecar.input.dtype[precision]
        up_tensors = [np.ascontiguousarray(tensor).astype(dtype) for tensor in up_float]
        own = BatchPreprocessor(sidecar, size, precision).preprocess(frames, rois)[0].copy()
        tensor_diff = np.abs(own.astype(np.float64) - np.stack(up_tensors))
        detector = create_detector(key, execution_provider="cpu", size=size, precision=precision)
        session = detector._open_session() if hasattr(detector, "_open_session") else detector.session
        path = ensure_artifact(get_detector(key), sidecar, size, precision)
        e = run_plain(plain(path), up_tensors)
        p_up = run_batches(session, sidecar, up_tensors)
        p_own = run_batches(session, sidecar, own)
        e_off = run_plain(plain(path, optimize=False), up_tensors)
        record = {
            "items": len(items), "input_dtype": dtype,
            "tensor_max_diff": float(tensor_diff.max()), "tensor_fraction_differs": float((tensor_diff > 0).mean()),
            "P_up_vs_E": diff(p_up, e), "P_own_vs_E": diff(p_own, e), "E_off_vs_E": diff(e_off, e),
        }
        if which == "yolox":
            top = np.argsort(-e["scores"], axis=1)[:, :100]

            def take(out, name, top=top):  # noqa: ANN001, ANN202
                return np.take_along_axis(out[name], top if out[name].ndim == 2 else top[..., None], 1)

            record["top100_P_own_vs_E"] = {name: float(np.abs(take(p_own, name).astype(np.float64) - take(e, name)).max()) for name in names}
            record["top100_E_off_vs_E"] = {name: float(np.abs(take(e_off, name).astype(np.float64) - take(e, name)).max()) for name in names}
        else:
            for label, other in (("P_own", p_own), ("E_off", e_off)):
                moved, peak = 0, 0.0
                for name in names:
                    moved += int(np.count_nonzero(other[name].argmax(-1) != e[name].argmax(-1)))
                    peak = max(peak, float(np.abs(other[name].max(-1).astype(np.float64) - e[name].max(-1)).max()))
                record[f"peaks_{label}_vs_E"] = {"bins_moved": moved, "of": int(sum(e[name][..., 0].size for name in names)), "peak_value_max_diff": peak}
        detector.close()
        print(size, precision, json.dumps(record), flush=True)
