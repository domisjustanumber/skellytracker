# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Smallest S8-like process with no pipeline: plugin EP sessions + device OrtValues with IO binding, then exit.

usage: mini.py --ep cuda --cams 6 --res 1080 --iters 300 --exit normal|leak|osexit
  normal: every object is a local of main and is freed when main returns
  leak:   sessions, bindings and device OrtValues stay in module globals into interpreter finalization
  osexit: flush, then os._exit(0) after main
Synthetic frames only. The EP store is read; the `last_used` write is dropped (as measure.py does).
"""
import argparse
import os
import sys
import time

import numpy as np
import onnx  # noqa: F401
from onnx import TensorProto, helper

KEEP = []


def graph(h: int, w: int, cams: int) -> bytes:
    """frame_i uint8 (h,w,3) -> tensor float (cams,3,h/2,w/2): cast, scale, resize, transpose, concat (a preprocess-like graph)."""
    nodes, inits, inputs, parts = [], [], [], []
    inits.append(helper.make_tensor("scale", TensorProto.FLOAT, [], [1 / 255.0]))
    inits.append(helper.make_tensor("sizes", TensorProto.INT64, [4], [1, 3, h // 2, w // 2]))
    for i in range(cams):
        inputs.append(helper.make_tensor_value_info(f"frame_{i}", TensorProto.UINT8, [h, w, 3]))
        nodes += [helper.make_node("Cast", [f"frame_{i}"], [f"f{i}"], to=TensorProto.FLOAT),
                  helper.make_node("Mul", [f"f{i}", "scale"], [f"s{i}"]),
                  helper.make_node("Transpose", [f"s{i}"], [f"t{i}"], perm=[2, 0, 1]),
                  helper.make_node("Unsqueeze", [f"t{i}", "axes0"], [f"u{i}"]),
                  helper.make_node("Resize", [f"u{i}", "", "", "sizes"], [f"r{i}"], mode="linear")]
        parts.append(f"r{i}")
    inits.append(helper.make_tensor("axes0", TensorProto.INT64, [1], [0]))
    nodes.append(helper.make_node("Concat", parts, ["tensor"], axis=0))
    out = helper.make_tensor_value_info("tensor", TensorProto.FLOAT, [cams, 3, h // 2, w // 2])
    model = helper.make_model(helper.make_graph(nodes, "pre", inputs, [out], inits), opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9
    return model.SerializeToString()


def model_graph(h: int, w: int, cams: int) -> bytes:
    """tensor -> a conv + a reduce: a stand-in for the model session that reads the device tensor."""
    inp = helper.make_tensor_value_info("tensor", TensorProto.FLOAT, [cams, 3, h // 2, w // 2])
    wt = helper.make_tensor("w", TensorProto.FLOAT, [16, 3, 3, 3], np.random.default_rng(0).standard_normal(432).astype(np.float32).tolist())
    nodes = [helper.make_node("Conv", ["tensor", "w"], ["c"], strides=[2, 2]),
             helper.make_node("ReduceMean", ["c"], ["out"], keepdims=0)]
    out = helper.make_tensor_value_info("out", TensorProto.FLOAT, None)
    model = helper.make_model(helper.make_graph(nodes, "m", [inp], [out], [wt]), opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9
    return model.SerializeToString()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", default="cuda")
    ap.add_argument("--cams", type=int, default=6)
    ap.add_argument("--res", default="1080", choices=["720", "1080"])
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--exit", default="normal", choices=["normal", "leak", "osexit"])
    a = ap.parse_args()
    from skellytracker.core.eps import session as eps_session, store

    real_write = store.write_json
    store.write_json = lambda path, value, *args, **kw: None if os.path.basename(str(path)) == "verdicts.json" else real_write(path, value, *args, **kw)
    h, w = (1080, 1920) if a.res == "1080" else (720, 1280)
    pre, pre_report = eps_session.build_session(graph(h, w, a.cams), execution_provider=a.ep)
    mod, _ = eps_session.build_session(model_graph(h, w, a.cams), execution_provider=a.ep)
    dev = pre_report.ep_device_id
    kind = "cpu" if a.ep == "cpu" else "cuda"
    rng = np.random.default_rng(1)
    host = [rng.integers(0, 255, (h, w, 3), np.uint8) for _ in range(a.cams)]
    t = time.perf_counter()
    for _ in range(a.iters):
        frames = [eps_session.upload_frame(img, dev, kind) for img in host]
        bound = pre.io_binding()
        for i, f in enumerate(frames):
            bound.bind_ortvalue_input(f"frame_{i}", f)
        bound.bind_output("tensor", kind, int(dev or 0))
        pre.run_with_iobinding(bound)
        bound.synchronize_outputs()
        tensor = bound.get_outputs()[0]
        eps_session.run_bound(mod, "tensor", ["out"], tensor)
    print(f"mini: {a.ep} {a.cams}x{a.res} {a.iters} iters in {time.perf_counter() - t:.1f}s; providers {pre.get_providers()[0]}", flush=True)
    if a.exit == "leak":
        KEEP.extend([pre, mod, bound, frames, tensor])


if __name__ == "__main__":
    main()
    if "--exit" in sys.argv and sys.argv[sys.argv.index("--exit") + 1] == "osexit":
        sys.stdout.flush()
        os._exit(0)
