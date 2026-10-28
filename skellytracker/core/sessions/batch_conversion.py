"""Sidecar-guided converter for static-batch ONNX exports."""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import onnx
from onnx import TensorProto, numpy_helper


@dataclass
class StaticBatchRewriteSummary:
    """Details of the batch-specific graph fields changed by a rewrite."""

    source_batch: int
    target_batch: int
    profile_id: str
    value_info_dims_updated: list[str] = field(default_factory=list)
    initializer_tensors_updated: list[str] = field(default_factory=list)
    constant_tensors_updated: list[str] = field(default_factory=list)
    metadata_props_updated: list[str] = field(default_factory=list)
    nodes_removed: list[str] = field(default_factory=list)
    initializer_tensors_removed: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_batch": self.source_batch,
            "target_batch": self.target_batch,
            "profile_id": self.profile_id,
            "value_info_dims_updated": self.value_info_dims_updated,
            "initializer_tensors_updated": self.initializer_tensors_updated,
            "constant_tensors_updated": self.constant_tensors_updated,
            "metadata_props_updated": self.metadata_props_updated,
            "nodes_removed": self.nodes_removed,
            "initializer_tensors_removed": self.initializer_tensors_removed,
        }


def _conversion_profile(sidecar_or_profile: dict[str, Any]) -> dict[str, Any]:
    if "batching" in sidecar_or_profile:
        try:
            return sidecar_or_profile["batching"]["batch_conversion"]
        except KeyError as exc:
            raise ValueError("sidecar does not include batching.batch_conversion") from exc
    return sidecar_or_profile


def _static_batch_from_model(model: onnx.ModelProto) -> int:
    if len(model.graph.input) != 1:
        raise ValueError(f"expected 1 graph input, got {len(model.graph.input)}")
    batch_dim = model.graph.input[0].type.tensor_type.shape.dim[0]
    if not batch_dim.HasField("dim_value"):
        raise ValueError("graph input batch dimension is not static")
    batch_size = batch_dim.dim_value
    if batch_size <= 1:
        raise ValueError(f"source batch must be > 1, got {batch_size}")
    return batch_size


def _rewrite_value_info_batch_dim(
    value_info,
    *,
    source_batch: int,
    target_batch: int,
) -> bool:
    tensor_type = value_info.type.tensor_type
    if not tensor_type.HasField("shape") or not tensor_type.shape.dim:
        return False
    batch_dim = tensor_type.shape.dim[0]
    if not batch_dim.HasField("dim_value"):
        return False
    dim_value = batch_dim.dim_value
    if dim_value == source_batch:
        batch_dim.dim_value = target_batch
    elif dim_value > source_batch and dim_value % source_batch == 0:
        batch_dim.dim_value = target_batch * (dim_value // source_batch)
    else:
        return False
    return True


def _rewrite_metadata_props(
    model: onnx.ModelProto,
    *,
    source_batch: int,
    target_batch: int,
) -> list[str]:
    updated: list[str] = []
    for prop in model.metadata_props:
        if prop.key == "batch" and prop.value == str(source_batch):
            prop.value = str(target_batch)
            updated.append(prop.key)
        elif prop.key == "args":
            try:
                args = ast.literal_eval(prop.value)
            except (SyntaxError, ValueError):
                continue
            if isinstance(args, dict) and args.get("batch") == source_batch:
                args["batch"] = target_batch
                prop.value = repr(args)
                updated.append(prop.key)
    return updated


def _rewrite_batch_tensor_array(
    array: np.ndarray,
    *,
    source_batch: int,
    target_batch: int,
    profile: dict[str, Any],
) -> np.ndarray | None:
    if array.dtype != np.int64 or array.size == 0:
        return None

    tensor_matchers = profile.get("tensor_matchers", {})
    shape_matcher = tensor_matchers.get("int64_shape_first_dim", {})
    minimum_size = int(shape_matcher.get("minimum_size", 2))
    if array.ndim == 1 and array.size >= minimum_size and array[0] == source_batch:
        rewritten = array.copy()
        rewritten[0] = target_batch
        return rewritten

    offset_matcher = tensor_matchers.get("batch_offset_initializer", {})
    expected_stride = offset_matcher.get("stride")
    if array.ndim == 2 and array.shape == (source_batch, 1):
        flat = array[:, 0]
        if source_batch >= 2:
            stride = flat[1] - flat[0]
            expected = np.arange(source_batch, dtype=np.int64) * stride
            stride_matches = expected_stride is None or stride == expected_stride
            if (
                flat[0] == 0
                and stride > 0
                and stride_matches
                and np.array_equal(flat, expected)
            ):
                return (np.arange(target_batch, dtype=np.int64) * stride).reshape(
                    target_batch, 1
                )

    return None


def _producer_for_output(model: onnx.ModelProto, output_name: str):
    for node in model.graph.node:
        if output_name in node.output:
            return node
    return None


def _remove_value_info_by_name(model: onnx.ModelProto, name: str) -> None:
    kept = [value_info for value_info in model.graph.value_info if value_info.name != name]
    if len(kept) == len(model.graph.value_info):
        return
    del model.graph.value_info[:]
    model.graph.value_info.extend(kept)


def _remove_initializer_by_name(model: onnx.ModelProto, name: str) -> None:
    kept = [initializer for initializer in model.graph.initializer if initializer.name != name]
    if len(kept) == len(model.graph.initializer):
        return
    del model.graph.initializer[:]
    model.graph.initializer.extend(kept)


def _remove_batch_offset_add_for_batch_one(
    model: onnx.ModelProto,
    *,
    profile: dict[str, Any],
    summary: StaticBatchRewriteSummary,
) -> None:
    target_batch_one = profile.get("target_batch_one", {})
    if not target_batch_one.get("remove_batch_offset_add"):
        return
    offset_name = target_batch_one.get("offset_initializer_name")
    if not isinstance(offset_name, str) or not offset_name:
        raise ValueError("target_batch_one.offset_initializer_name is required")

    for idx, node in enumerate(model.graph.node):
        if node.op_type != "Add":
            continue
        if offset_name not in node.input or len(node.input) != 2 or len(node.output) != 1:
            continue

        passthrough_name = next(name for name in node.input if name != offset_name)
        producer = _producer_for_output(model, passthrough_name)
        if producer is None:
            continue

        add_output_name = node.output[0]
        if target_batch_one.get("rewire_producer_output", True):
            for output_idx, output_name in enumerate(producer.output):
                if output_name == passthrough_name:
                    producer.output[output_idx] = add_output_name
                    break
            else:
                continue
        if target_batch_one.get("rewire_consumers", True):
            for consumer in model.graph.node:
                if consumer is node:
                    continue
                for input_idx, input_name in enumerate(consumer.input):
                    if input_name == passthrough_name:
                        consumer.input[input_idx] = add_output_name

        del model.graph.node[idx]
        _remove_value_info_by_name(model, passthrough_name)
        _remove_initializer_by_name(model, offset_name)
        summary.nodes_removed.append(node.name or f"{node.op_type}:{add_output_name}")
        summary.initializer_tensors_removed.append(offset_name)
        return


def _rewrite_tensor_proto(
    tensor: onnx.TensorProto,
    *,
    source_batch: int,
    target_batch: int,
    profile: dict[str, Any],
) -> bool:
    if tensor.data_type != TensorProto.INT64:
        return False
    array = numpy_helper.to_array(tensor)
    rewritten = _rewrite_batch_tensor_array(
        array,
        source_batch=source_batch,
        target_batch=target_batch,
        profile=profile,
    )
    if rewritten is None:
        return False
    name = tensor.name
    tensor.CopyFrom(numpy_helper.from_array(rewritten, name=name))
    return True


def _dim_values(value_info) -> list[int | str]:
    return [
        dim.dim_param or dim.dim_value
        for dim in value_info.type.tensor_type.shape.dim
    ]


def _expected_shape(shape: list[Any], *, target_batch: int) -> list[Any]:
    return [target_batch if dim == "target_batch" else dim for dim in shape]


def _validate_generated_shapes(
    model: onnx.ModelProto,
    *,
    profile: dict[str, Any],
    target_batch: int,
) -> None:
    validation = profile.get("validation", {})
    expected_input = validation.get("input_shape")
    if expected_input is not None:
        actual_input = _dim_values(model.graph.input[0])
        if actual_input != _expected_shape(expected_input, target_batch=target_batch):
            raise ValueError(
                f"converted input shape mismatch: expected {expected_input}, got {actual_input}"
            )

    expected_outputs = validation.get("output_shapes", [])
    if expected_outputs and len(expected_outputs) != len(model.graph.output):
        raise ValueError(
            f"converted output count mismatch: expected {len(expected_outputs)}, "
            f"got {len(model.graph.output)}"
        )
    for output, expected in zip(model.graph.output, expected_outputs, strict=False):
        actual_output = _dim_values(output)
        if actual_output != _expected_shape(expected, target_batch=target_batch):
            raise ValueError(
                f"converted output shape mismatch for {output.name}: "
                f"expected {expected}, got {actual_output}"
            )


def model_batch_convert(
    source_onnx: str | Path,
    output_onnx: str | Path,
    *,
    target_batch: int,
    sidecar: dict[str, Any] | None = None,
    batch_conversion: dict[str, Any] | None = None,
) -> StaticBatchRewriteSummary:
    """Convert a static-batch ONNX export using sidecar conversion metadata."""
    profile_source = batch_conversion if batch_conversion is not None else sidecar
    if profile_source is None:
        raise ValueError("sidecar or batch_conversion must be provided")
    profile = _conversion_profile(profile_source)
    profile_id = profile.get("profile_id")
    if not isinstance(profile_id, str):
        raise ValueError("batch_conversion.profile_id is required")

    target_minimum = int(profile.get("target_batch", {}).get("minimum", 1))
    if target_batch < target_minimum:
        raise ValueError(
            f"target batch must be >= {target_minimum}, got {target_batch}"
        )

    model = onnx.load(os.fspath(source_onnx), load_external_data=False)
    source_batch = _static_batch_from_model(model)
    expected_source_batch = profile.get("source_batch_size")
    if expected_source_batch != source_batch:
        raise ValueError(
            f"source batch mismatch: model has {source_batch}, "
            f"profile has {expected_source_batch}"
        )

    summary = StaticBatchRewriteSummary(
        source_batch=source_batch,
        target_batch=target_batch,
        profile_id=profile_id,
    )
    summary.metadata_props_updated.extend(
        _rewrite_metadata_props(
            model,
            source_batch=source_batch,
            target_batch=target_batch,
        )
    )

    if target_batch == 1:
        _remove_batch_offset_add_for_batch_one(
            model,
            profile=profile,
            summary=summary,
        )

    for value_info in (
        list(model.graph.input) + list(model.graph.value_info) + list(model.graph.output)
    ):
        if _rewrite_value_info_batch_dim(
            value_info,
            source_batch=source_batch,
            target_batch=target_batch,
        ):
            summary.value_info_dims_updated.append(value_info.name)

    for initializer in model.graph.initializer:
        if _rewrite_tensor_proto(
            initializer,
            source_batch=source_batch,
            target_batch=target_batch,
            profile=profile,
        ):
            summary.initializer_tensors_updated.append(initializer.name)

    for node in model.graph.node:
        for attr in node.attribute:
            if attr.type != onnx.AttributeProto.TENSOR:
                continue
            if _rewrite_tensor_proto(
                attr.t,
                source_batch=source_batch,
                target_batch=target_batch,
                profile=profile,
            ):
                tensor_name = attr.t.name or f"{node.name}:{attr.name}"
                summary.constant_tensors_updated.append(tensor_name)

    _validate_generated_shapes(model, profile=profile, target_batch=target_batch)

    dst = Path(output_onnx)
    dst.parent.mkdir(parents=True, exist_ok=True)
    onnx.checker.check_model(model)
    onnx.save(model, os.fspath(dst))
    return summary
