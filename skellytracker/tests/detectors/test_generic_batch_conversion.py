"""The batch conversion of the profile `static-batch-v1`, on a tiny ONNX model."""
from __future__ import annotations

from pathlib import Path

import pytest

import onnx

from skellytracker.core.detectors.generic.batch_conversion import model_batch_convert  # noqa: E402
from skellytracker.tests.detectors.onnx_models import object_model  # noqa: E402


def test_the_batch_conversion_changes_the_batch_and_refuses_a_request_that_the_profile_does_not_allow(tmp_path: Path) -> None:
    source = tmp_path / "b3.onnx"
    source.write_bytes(object_model())
    converted = onnx.load_from_string(model_batch_convert(source, source_batch=3, target_batch=4))
    assert converted.graph.input[0].type.tensor_type.shape.dim[0].dim_value == 4
    assert converted.graph.output[0].type.tensor_type.shape.dim[0].dim_value == 4
    shapes = {item.name: onnx.numpy_helper.to_array(item).tolist() for item in converted.graph.initializer if item.name.endswith("_shape")}
    assert shapes == {"boxes_shape": [4, 1, 1], "scores_shape": [4, 1]}
    with pytest.raises(ValueError, match="no static dim 0 equal to 2"):
        model_batch_convert(source, source_batch=2, target_batch=1)
    with pytest.raises(ValueError, match="1 or larger"):
        model_batch_convert(source, source_batch=3, target_batch=0)
    with pytest.raises(ValueError, match="unsupported batch_conversion.profile_id"):
        model_batch_convert(source, source_batch=3, target_batch=1, profile_id="static-batch-v9")
    external = tmp_path / "external.onnx"
    onnx.save(onnx.load(source), external, save_as_external_data=True, location="external.bin", size_threshold=0)
    with pytest.raises(ValueError, match="external data"):
        model_batch_convert(external, source_batch=3, target_batch=1)
