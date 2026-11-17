"""The generic annotator: it draws each delivered output of one camera result from the output schema."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

_COLOURS = ((0, 255, 0), (255, 128, 0), (0, 128, 255), (255, 0, 255), (0, 255, 255))  # BGR, one for each row


def annotate(image: np.ndarray, result: Mapping[str, Any], output_schema: Mapping[str, Mapping[str, Any]], *, min_score: float = 0.0) -> np.ndarray:
    """Return a copy of the BGR `image` with each output of `result` drawn.

    `result` is the result of one camera. `output_schema` is the output schema of the run. The
    output `wholebody` or `holistic` gives its points and its `edges`. The output `boxes` gives its
    boxes as rectangles, with the class name and the score of a row that has a class. The function
    skips a padding row, a missing point and a point with a score below `min_score`.
    """
    import cv2

    canvas = image.copy()
    for name, value in result.items():
        if name not in output_schema:
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
            elif schema["port_type"] == "boxes" and np.isfinite(value.xyxy[row]).all():
                x1, y1, x2, y2 = (int(v) for v in np.round(value.xyxy[row]))
                cv2.rectangle(canvas, (x1, y1), (x2, y2), colour, 1, cv2.LINE_AA)
                index = int(value.class_index[row])
                if index >= 0:
                    class_names = schema.get("class_names") or ()
                    label = class_names[index] if index < len(class_names) and class_names[index] else str(index)
                    cv2.putText(canvas, f"{label} {value.score[row]:.2f}", (x1, max(y1 - 4, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, colour, 1, cv2.LINE_AA)
    return canvas
