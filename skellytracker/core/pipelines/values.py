"""The values of the ports of a pipeline, and the facts of a port that are fixed at load.

Implements: pipeline.outputs

A value of an instance port has ``I`` rows on each frame. A padding row has NaN coordinates, the
score 0, ``present`` false, and -1 for ``track_ids`` and ``class_index``. A value with no present
row is empty. An empty ``image`` or ``tensor`` value is ``None``.
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
    xyz: NDArray[np.float64]
    """``(I, P, 3)`` in source-image pixels. z is NaN for a ``2d`` output. A missing point is NaN."""
    score: NDArray[np.float64]
    """``(I, P)``. A missing point has 0."""
    instance_score: NDArray[np.float64]
    """``(I,)``: the instance score of each row, from its instance source row."""
    present: NDArray[np.bool_]
    """``(I,)``: true for a present row."""
    track_ids: NDArray[np.int64]
    """``(I,)``: -1 without an ``associate`` node."""

    @staticmethod
    def empty(point_names: tuple[str, ...], rows: int) -> InstanceKeypoints:
        """Return a value with ``rows`` padding rows."""
        count = len(point_names)
        return InstanceKeypoints(
            point_names, np.full((rows, count, 3), np.nan), np.zeros((rows, count)), np.zeros(rows),
            np.zeros(rows, dtype=bool), np.full(rows, -1, dtype=np.int64),
        )

    def instance(self, row: int) -> dict[str, Any]:
        """Return the fields of one row: ``xyz`` ``(P, 3)``, ``score`` ``(P,)``, ``instance_score``, ``present`` and ``track_id``."""
        return {
            "xyz": self.xyz[row], "score": self.score[row], "instance_score": float(self.instance_score[row]),
            "present": bool(self.present[row]), "track_id": int(self.track_ids[row]),
        }

    def single(self) -> dict[str, Any]:
        """Return row 0 of a value with ``I`` = 1. Raise ``ValueError`` for another ``I``."""
        if len(self.present) != 1:
            raise ValueError(f"single() needs I = 1; this value has I = {len(self.present)}")
        return self.instance(0)

    def by_track(self) -> dict[int, dict[str, Any]]:
        """Return the present rows with a track id, by track id. It is empty without an ``associate`` node."""
        return {int(track): self.instance(row) for row, track in enumerate(self.track_ids) if track >= 0 and self.present[row]}


@dataclass(frozen=True)
class InstanceBoxes:
    """The value of a ``detections`` port: ``I`` rows, each with one box."""

    xyxy: NDArray[np.float64]
    """``(I, 4)`` in source-image pixels."""
    score: NDArray[np.float64]
    """``(I,)``."""
    class_index: NDArray[np.int64]
    """``(I,)``: the class index of each row. -1 for a padding row."""
    present: NDArray[np.bool_]
    track_ids: NDArray[np.int64]

    @staticmethod
    def empty(rows: int) -> InstanceBoxes:
        """Return a value with ``rows`` padding rows."""
        return InstanceBoxes(
            np.full((rows, 4), np.nan), np.zeros(rows), np.full(rows, -1, dtype=np.int64),
            np.zeros(rows, dtype=bool), np.full(rows, -1, dtype=np.int64),
        )


@dataclass(frozen=True)
class InstanceRois:
    """The value of a ``roi`` port: ``I`` rows, each ``(cx, cy, w, h, rotation)`` in source-image pixels."""

    rois: NDArray[np.float64]
    """``(I, 5)``. ``rotation`` is in radians, clockwise, in ``[-pi, pi)``."""
    instance_score: NDArray[np.float64]
    present: NDArray[np.bool_]

    @staticmethod
    def empty(rows: int) -> InstanceRois:
        """Return a value with ``rows`` padding rows."""
        return InstanceRois(np.full((rows, 5), np.nan), np.zeros(rows), np.zeros(rows, dtype=bool))


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
    ``keypoints`` port. ``class_names`` is only for a ``detections`` port. ``max_instances`` and
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
            return InstanceKeypoints.empty(self.point_names, self.max_instances or 0)
        if self.port_type == "detections":
            return InstanceBoxes.empty(self.max_instances or 0)
        if self.port_type == "roi":
            return InstanceRois.empty(self.max_instances or 0)
        return None
