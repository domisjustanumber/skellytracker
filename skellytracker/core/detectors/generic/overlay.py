"""The edge groups of `keypoint.overlay` for drawing (section `post.keypoint.overlay`)."""
from __future__ import annotations

from dataclasses import dataclass

from skellytracker.core.model_spec.model import KeypointSpec

Edge = tuple[str, str]


@dataclass(frozen=True)
class OverlayGroup:
    """The edges of one part of `keypoint.overlay.parts`, with its colors.

    `keypoint_color` is the color of the part, else `keypoint.overlay.keypoint_color`, else None.
    """

    name: str
    edges: tuple[Edge, ...]
    edge_color: tuple[float, ...]
    edge_thickness: int
    keypoint_color: tuple[float, ...] | None


def overlay_edges(keypoint: KeypointSpec) -> tuple[Edge, ...]:
    """Return the edges of the skeleton to draw.

    Implements: post.keypoint.overlay

    The skeleton is the one that `keypoint.overlay.skeleton` names, or its inline edge list. With
    no `overlay.skeleton`, it is the first entry of `keypoint.skeletons`.
    """
    selected = None if keypoint.overlay is None else keypoint.overlay.skeleton
    if isinstance(selected, list):
        edges = selected
    else:
        skeletons = [skeleton for skeleton in keypoint.skeletons if selected in (None, skeleton.name)]
        edges = skeletons[0].edges if skeletons else []
    return tuple((str(edge[0]), str(edge[1])) for edge in edges)


def overlay_groups(keypoint: KeypointSpec) -> tuple[OverlayGroup, ...]:
    """Return one group for each part of `keypoint.overlay.parts`, in declaration order.

    Implements: post.keypoint.overlay

    A part with `edges` gets these edges of the skeleton. An other edge goes to the first `prefix`
    part, in declaration order, whose prefix starts an endpoint of the edge. The default part, with
    no `edges` and no `prefix`, gets each edge that no other part selects. A sidecar with no
    overlay parts gives no group.
    """
    if keypoint.overlay is None:
        return ()
    parts = keypoint.overlay.parts
    explicit = {name: {frozenset(edge) for edge in part.edges} for name, part in parts.items() if part.edges is not None}
    prefixed = [(name, part.prefix) for name, part in parts.items() if part.prefix is not None]
    default = next((name for name, part in parts.items() if part.edges is None and part.prefix is None), None)
    grouped: dict[str, list[Edge]] = {name: [] for name in parts}
    for edge in overlay_edges(keypoint):
        name = next((name for name, edges in explicit.items() if frozenset(edge) in edges), None)
        if name is None:
            name = next((name for name, prefix in prefixed if edge[0].startswith(prefix) or edge[1].startswith(prefix)), default)
        if name is not None:
            grouped[name].append(edge)
    result = []
    for name, part in parts.items():
        color = part.keypoint_color if part.keypoint_color is not None else keypoint.overlay.keypoint_color
        result.append(
            OverlayGroup(name, tuple(grouped[name]), tuple(part.edge_color), part.edge_thickness, None if color is None else tuple(color))
        )
    return tuple(result)
