from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

onnx = pytest.importorskip("onnx", reason="onnx not installed")

from onnx import TensorProto, helper, numpy_helper  # noqa: E402

from skellytracker.core.sessions.batch_conversion import model_batch_convert  # noqa: E402

PROFILE = {"profile_id": "static-batch-v1", "source_batch_size": 2}


def _dims(value_info) -> list[int | str]:
    return [dim.dim_param or dim.dim_value for dim in value_info.type.tensor_type.shape.dim]


def _initializer(model: onnx.ModelProto, name: str) -> np.ndarray:
    for initializer in model.graph.initializer:
        if initializer.name == name:
            return numpy_helper.to_array(initializer)
    raise AssertionError(f"missing initializer {name}")


def _save(path: Path, nodes, inputs, outputs, initializers=(), value_info=()) -> Path:
    graph = helper.make_graph(nodes, "fixture", inputs, outputs, list(initializers), value_info=list(value_info))
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 20)])
    onnx.checker.check_model(model, full_check=True)
    onnx.save(model, path)
    return path


def _reshape_model(path: Path, *, list_initializer_as_input: bool = False) -> Path:
    """x[2, 3] -> Reshape([2, 3]) -> y[2, 3], with Ultralytics-style batch metadata."""
    shape = numpy_helper.from_array(np.array([2, 3], dtype=np.int64), name="shape")
    inputs = [helper.make_tensor_value_info("x", TensorProto.FLOAT, [2, 3])]
    if list_initializer_as_input:
        inputs.append(helper.make_tensor_value_info("shape", TensorProto.INT64, [2]))
    graph = helper.make_graph(
        [helper.make_node("Reshape", ["x", "shape"], ["y"])],
        "fixture",
        inputs,
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [2, 3])],
        [shape],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 20)])
    helper.set_model_props(model, {"batch": "2", "args": repr({"batch": 2, "dynamic": False})})
    onnx.save(model, path)
    return path


@pytest.mark.parametrize("target", [1, 3])
def test_converts_dims_shape_constants_and_metadata(tmp_path: Path, target: int) -> None:
    src = _reshape_model(tmp_path / "b2.onnx")
    dst = tmp_path / f"b{target}.onnx"

    summary = model_batch_convert(src, dst, target_batch=target, batch_conversion=PROFILE)

    assert (summary.source_batch, summary.target_batch, summary.profile_id) == (2, target, "static-batch-v1")
    assert summary.value_info_dims_updated == ["x", "y"]
    assert summary.initializer_tensors_updated == ["shape"]
    assert summary.metadata_props_updated == ["batch", "args"]
    model = onnx.load(dst)
    onnx.checker.check_model(model, full_check=True)
    assert _dims(model.graph.input[0]) == [target, 3]
    assert _dims(model.graph.output[0]) == [target, 3]
    np.testing.assert_array_equal(_initializer(model, "shape"), np.array([target, 3], dtype=np.int64))
    assert {prop.key: prop.value for prop in model.metadata_props} == {
        "batch": str(target),
        "args": repr({"batch": target, "dynamic": False}),
    }


def test_reads_the_profile_from_a_sidecar(tmp_path: Path) -> None:
    src = _reshape_model(tmp_path / "b2.onnx")

    summary = model_batch_convert(
        src, tmp_path / "b1.onnx", target_batch=1, sidecar={"batching": {"batch_axis": 0, "batch_conversion": PROFILE}}
    )

    assert summary.target_batch == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"sidecar": {}},
        {"sidecar": {"batching": None}},
        {"sidecar": {"batching": {"batch_conversion": None}}},
        {"batch_conversion": {"profile_id": "yolo26-object_detector-static-batch", "source_batch_size": 2}},
        {"batch_conversion": {"source_batch_size": 2}},
        {"batch_conversion": {"profile_id": "static-batch-v1", "source_batch_size": 3}},
        {"batch_conversion": PROFILE, "target_batch": 0},
    ],
)
def test_rejects_a_bad_request(tmp_path: Path, kwargs: dict) -> None:
    src = _reshape_model(tmp_path / "b2.onnx")
    kwargs = {"target_batch": 1, **kwargs}

    with pytest.raises(ValueError):
        model_batch_convert(src, tmp_path / "out.onnx", **kwargs)


@pytest.mark.parametrize("input_shape", [["N", 3], []])
def test_rejects_an_input_with_no_static_batch(tmp_path: Path, input_shape: list) -> None:
    src = _save(
        tmp_path / "b2.onnx",
        [helper.make_node("Identity", ["x"], ["y"])],
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, input_shape)],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, input_shape)],
    )

    with pytest.raises(ValueError, match="no static batch"):
        model_batch_convert(src, tmp_path / "out.onnx", target_batch=1, batch_conversion=PROFILE)


def test_rejects_external_data(tmp_path: Path) -> None:
    weight = numpy_helper.from_array(np.ones((2, 3), dtype=np.float32), name="w")
    graph = helper.make_graph(
        [helper.make_node("Add", ["x", "w"], ["y"])],
        "fixture",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [2, 3])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [2, 3])],
        [weight],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 20)])
    src = tmp_path / "b2.onnx"
    onnx.save(model, src, save_as_external_data=True, location="b2.bin", size_threshold=0)

    with pytest.raises(ValueError, match="external data"):
        model_batch_convert(src, tmp_path / "out.onnx", target_batch=1, batch_conversion=PROFILE)


def test_rejects_external_data_in_a_constant_node(tmp_path: Path) -> None:
    weight = numpy_helper.from_array(np.ones((1, 3), dtype=np.float32), name="w")
    graph = helper.make_graph(
        [helper.make_node("Constant", [], ["w"], value=weight), helper.make_node("Add", ["x", "w"], ["y"])],
        "fixture",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [2, 3])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [2, 3])],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 20)])
    src = tmp_path / "b2.onnx"
    onnx.save(model, src, save_as_external_data=True, location="b2.bin", size_threshold=0, convert_attribute=True)

    with pytest.raises(ValueError, match="external data"):
        model_batch_convert(src, tmp_path / "out.onnx", target_batch=1, batch_conversion=PROFILE)


def test_converts_value_info_and_constant_shape_tensors(tmp_path: Path) -> None:
    shape = numpy_helper.from_array(np.array([2, 3], dtype=np.int64), name="shape")
    src = _save(
        tmp_path / "b2.onnx",
        [
            helper.make_node("Constant", [], ["shape"], value=shape),
            helper.make_node("Reshape", ["x", "shape"], ["r"]),
            helper.make_node("Identity", ["r"], ["y"]),
        ],
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [2, 3])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [2, 3])],
        value_info=[helper.make_tensor_value_info("r", TensorProto.FLOAT, [2, 3])],
    )

    summary = model_batch_convert(src, tmp_path / "b3.onnx", target_batch=3, batch_conversion=PROFILE)

    assert summary.value_info_dims_updated == ["x", "r", "y"]
    assert summary.constant_tensors_updated == ["shape"]
    model = onnx.load(tmp_path / "b3.onnx")
    assert _dims(model.graph.value_info[0]) == [3, 3]
    np.testing.assert_array_equal(numpy_helper.to_array(model.graph.node[0].attribute[0].t), [3, 3])


def test_skips_args_metadata_that_does_not_parse(tmp_path: Path) -> None:
    src = _reshape_model(tmp_path / "b2.onnx")
    model = onnx.load(src)
    helper.set_model_props(model, {"batch": "2", "args": "{[1]: 2}"})
    onnx.save(model, src)

    summary = model_batch_convert(src, tmp_path / "b1.onnx", target_batch=1, batch_conversion=PROFILE)

    assert summary.metadata_props_updated == ["batch"]


def test_converts_two_inputs_of_the_same_batch(tmp_path: Path) -> None:
    src = _save(
        tmp_path / "b2.onnx",
        [helper.make_node("Add", ["a", "b"], ["y"])],
        [
            helper.make_tensor_value_info("a", TensorProto.FLOAT, [2, 3]),
            helper.make_tensor_value_info("b", TensorProto.FLOAT, [2, 3]),
        ],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [2, 3])],
    )

    model_batch_convert(src, tmp_path / "b3.onnx", target_batch=3, batch_conversion=PROFILE)

    model = onnx.load(tmp_path / "b3.onnx")
    assert [_dims(value_info) for value_info in model.graph.input] == [[3, 3], [3, 3]]


def test_skips_an_initializer_listed_as_a_graph_input(tmp_path: Path) -> None:
    src = _reshape_model(tmp_path / "b2.onnx", list_initializer_as_input=True)

    summary = model_batch_convert(src, tmp_path / "b3.onnx", target_batch=3, batch_conversion=PROFILE)

    assert summary.value_info_dims_updated == ["x", "y"]
    model = onnx.load(tmp_path / "b3.onnx")
    assert _dims(model.graph.input[1]) == [2]


def test_rejects_a_changed_dim_that_is_not_the_batch(tmp_path: Path) -> None:
    # Dim 0 of t is 2 but holds dim 1 of x. Step 2 changes it, and strict inference rejects the graph.
    src = _save(
        tmp_path / "b2.onnx",
        [helper.make_node("Transpose", ["x"], ["t"], perm=[1, 0, 2]), helper.make_node("Identity", ["t"], ["y"])],
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [2, 2, 5])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [2, 2, 5])],
        value_info=[helper.make_tensor_value_info("t", TensorProto.FLOAT, [2, 2, 5])],
    )

    with pytest.raises(ValueError, match="strict shape check"):
        model_batch_convert(src, tmp_path / "b1.onnx", target_batch=1, batch_conversion=PROFILE)
