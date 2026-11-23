"""The batch loop of the generic detectors: N input tensors through a session with any batch form."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from skellytracker.core.eps.session import run_bound, run_preprocess, run_session
from skellytracker.core.model_spec.model import SidecarModel


def session_batch(session: Any) -> int | None:
    """Return the fixed batch of a session: dim 0 of its first input. None is a dynamic batch."""
    batch = session.get_inputs()[0].shape[0]
    return batch if isinstance(batch, int) and batch > 0 else None


def run_batches(session: Any, sidecar: SidecarModel, tensors: Sequence[np.ndarray] | np.ndarray) -> dict[str, np.ndarray]:
    """Run N input tensors, one for each image or crop. Return each output by name, with N rows.

    Implements: common.outputs

    `tensors` is the batch of `BatchPreprocessor` (N items on axis 0), or a sequence of N tensors.
    The function feeds the tensors to the input `input.name`, in their dtype: the preprocess
    gives the `input.dtype` of the precision. It reads each output by its `outputs[].name`. A
    session with a fixed batch runs groups of that batch. Zero tensors fill the last group, and
    their output rows go. A session with a dynamic batch runs the N tensors in one call. A float16
    output becomes float32, which changes no value. `tensors` must hold one tensor or more. An
    out-of-memory error of the session raises `VRAMExhaustionError`, with no retry. Each session
    call ends before the function returns, and no output shares memory with `tensors`.
    """
    names = [output.name for output in sidecar.outputs]
    stacked = tensors if isinstance(tensors, np.ndarray) else np.stack(tensors)
    batch = session_batch(session) or len(stacked)
    parts: list[list[np.ndarray]] = []
    for start in range(0, len(stacked), batch):
        group = stacked[start : start + batch]
        count = len(group)
        if count < batch:
            group = np.concatenate([group, np.zeros((batch - count, *group.shape[1:]), dtype=group.dtype)])
        parts.append([output[:count] for output in run_session(session, names, {sidecar.input.name: group})])
    return _joined(names, parts)


def preprocess_batches(
    preprocess: Any, frames: Sequence[Any], index: np.ndarray, theta: np.ndarray | None, batch: int, device_type: str, device_id: int,
) -> list[tuple[Any, int]]:
    """Run N items through a preprocess graph, in groups of `batch`. Return the device tensor and the item count of each group.

    `preprocess` is a session of `build_preprocess_graph` at `batch`. `frames` holds the device
    frame of each slot, `index` the slot of each item and `theta` the map of each item of an
    `affine_crop` graph. The last group gets padding items with the index 0 and the first map.
    """
    groups = []
    for start in range(0, len(index), batch):
        count = len(index[start : start + batch])
        pad = [0] * (batch - count)
        group_index = np.concatenate([index[start : start + batch], np.array(pad, np.int64)])
        group_theta = None if theta is None else np.concatenate([theta[start : start + batch], theta[pad]])
        groups.append((run_preprocess(preprocess, frames, group_index, group_theta, device_type, device_id), count))
    return groups


def run_bound_batches(session: Any, sidecar: SidecarModel, groups: Sequence[tuple[Any, int]]) -> dict[str, np.ndarray]:
    """Run the device tensors of `preprocess_batches` through the model session, as `run_batches` runs N tensors.

    Return each output by name, with the rows of the padding items removed.
    """
    names = [output.name for output in sidecar.outputs]
    parts = [[output[:count] for output in run_bound(session, sidecar.input.name, names, tensor)] for tensor, count in groups]
    return _joined(names, parts)


def _joined(names: list[str], parts: list[list[np.ndarray]]) -> dict[str, np.ndarray]:
    # shortcut: the groups of one output must have one shape after dim 0, which each implemented
    # decode gives; a decode with a row count for each image must return the groups apart.
    joined = [np.concatenate(group_outputs) for group_outputs in zip(*parts, strict=True)]
    return {
        name: (output.astype(np.float32) if output.dtype == np.float16 else output)
        for name, output in zip(names, joined, strict=True)
    }
