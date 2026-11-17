"""The values of the ports of a pipeline, and the facts of a port that are fixed at load.

Implements: pipeline.outputs

A value of an instance port has ``I`` rows on each frame. A padding row has NaN coordinates, the
score 0, the raw score 0, ``present`` false, and -1 for ``track_ids`` and ``class_index``. A value with no present
row is empty. The only ``image`` value is the frame of the call: the run passes it by reference and
never copies it. A ``flag`` value is ``True`` or ``False``, never empty.

A ``keypoints`` value holds ``xy`` for each output, and ``z`` only for a ``3d`` output. A ``2d``
output has no ``z``: ``z is None``. ``xy`` and ``z`` are float64. ``geometry`` is ``"2d"`` or ``"3d"``.
No value has an ``xyz`` field, and the package has no alias for it. ``instance(i)`` and ``single()``
give a dict with the keys ``xy`` and ``z``. ``InstanceKeypoints`` has no accessor by track id: the
``associate`` node type adds one. This version tracks one person:
read row 0, and check ``present[0]`` first.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class InstanceKeypoints:
    """The value of a ``keypoints`` port: ``I`` rows, each with ``P`` points."""

    point_names: tuple[str, ...]
    """``(P,)``: the point names ``<group>/<point>``."""
    xy: NDArray[np.float64]
    """``(I, P, 2)``: x and y of each point, in source-image pixels. A missing point is NaN."""
    score: NDArray[np.float64]
    """``(I, P)``: the score of each point, after the score map of the sidecar when its size has one
    (a value in ``[0, 1]``). A missing point has 0."""
    raw_score: NDArray[np.float64]
    """``(I, P)``: the decode score of each point, before the score map. Equal to ``score`` for a
    model with no score map and for MediaPipe. A missing point has 0. A point with ``raw_score > 0``
    is present, also when its mapped ``score`` rounds to 0."""
    instance_score: NDArray[np.float64]
    """``(I,)``: the instance score of each row, from its instance source row."""
    present: NDArray[np.bool_]
    """``(I,)``: true for a present row."""
    track_ids: NDArray[np.int64]
    """``(I,)``: -1 without an ``associate`` node."""
    z: NDArray[np.float64] | None = None
    """``(I, P)``, only for a ``3d`` output: the root-relative depth of each point in ``depth_unit``.
    A missing point is NaN. ``None`` for a ``2d`` output."""

    @property
    def geometry(self) -> str:
        """``"3d"`` when the value has ``z``, else ``"2d"``."""
        return "2d" if self.z is None else "3d"

    @staticmethod
    def empty(point_names: tuple[str, ...], rows: int, geometry: str | None = "2d") -> InstanceKeypoints:
        """Return a value with ``rows`` padding rows. It has ``z`` only when ``geometry`` is ``"3d"``."""
        count = len(point_names)
        return InstanceKeypoints(
            point_names, np.full((rows, count, 2), np.nan), np.zeros((rows, count)), np.zeros((rows, count)), np.zeros(rows),
            np.zeros(rows, dtype=bool), np.full(rows, -1, dtype=np.int64),
            np.full((rows, count), np.nan) if geometry == "3d" else None,
        )

    def instance(self, row: int) -> dict[str, Any]:
        """Return the fields of one row: ``xy`` ``(P, 2)``, ``z`` ``(P,)`` or ``None``, ``score`` ``(P,)``, ``raw_score`` ``(P,)``, ``instance_score``, ``present`` and ``track_id``."""
        return {
            "xy": self.xy[row], "z": None if self.z is None else self.z[row], "score": self.score[row],
            "raw_score": self.raw_score[row], "instance_score": float(self.instance_score[row]),
            "present": bool(self.present[row]), "track_id": int(self.track_ids[row]),
        }

    def single(self) -> dict[str, Any]:
        """Return row 0 of a value with ``I`` = 1. Raise ``ValueError`` for another ``I``."""
        if len(self.present) != 1:
            raise ValueError(f"single() needs I = 1; this value has I = {len(self.present)}")
        return self.instance(0)


@dataclass(frozen=True)
class InstanceBoxes:
    """The value of a ``boxes`` port: ``I`` rows, each with one box ``(cx, cy, w, h, rotation)`` in source-image pixels."""

    boxes: NDArray[np.float64]
    """``(I, 5)``: the centre, the width, the height and the rotation. ``rotation`` is in radians, clockwise, in ``[-pi, pi)``."""
    instance_score: NDArray[np.float64]
    """``(I,)``: the instance score of each row, from its instance source row."""
    class_index: NDArray[np.int64]
    """``(I,)``: the class index of a detector row. -1 for a padding row and for a box that no detector made."""
    present: NDArray[np.bool_]
    """``(I,)``: true for a present row."""
    track_ids: NDArray[np.int64]
    """``(I,)``: -1 without an ``associate`` node."""

    @staticmethod
    def empty(rows: int) -> InstanceBoxes:
        """Return a value with ``rows`` padding rows."""
        return InstanceBoxes(
            np.full((rows, 5), np.nan), np.zeros(rows), np.full(rows, -1, dtype=np.int64),
            np.zeros(rows, dtype=bool), np.full(rows, -1, dtype=np.int64),
        )


def is_empty(value: Any) -> bool:
    """Return true for an empty value: ``None``, or an instance value with no present row."""
    return value is None or (hasattr(value, "present") and not bool(np.any(value.present)))


@dataclass(frozen=True)
class Group:
    """A named run of point columns of a ``keypoints`` port."""

    name: str
    start: int
    count: int
    landmark_schema: str | None


@dataclass(frozen=True)
class PortInfo:
    """The facts of one port that are fixed at load. The output schema gives them for each output.

    ``point_names``, ``groups``, ``geometry``, ``depth_unit`` and ``edges`` are only for a
    ``keypoints`` port. ``class_names`` is only for a ``boxes`` port whose instance source is a detector. ``max_instances`` and
    ``instance_source`` are for each instance port.
    """

    port_type: str
    max_instances: int | None = None
    instance_source: str | None = None
    point_names: tuple[str, ...] = ()
    groups: tuple[Group, ...] = ()
    geometry: str | None = None
    depth_unit: str | None = None
    class_names: tuple[str | None, ...] | None = None
    edges: tuple[tuple[str, str], ...] = ()
    tracked: bool = False

    def empty(self) -> Any:
        """Return the empty value of the port."""
        if self.port_type == "keypoints":
            return InstanceKeypoints.empty(self.point_names, self.max_instances or 0, self.geometry)
        if self.port_type == "boxes":
            return InstanceBoxes.empty(self.max_instances or 0)
        return None
