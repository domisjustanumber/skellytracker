from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

onnx = pytest.importorskip("onnx", reason="onnx not installed")

from onnx import TensorProto, helper, numpy_helper  # noqa: E402

from skellytracker.core.sessions.batch_conversion import model_batch_convert  # noqa: E402


def _dims(value_info) -> list[int | str]:
    return [
        dim.dim_param or dim.dim_value
        for dim in value_info.type.tensor_type.shape.dim
    ]


def _initializer(model: onnx.ModelProto, name: str) -> np.ndarray:
    for initializer in model.graph.initializer:
        if initializer.name == name:
            return numpy_helper.to_array(initializer)
    raise AssertionError(f"missing initializer {name}")


def _write_fixture(path: Path, *, batch_size: int) -> None:
    images = helper.make_tensor_value_info(
        "images", TensorProto.FLOAT, [batch_size, 2]
    )
    reshaped = helper.make_tensor_value_info(
        "reshaped", TensorProto.FLOAT, [batch_size, 2]
    )
    output = helper.make_tensor_value_info(
        "output0", TensorProto.FLOAT, [batch_size, 2]
    )
    flattened = helper.make_tensor_value_info(
        "flattened", TensorProto.INT64, [batch_size * 300, 1]
    )
    shape = numpy_helper.from_array(
        np.array([batch_size, 2], dtype=np.int64),
        name="reshape_shape",
    )
    offsets = numpy_helper.from_array(
        (np.arange(batch_size, dtype=np.int64) * 300).reshape(batch_size, 1),
        name="batch_offsets",
    )
    one = numpy_helper.from_array(np.array(1.0, dtype=np.float32), name="one")
    graph = helper.make_graph(
        [
            helper.make_node("Reshape", ["images", "reshape_shape"], ["reshaped"]),
            helper.make_node("Add", ["reshaped", "one"], ["output0"]),
        ],
        "static-batch-fixture",
        [images],
        [output],
        [shape, offsets, one],
        value_info=[reshaped, flattened],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 20)])
    batch_prop = model.metadata_props.add()
    batch_prop.key = "batch"
    batch_prop.value = str(batch_size)
    args_prop = model.metadata_props.add()
    args_prop.key = "args"
    args_prop.value = repr({"batch": batch_size, "dynamic": False})
    onnx.checker.check_model(model)
    onnx.save(model, path)


def _fixture_batch_conversion(batch_size: int) -> dict:
    return {
        "profile_id": "test-det-static-batch",
        "source_batch_size": batch_size,
        "target_batch": {"minimum": 1, "axis": 0},
        "rewrite_rules": [
            "metadata_batch",
            "leading_value_info_batch",
            "int64_shape_first_dim",
            "batch_offset_initializer",
        ],
        "tensor_matchers": {
            "int64_shape_first_dim": {
                "dtype": "int64",
                "rank": 1,
                "minimum_size": 2,
                "first_value": "source_batch",
                "rewrite_first_value_to": "target_batch",
            },
            "batch_offset_initializer": {
                "dtype": "int64",
                "shape": ["source_batch", 1],
                "start": 0,
                "stride": 300,
                "rewrite_shape": ["target_batch", 1],
            },
        },
        "target_batch_one": {
            "remove_batch_offset_add": True,
            "offset_initializer_name": "batch_offsets",
            "rewire_producer_output": True,
            "rewire_consumers": True,
        },
        "validation": {
            "input_shape": ["target_batch", 2],
            "output_shapes": [["target_batch", 2]],
        },
    }


def test_batch_convert_updates_metadata_and_batch_tensors(tmp_path: Path) -> None:
    src = tmp_path / "b2.onnx"
    dst = tmp_path / "b4.onnx"
    _write_fixture(src, batch_size=2)

    summary = model_batch_convert(
        src,
        dst,
        target_batch=4,
        batch_conversion=_fixture_batch_conversion(batch_size=2),
    )

    assert summary.source_batch == 2
    assert summary.target_batch == 4
    assert summary.profile_id == "test-det-static-batch"
    assert summary.value_info_dims_updated == [
        "images",
        "reshaped",
        "flattened",
        "output0",
    ]
    assert summary.initializer_tensors_updated == ["reshape_shape", "batch_offsets"]
    assert summary.metadata_props_updated == ["batch", "args"]

    model = onnx.load(dst)
    assert _dims(model.graph.input[0]) == [4, 2]
    assert _dims(model.graph.value_info[0]) == [4, 2]
    assert _dims(model.graph.value_info[1]) == [1200, 1]
    assert _dims(model.graph.output[0]) == [4, 2]
    assert [(prop.key, prop.value) for prop in model.metadata_props] == [
        ("batch", "4"),
        ("args", "{'batch': 4, 'dynamic': False}"),
    ]
    np.testing.assert_array_equal(
        _initializer(model, "reshape_shape"),
        np.array([4, 2], dtype=np.int64),
    )
    np.testing.assert_array_equal(
        _initializer(model, "batch_offsets"),
        np.array([[0], [300], [600], [900]], dtype=np.int64),
    )


def test_batch_convert_can_target_batch_one(tmp_path: Path) -> None:
    src = tmp_path / "b2.onnx"
    dst = tmp_path / "b1.onnx"
    _write_fixture(src, batch_size=2)

    summary = model_batch_convert(
        src,
        dst,
        target_batch=1,
        batch_conversion=_fixture_batch_conversion(batch_size=2),
    )

    assert summary.source_batch == 2
    assert summary.target_batch == 1
    model = onnx.load(dst)
    assert _dims(model.graph.input[0]) == [1, 2]
    assert _dims(model.graph.value_info[1]) == [300, 1]
    np.testing.assert_array_equal(
        _initializer(model, "batch_offsets"),
        np.array([[0]], dtype=np.int64),
    )
