"""Make the shared inputs of the EP device checks. It runs in the ``prep`` environment.

Usage: ``python -I -B prep_assets.py JOB.json``. ``run_checks.py`` writes the job and runs this file.

For each model of the job it writes, in the job folder:

- ``<key>.input.npy``: one input tensor, made from the pinned test image;
- ``<key>.ref.npz``: the outputs of the fp32 model on the CPU EP (the reference of each route);
- ``<key>.fp16.onnx``: an fp16 copy (``onnxconverter-common``, ``keep_io_types=True``), if the job
  asks for fp16.

It also writes ``probe.onnx`` (Conv 3 to 8, 3x3, and Relu; 1x3x64x64; opset 17) and ``probe.input.npy``.
The result goes to ``prep_result.json``. This is not an accuracy test: the preprocessing is simple.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from importlib.metadata import version
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
from onnx import TensorProto, helper
from PIL import Image

MEAN = np.array([123.675, 116.28, 103.53], np.float32)
STD = np.array([58.395, 57.12, 57.375], np.float32)
# The person box in the pinned test image (pixels; x0, y0, x1, y1).
PERSON_BOX = (60, 40, 560, 860)


def make_probe(folder: Path) -> None:
    rng = np.random.default_rng(0)
    weight = helper.make_tensor("w", TensorProto.FLOAT, [8, 3, 3, 3], rng.random(216).astype(np.float32))
    graph = helper.make_graph(
        [
            helper.make_node("Conv", ["x", "w"], ["c"], pads=[1, 1, 1, 1], name="conv"),
            helper.make_node("Relu", ["c"], ["y"], name="relu"),
        ],
        "probe",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 3, 64, 64])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 8, 64, 64])],
        [weight],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9
    onnx.checker.check_model(model)
    onnx.save(model, folder / "probe.onnx")
    np.save(folder / "probe.input.npy", np.random.default_rng(1).random((1, 3, 64, 64), dtype=np.float32))


def letterbox(image: Image.Image, size: int) -> np.ndarray:
    """Detector input: BGR, 0 to 255, scaled to fit, padded with 114. NCHW float32."""
    scale = size / max(image.size)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.BILINEAR)
    canvas = np.full((size, size, 3), 114, np.float32)
    canvas[: resized.height, : resized.width] = np.asarray(resized, np.float32)
    return canvas[..., ::-1].transpose(2, 0, 1)[None].copy()


def person_crop(image: Image.Image, height: int, width: int) -> np.ndarray:
    """Top-down pose input: the person box at the model aspect, RGB, mean/std normalized. NCHW."""
    x0, y0, x1, y1 = PERSON_BOX
    cx, cy, box_h = (x0 + x1) / 2, (y0 + y1) / 2, y1 - y0
    box_w = max(x1 - x0, box_h * width / height)
    box_h = box_w * height / width
    box = (cx - box_w / 2, cy - box_h / 2, cx + box_w / 2, cy + box_h / 2)
    crop = image.crop(tuple(round(v) for v in box)).resize((width, height), Image.BILINEAR)
    return ((np.asarray(crop, np.float32) - MEAN) / STD).transpose(2, 0, 1)[None].copy()


def to_fp16(src: Path, dst: Path) -> None:
    from onnxconverter_common import float16

    model = float16.convert_float_to_float16(onnx.load(str(src)), keep_io_types=True)
    onnx.checker.check_model(model, full_check=True)  # strict type inference finds a bad Cast boundary
    onnx.save(model, str(dst))


def prepare_model(folder: Path, image: Image.Image, spec: dict, want_fp16: bool) -> dict:
    key, src = spec["key"], Path(spec["onnx"])
    rec: dict = {}
    if spec["kind"] == "detector":
        x = letterbox(image, spec["size"][0])
    else:
        x = person_crop(image, *spec["size"])
    np.save(folder / f"{key}.input.npy", x)
    session = ort.InferenceSession(str(src), providers=["CPUExecutionProvider"])
    name = session.get_inputs()[0].name
    start = time.perf_counter()
    outputs = session.run(None, {name: x})
    rec["cpu_ref_ms"] = round(1000 * (time.perf_counter() - start), 1)
    names = [o.name for o in session.get_outputs()]
    np.savez(folder / f"{key}.ref.npz", **{f"out{i}": o for i, o in enumerate(outputs)})
    rec["input_shape"] = list(x.shape)
    rec["outputs"] = {n: list(o.shape) for n, o in zip(names, outputs, strict=True)}
    del session
    if want_fp16:
        try:
            to_fp16(src, folder / f"{key}.fp16.onnx")
            rec["fp16"] = "made"
        except Exception as exc:  # noqa: BLE001 - a failed conversion is a recorded result
            (folder / f"{key}.fp16.onnx").unlink(missing_ok=True)
            rec["fp16"] = f"not made: {type(exc).__name__}: {str(exc)[:300]}"
    return rec


def main() -> int:
    job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    folder = Path(job["folder"])
    result: dict = {"versions": {p: version(p) for p in ("onnxruntime", "onnx", "onnxconverter-common", "numpy")}}
    make_probe(folder)
    image = Image.open(job["image"]).convert("RGB") if job["models"] else None
    result["models"] = {}
    for spec in job["models"]:
        try:
            result["models"][spec["key"]] = prepare_model(folder, image, spec, job["fp16"])
        except Exception as exc:  # noqa: BLE001 - recorded per model
            result["models"][spec["key"]] = {"error": f"{type(exc).__name__}: {str(exc)[:300]}",
                                             "trace": traceback.format_exc(limit=3)[-600:]}
    (folder / "prep_result.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
