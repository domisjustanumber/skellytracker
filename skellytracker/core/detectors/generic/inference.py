"""The batch loop of the generic detectors: N input tensors through a session with any batch form."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from skellytracker.core.eps.session import run_session
from skellytracker.core.model_spec.model import SidecarModel


def session_batch(session: Any) -> int | None:
    """Return the fixed batch of a session: dim 0 of its first input. None is a dynamic batch."""
    batch = session.get_inputs()[0].shape[0]
    return batch if isinstance(batch, int) and batch > 0 else None


def run_batches(session: Any, sidecar: SidecarModel, tensors: Sequence[np.ndarray]) -> dict[str, np.ndarray]:
    """Run N input tensors, one for each image or crop. Return each output by name, with N rows.

    Implements: common.outputs

    The function feeds the tensors to the input `input.name`, in their dtype: `preprocess_image`
    gives the `input.dtype` of the precision. It reads each output by its `outputs[].name`. A
    session with a fixed batch runs groups of that batch. Zero tensors fill the last group, and
    their output rows go. A session with a dynamic batch runs the N tensors in one call. A float16
    output becomes float32, which changes no value. `tensors` must hold one tensor or more. An
    out-of-memory error of the session raises `VRAMExhaustionError`, with no retry.
    """
    names = [output.name for output in sidecar.outputs]
    stacked = np.stack(tensors)
    batch = session_batch(session) or len(stacked)
    parts: list[list[np.ndarray]] = []
    for start in range(0, len(stacked), batch):
        group = stacked[start : start + batch]
        count = len(group)
        if count < batch:
            group = np.concatenate([group, np.zeros((batch - count, *group.shape[1:]), dtype=group.dtype)])
        parts.append([output[:count] for output in run_session(session, names, {sidecar.input.name: group})])
    # shortcut: the groups of one output must have one shape after dim 0, which each implemented
    # decode gives; a decode with a row count for each image must return the groups apart.
    joined = [np.concatenate(group_outputs) for group_outputs in zip(*parts, strict=True)]
    return {
        name: (output.astype(np.float32) if output.dtype == np.float16 else output)
        for name, output in zip(names, joined, strict=True)
    }
