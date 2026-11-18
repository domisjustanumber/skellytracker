"""The batch conversion of a static-batch ONNX artifact (section `common.batch_conversion`).

`model_batch_convert` makes the generated artifact of the profile `static-batch-v1` in memory. It
needs the `onnx` package, a base dependency of skellytracker.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any

SUPPORTED_PROFILES = frozenset({"static-batch-v1"})


def _graph_tensors(graph: Any) -> list[Any]:
    import onnx

    tensors = list(graph.initializer)
    for sparse in graph.sparse_initializer:
        tensors += [sparse.values, sparse.indices]
    for node in graph.node:
        for attribute in node.attribute:
            tensors.extend([attribute.t] if attribute.type == onnx.AttributeProto.TENSOR else attribute.tensors)
            for subgraph in [attribute.g] if attribute.type == onnx.AttributeProto.GRAPH else attribute.graphs:
                tensors.extend(_graph_tensors(subgraph))
    return tensors


def _set_first_value(tensor: Any, source_batch: int, target_batch: int) -> None:
    """Step 3 for one tensor: a 1-D int64 tensor with 2 or more values and the first value `S`."""
    import onnx
    from onnx import numpy_helper

    if tensor.data_type != onnx.TensorProto.INT64:
        return
    values = numpy_helper.to_array(tensor)
    if values.ndim == 1 and values.size >= 2 and values[0] == source_batch:
        changed = values.copy()
        changed[0] = target_batch
        tensor.CopyFrom(numpy_helper.from_array(changed, name=tensor.name))


def model_batch_convert(
    source_onnx: str | os.PathLike,
    *,
    source_batch: int,
    target_batch: int,
    profile_id: str = "static-batch-v1",
) -> bytes:
    """Return the bytes of the generated artifact of `source_onnx` at the batch `target_batch`.

    Implements: common.batch_conversion

    `source_batch` is `batching.batch` of the sidecar (`S`). `target_batch` is `T`. `profile_id`
    is `batching.batch_conversion.profile_id`. The caller verifies the source file against its
    `sha256` first. The function checks the conditions of the profile, applies its three steps in
    order and runs its check. It raises `ValueError` when the host does not support the profile,
    when a condition is not met or when the check fails. The generated artifact has no sidecar and
    no `sha256`. The function writes no file.
    """
    import onnx
    from onnx.external_data_helper import uses_external_data

    if profile_id not in SUPPORTED_PROFILES:
        raise ValueError(f"unsupported batch_conversion.profile_id: {profile_id!r}")
    if target_batch < 1:
        raise ValueError(f"the target batch must be 1 or larger, not {target_batch}")
    name = Path(source_onnx).name
    model = onnx.load(os.fspath(source_onnx), load_external_data=False)
    if any(uses_external_data(tensor) for tensor in _graph_tensors(model.graph)):
        raise ValueError(f"{name} uses external data; the profile {profile_id} does not convert it")
    initializers = {initializer.name for initializer in model.graph.initializer}
    inputs = [value for value in model.graph.input if value.name not in initializers]
    if not inputs:
        raise ValueError(f"{name} has no graph input")
    for value in inputs:
        dims = value.type.tensor_type.shape.dim
        if not dims or not dims[0].HasField("dim_value") or dims[0].dim_value != source_batch:
            raise ValueError(f"the input {value.name!r} of {name} has no static dim 0 equal to {source_batch}")

    # Step 1, `metadata_batch`. `args` holds the repr of a Python dict: the Ultralytics form.
    for prop in model.metadata_props:
        if prop.key == "batch" and prop.value == str(source_batch):
            prop.value = str(target_batch)
        elif prop.key == "args":
            try:
                args = ast.literal_eval(prop.value)
            except (SyntaxError, TypeError, ValueError, RecursionError):
                continue
            if isinstance(args, dict) and args.get("batch") == source_batch:
                args["batch"] = target_batch
                prop.value = repr(args)
    # Step 2, `leading_dim`.
    for value in [*inputs, *model.graph.output, *model.graph.value_info]:
        dims = value.type.tensor_type.shape.dim
        if dims and dims[0].HasField("dim_value") and dims[0].dim_value == source_batch:
            dims[0].dim_value = target_batch
    # Step 3, `int64_shape_first_dim`: the initializers and the TENSOR attributes of the graph nodes.
    for initializer in model.graph.initializer:
        _set_first_value(initializer, source_batch, target_batch)
    for node in model.graph.node:
        for attribute in node.attribute:
            if attribute.type == onnx.AttributeProto.TENSOR:
                _set_first_value(attribute.t, source_batch, target_batch)

    try:
        onnx.checker.check_model(model, full_check=True)
    except (onnx.checker.ValidationError, onnx.shape_inference.InferenceError) as exc:
        raise ValueError(f"the graph of {name} at batch {target_batch} fails the strict shape check: {exc}") from exc
    return model.SerializeToString()
