"""The probe model of the EP verification is the model that this test makes."""

import numpy as np
import pytest

from skellytracker.core.eps import _probe_model


def make_probe_model() -> bytes:
    """Conv (3 to 8 channels, 3x3) and Relu on a 1x3x64x64 float input `x`, opset 17, weights of standard deviation 0.25 from seed 0."""
    onnx = pytest.importorskip("onnx")
    from onnx import TensorProto, helper, numpy_helper

    rng = np.random.default_rng(0)
    weight = numpy_helper.from_array((0.25 * rng.standard_normal((8, 3, 3, 3))).astype(np.float32), "w")
    bias = numpy_helper.from_array(rng.standard_normal(8).astype(np.float32), "b")
    graph = helper.make_graph(
        [helper.make_node("Conv", ["x", "w", "b"], ["c"], name="conv", pads=[1, 1, 1, 1]),
         helper.make_node("Relu", ["c"], ["y"], name="relu")],
        "probe", [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 3, 64, 64])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 8, 64, 64])], [weight, bias])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)], producer_name="skellytracker")
    model.ir_version = 8
    onnx.checker.check_model(model)
    return model.SerializeToString()


def test_the_probe_model_bytes_are_the_generated_model():
    assert _probe_model.model_bytes() == make_probe_model()


def test_the_probe_model_runs_on_the_cpu():
    import onnxruntime

    session = onnxruntime.InferenceSession(_probe_model.model_bytes(), providers=["CPUExecutionProvider"])
    (output,) = session.run(None, {"x": _probe_model.probe_input()})
    assert output.shape == (1, 8, 64, 64) and output.min() == 0.0 and output.max() > 0.0
