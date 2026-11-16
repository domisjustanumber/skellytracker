"""The generic annotator: it draws each output of one camera result from the output schema."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from skellytracker.core.pipelines.config import RESULT_FIELDS

_COLOURS = ((0, 255, 0), (255, 128, 0), (0, 128, 255), (255, 0, 255), (0, 255, 255))  # BGR, one for each row


def annotate(image: np.ndarray, result: Mapping[str, Any], output_schema: Mapping[str, Mapping[str, Any]], *, min_score: float = 0.0) -> np.ndarray:
    """Return a copy of the BGR `image` with each output of `result` drawn.

    `result` is the result of one camera. `output_schema` is the output schema of the run. A
    `keypoints` output gives its points and its `edges`, a `detections` output gives its boxes with
    the class name and the score, and a `roi` output gives its ROIs as rotated rectangles. The
    function skips a padding row, a missing point and a point with a score below `min_score`.
    """
    import cv2

    canvas = image.copy()
    for name, value in result.items():
        if name in RESULT_FIELDS or value is None or name not in output_schema:
            continue
        schema = output_schema[name]
        for row in np.flatnonzero(value.present):
            colour = _COLOURS[int(row) % len(_COLOURS)]
            if schema["port_type"] == "keypoints":
                xy = value.xy[row]
                shown = np.isfinite(xy).all(axis=1) & (value.score[row] >= min_score)
                points = {point: tuple(int(v) for v in np.round(xy[column])) for column, point in enumerate(value.point_names) if shown[column]}
                for start, end in schema.get("edges", ()):
                    if start in points and end in points:
                        cv2.line(canvas, points[start], points[end], colour, 1, cv2.LINE_AA)
                for point in points.values():
                    cv2.circle(canvas, point, 2, colour, -1, cv2.LINE_AA)
            elif schema["port_type"] == "detections" and np.isfinite(value.xyxy[row]).all():
                x1, y1, x2, y2 = (int(v) for v in np.round(value.xyxy[row]))
                cv2.rectangle(canvas, (x1, y1), (x2, y2), colour, 2)
                class_names = schema.get("class_names") or ()
                index = int(value.class_index[row])
                label = class_names[index] if 0 <= index < len(class_names) and class_names[index] else str(index)
                cv2.putText(canvas, f"{label} {value.score[row]:.2f}", (x1, max(y1 - 4, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, colour, 1, cv2.LINE_AA)
            elif schema["port_type"] == "roi" and np.isfinite(value.rois[row]).all():
                cx, cy, width, height, rotation = value.rois[row]
                x_axis = np.array([np.cos(rotation), np.sin(rotation)]) * width / 2
                y_axis = np.array([-np.sin(rotation), np.cos(rotation)]) * height / 2
                corners = np.array([cx, cy]) + [-x_axis - y_axis, x_axis - y_axis, x_axis + y_axis, -x_axis + y_axis]
                cv2.polylines(canvas, [np.round(corners).astype(np.int32)], True, colour, 1, cv2.LINE_AA)
    return canvas
