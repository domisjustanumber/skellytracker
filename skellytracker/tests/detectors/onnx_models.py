"""Tiny ONNX models for the tests of the generic detectors. `onnx.helper` makes them at run time."""
from __future__ import annotations

import numpy as np
import onnx

# Row 1 overlaps row 0 (IoU 0.62 > 0.5) and has the lower score. Row 2 is apart.
BOXES = np.array([[[2, 2, 10, 10], [3, 3, 11, 11], [20, 20, 30, 30]]], np.float32)
SCORES = np.array([[0.9, 0.8, 0.75]], np.float32)


def tiny_model(input_shape: list[int], constants: dict[str, np.ndarray], scaled: tuple[str, ...] = ()) -> bytes:
    """Return a batch-3 graph. Each output is its constant, for each batch item.

    A `scaled` output is its constant times the mean of the batch item of the input. Each output
    goes through a `Reshape` with a 1-D int64 shape `[3, 1, ...]`: the constant that step 3 of the
    conversion profile changes.
    """
    helper, proto = onnx.helper, onnx.TensorProto
    nodes = [helper.make_node("ReduceMean", ["input"], ["mean"], axes=[1, 2, 3], keepdims=1)]
    initializers = [onnx.numpy_helper.from_array(np.zeros(1, np.float32), "zero")]
    outputs = []
    for name, constant in constants.items():
        shape = np.array([3] + [1] * (constant.ndim - 1), np.int64)
        initializers += [onnx.numpy_helper.from_array(constant, f"{name}_c"), onnx.numpy_helper.from_array(shape, f"{name}_shape")]
        nodes.append(helper.make_node("Reshape", ["mean", f"{name}_shape"], [f"{name}_mean"]))
        if name in scaled:
            nodes.append(helper.make_node("Mul", [f"{name}_mean", f"{name}_c"], [name]))
        else:
            nodes.append(helper.make_node("Mul", [f"{name}_mean", "zero"], [f"{name}_zero"]))
            nodes.append(helper.make_node("Add", [f"{name}_zero", f"{name}_c"], [name]))
        outputs.append(helper.make_tensor_value_info(name, proto.FLOAT, [3, *constant.shape[1:]]))
    graph = helper.make_graph(nodes, "tiny", [helper.make_tensor_value_info("input", proto.FLOAT, input_shape)], outputs, initializers)
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)], ir_version=8)
    onnx.checker.check_model(model, full_check=True)
    return model.SerializeToString()


def object_model() -> bytes:
    return tiny_model([3, 3, 32, 32], {"boxes": BOXES, "scores": SCORES}, scaled=("scores",))


def keypoint_model() -> bytes:
    simcc_x, simcc_y = np.full((1, 3, 24), -1, np.float32), np.full((1, 3, 32), -1, np.float32)
    simcc_x[0, 0, 12], simcc_y[0, 0, 16] = 5, 3  # point a: the centre of the crop, score 3
    simcc_x[0, 1, 0], simcc_y[0, 1, 0] = 2, 4  # point b: the top-left corner of the crop, score 2
    return tiny_model([3, 3, 16, 12], {"simcc_x": simcc_x, "simcc_y": simcc_y})  # point c: score -1, missing
