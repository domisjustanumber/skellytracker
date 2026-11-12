"""Tiny opset-17 models: Relu only, MatMul fp32, MatMul fp16 (fp32 I/O via Cast). Usage: python -I -B make_tiny.py OUT"""
import sys
from pathlib import Path
import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
X = helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 133, 256])
Y = helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 133, "n"])
rng = np.random.default_rng(7)
W = rng.standard_normal((256, 512)).astype(np.float32) * 0.05
def save(name, nodes, inits):
    g = helper.make_graph(nodes, name, [X], [Y], inits)
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 17)])
    m.ir_version = 8
    onnx.checker.check_model(m)
    onnx.save(m, str(out / f"{name}.onnx"))
save("relu", [helper.make_node("Relu", ["input"], ["y"])], [])
save("matmul32", [helper.make_node("MatMul", ["input", "W"], ["y"])], [numpy_helper.from_array(W, "W")])
save("matmul16", [helper.make_node("Cast", ["input"], ["x16"], to=TensorProto.FLOAT16),
                  helper.make_node("MatMul", ["x16", "W"], ["y16"]),
                  helper.make_node("Cast", ["y16"], ["y"], to=TensorProto.FLOAT)],
     [numpy_helper.from_array(W.astype(np.float16), "W")])
np.save(out / "tiny_in.npy", rng.standard_normal((1, 133, 256)).astype(np.float32))
print(sorted(p.name for p in out.iterdir()))
