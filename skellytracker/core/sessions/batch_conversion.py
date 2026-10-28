"""Sidecar-guided converter for static-batch ONNX exports."""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import onnx
from onnx import TensorProto, numpy_helper
from onnx.external_data_helper import uses_external_data

SUPPORTED_PROFILES = frozenset({"static-batch-v1"})
_SHAPE_TENSOR_MINIMUM_SIZE = 2


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


def _graph_inputs(model: onnx.ModelProto) -> list[onnx.ValueInfoProto]:
    # Older exports also list initializers in graph.input. They are not runtime inputs.
    initializer_names = {initializer.name for initializer in model.graph.initializer}
    return [value_info for value_info in model.graph.input if value_info.name not in initializer_names]


def _graph_tensors(graph: onnx.GraphProto) -> list[onnx.TensorProto]:
    tensors = list(graph.initializer) + [sparse.values for sparse in graph.sparse_initializer]
    for node in graph.node:
        for attr in node.attribute:
            tensors.extend([attr.t] if attr.type == onnx.AttributeProto.TENSOR else attr.tensors)
            for subgraph in [attr.g] if attr.type == onnx.AttributeProto.GRAPH else attr.graphs:
                tensors.extend(_graph_tensors(subgraph))
    return tensors


def _static_batch_from_model(model: onnx.ModelProto) -> int:
    inputs = _graph_inputs(model)
    if not inputs:
        raise ValueError("graph has no inputs")
    batches = set()
    for value_info in inputs:
        dims = value_info.type.tensor_type.shape.dim
        if not dims or not dims[0].HasField("dim_value"):
            raise ValueError(f"graph input {value_info.name!r} has no static batch dimension")
        batches.add(dims[0].dim_value)
    if len(batches) != 1:
        raise ValueError(f"graph inputs have different batch dimensions: {sorted(batches)}")
    batch_size = batches.pop()
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
    if not batch_dim.HasField("dim_value") or batch_dim.dim_value != source_batch:
        return False
    batch_dim.dim_value = target_batch
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
            # `args` holds a Python dict repr: the Ultralytics metadata form.
            try:
                args = ast.literal_eval(prop.value)
            except (SyntaxError, TypeError, ValueError, RecursionError):
                continue
            if isinstance(args, dict) and args.get("batch") == source_batch:
                args["batch"] = target_batch
                prop.value = repr(args)
                updated.append(prop.key)
    return updated


def _rewrite_tensor_proto(
    tensor: onnx.TensorProto,
    *,
    source_batch: int,
    target_batch: int,
) -> bool:
    if tensor.data_type != TensorProto.INT64:
        return False
    array = numpy_helper.to_array(tensor)
    if array.ndim != 1 or array.size < _SHAPE_TENSOR_MINIMUM_SIZE or array[0] != source_batch:
        return False
    rewritten = array.copy()
    rewritten[0] = target_batch
    tensor.CopyFrom(numpy_helper.from_array(rewritten, name=tensor.name))
    return True


def model_batch_convert(
    source_onnx: str | Path,
    output_onnx: str | Path,
    *,
    target_batch: int,
    sidecar: dict[str, Any] | None = None,
    batch_conversion: dict[str, Any] | None = None,
) -> StaticBatchRewriteSummary:
    """Convert a static-batch ONNX export with the `static-batch-v1` profile."""
    if batch_conversion is None and sidecar is None:
        raise ValueError("sidecar or batch_conversion must be provided")
    profile = batch_conversion
    if profile is None:
        profile = (sidecar.get("batching") or {}).get("batch_conversion")
    if not isinstance(profile, dict):
        raise ValueError("sidecar does not include batching.batch_conversion")
    profile_id = profile.get("profile_id")
    if not isinstance(profile_id, str) or profile_id not in SUPPORTED_PROFILES:
        raise ValueError(f"unsupported batch_conversion.profile_id: {profile_id!r}")
    if target_batch < 1:
        raise ValueError(f"target batch must be >= 1, got {target_batch}")

    model = onnx.load(os.fspath(source_onnx), load_external_data=False)
    if any(uses_external_data(tensor) for tensor in _graph_tensors(model.graph)):
        raise ValueError("source ONNX file uses external data, which is not supported")
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

    for value_info in (
        _graph_inputs(model) + list(model.graph.value_info) + list(model.graph.output)
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
            ):
                tensor_name = attr.t.name or f"{node.name}:{attr.name}"
                summary.constant_tensors_updated.append(tensor_name)

    try:
        onnx.checker.check_model(model, full_check=True)
    except (onnx.checker.ValidationError, onnx.shape_inference.InferenceError) as exc:
        raise ValueError(f"converted graph fails the strict shape check: {exc}") from exc

    dst = Path(output_onnx)
    dst.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, os.fspath(dst))
    return summary
