"""The taps of a run: a `record` tap writes the value of a port, and a `replay` tap reads it.

Implements: pipeline.taps

The forms of a JSONL line. Each line is one present row and has `image_id`, `frame_index`,
`camera_id` and `row`:

- `boxes.jsonl`: `box` `[cx, cy, w, h, rotation]`, `bbox` `[x, y, width, height]` (the
  axis-aligned bounds of the box), `score` (the instance score) and `class` (the class name, or
  null when the row has no class).
- `keypoints.jsonl`: `keypoints` `[x, y, score, ...]`, three numbers for each point, and `score`,
  the instance score. A missing point has null for x and y.

A `flag` port has no rows: `flag.jsonl` has one line for each frame and camera, with `image_id`,
`frame_index`, `camera_id` and `flag` (true or false), and no `row`.
"""
from __future__ import annotations

import importlib.metadata
import json
import math
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from skellytracker.core.pipelines import timing
from skellytracker.core.pipelines.config import FRAME, PipelineConfig, Tap
from skellytracker.core.pipelines.values import PortInfo

TAP_SCHEMA = "skellytracker.tap/1"
MANIFEST = "tap.json"
MATCH_FIELDS = ("schema", "port", "port_type", "upstream_sha256", "image_list_sha256", "camera_ids", "running_mode")
JSONL_TYPES = ("boxes", "keypoints", "flag")


def upstream_nodes(config: PipelineConfig, node_id: str) -> list[str]:
    """Return the ids of `node_id` and of each node upstream of it, also through `@prev` inputs, sorted."""
    inputs = {node.id: (node.inputs if isinstance(node.inputs, list) else list(node.inputs.values())) for node in config.nodes}
    found: set[str] = set()
    todo = [node_id]
    while todo:
        current = todo.pop()
        if current not in found:
            found.add(current)
            todo += [source for ref in inputs[current] if (source := ref.split(".")[0]) != FRAME]
    return sorted(found)


def check_tap_port(tap: Tap, info: PortInfo) -> None:
    """Refuse a tap whose file form no text fixes: a `3d` keypoints port. The frame image has no tap (V-pipeline.taps-1)."""
    if info.port_type not in JSONL_TYPES:
        raise ValueError(f"V-pipeline.taps-1: the tap {tap.name!r} names the port {tap.port} of the type {info.port_type}; a tap port is boxes, keypoints or flag")
    if info.port_type == "keypoints" and info.geometry == "3d":
        raise ValueError(f"the tap {tap.name!r} names the 3d keypoints port {tap.port}: the pipeline spec gives no place for z in a keypoints.jsonl line")


def make_manifest(
    config: PipelineConfig, tap: Tap, info: PortInfo, *, run_id: str, node_items: Mapping[str, Mapping[str, Any]],
    image_list_sha256: str | None, camera_ids: Sequence[int | str], running_mode: str,
) -> dict[str, Any]:
    """Return the fields of `tap.json` of one tap of this run, without `record_count`."""
    node_id = tap.port.split(".")[0]
    return {
        "schema": TAP_SCHEMA,
        "skellytracker_version": importlib.metadata.version("skellytracker"),
        "run_id": run_id,
        "port": tap.port,
        "port_type": info.port_type,
        "point_names": list(info.point_names) if info.port_type == "keypoints" else None,
        "class_names": list(info.class_names or ()) if info.port_type == "boxes" else None,
        "geometry": info.geometry if info.port_type == "keypoints" else None,
        "upstream_sha256": timing.upstream_sha256(config, node_id),
        "nodes": [dict(node_items[item]) for item in upstream_nodes(config, node_id)],
        "image_list_sha256": image_list_sha256,
        "camera_ids": list(camera_ids),
        "running_mode": running_mode,
        "pipeline_sha256": timing.pipeline_sha256(config),
    }


def _number(value: float) -> float | None:
    return None if math.isnan(value) else float(value)


def row_record(value: Any, row: int, info: PortInfo) -> dict[str, Any]:
    """Return the fields of one present row for its JSONL line."""
    if info.port_type == "boxes":
        cx, cy, w, h, rotation = (float(item) for item in value.boxes[row])
        half_x = (abs(w * math.cos(rotation)) + abs(h * math.sin(rotation))) / 2
        half_y = (abs(w * math.sin(rotation)) + abs(h * math.cos(rotation))) / 2
        index = int(value.class_index[row])
        return {
            "box": [cx, cy, w, h, rotation], "bbox": [cx - half_x, cy - half_y, 2 * half_x, 2 * half_y],
            "score": float(value.instance_score[row]), "class": (info.class_names or ())[index] if index >= 0 else None,
        }
    points = [number for (x, y), score in zip(value.xy[row].tolist(), value.score[row].tolist(), strict=True) for number in (_number(x), _number(y), score)]
    return {"keypoints": points, "raw_score": value.raw_score[row].tolist(), "score": float(value.instance_score[row])}


class RecordTap:
    """One `record` tap. `close()` writes `tap.json` last."""

    def __init__(self, tap: Tap, tap_dir: Path, info: PortInfo) -> None:
        check_tap_port(tap, info)
        self.tap, self.info, self.folder = tap, info, tap_dir / tap.name
        if self.folder.exists() and any(self.folder.iterdir()):
            raise ValueError(f"V-pipeline.taps-5: the folder {self.folder.name} of the record tap {tap.name!r} exists and is not empty")
        self.folder.mkdir(parents=True, exist_ok=True)
        self.count = 0
        self._file: Any = open(self.folder / f"{info.port_type}.jsonl", "w", encoding="utf-8", newline="\n")  # noqa: SIM115 (`close` closes it)

    def write(self, value: Any, frame_index: int, camera_id: int | str, image_id: int) -> None:
        """Write one line for each present row of the value of one image, in ascending row order. A flag gives one line."""
        if self.info.port_type == "flag":
            record = {"image_id": image_id, "frame_index": frame_index, "camera_id": camera_id, "flag": bool(value)}
            self._file.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
            self.count += 1
            return
        for row in np.flatnonzero(value.present):
            record = {"image_id": image_id, "frame_index": frame_index, "camera_id": camera_id, "row": int(row), **row_record(value, int(row), self.info)}
            self._file.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
            self.count += 1

    def discard(self) -> None:
        """Close the data file and write no `tap.json`: the folder then holds a partial record."""
        if self._file is not None:
            self._file.close()
            self._file = None

    def close(self, manifest: Mapping[str, Any]) -> None:
        """Close the data file, then write `tap.json`: to a temporary file, then a rename. A second call does nothing."""
        if self._file is None:
            return
        self.discard()
        temporary = self.folder / (MANIFEST + ".tmp")
        temporary.write_text(json.dumps({**manifest, "record_count": self.count}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, self.folder / MANIFEST)


class ReplayTap:
    """One `replay` tap: the values of its port, read at start.

    `expected` is the manifest of this run for the tap (`make_manifest`). `node_facts` maps each
    upstream node to `(sidecar_sha256, artifact_sha256, EP key)` of this run. `image_ids[k]` is the
    `image_id` of the frame `k` of the COCO input form.
    """

    def __init__(
        self, tap: Tap, tap_dir: Path, info: PortInfo, expected: Mapping[str, Any],
        node_facts: Mapping[str, tuple[str | None, str | None, str | None]], image_ids: Sequence[int] | None,
    ) -> None:
        check_tap_port(tap, info)
        self.tap, self.info = tap, info
        folder, rule = tap_dir / tap.name, f"V-pipeline.taps-3: the replay tap {tap.name!r}"
        if not (folder / MANIFEST).is_file():
            raise ValueError(f"{rule} has no {MANIFEST}")
        manifest = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
        if manifest.get("image_list_sha256") is None:
            raise ValueError(f"{rule} has `image_list_sha256: null`: only a tap of the COCO input form can be replayed")
        for name in MATCH_FIELDS:
            if manifest.get(name) != expected[name]:
                raise ValueError(f"{rule} does not agree with the run in `{name}`: the tap has {manifest.get(name)!r}, the run has {expected[name]!r}")
        items = {item["id"]: item for item in manifest.get("nodes", [])}
        for node_id, facts in node_facts.items():
            item = items.get(node_id, {})
            recorded = (item.get("sidecar_sha256"), item.get("artifact_sha256"), (item.get("execution") or {}).get("used_ep"))
            for name, was, now in zip(("sidecar_sha256", "artifact_sha256", "used_ep"), recorded, facts, strict=True):
                if was != now:
                    raise ValueError(f"{rule} does not agree with the run in `{name}` of the node {node_id}: the tap has {was!r}, the run has {now!r}")
        self.values = self._read(folder / f"{info.port_type}.jsonl", list(expected["camera_ids"]), list(image_ids or ()), tap.port.split(".")[0])

    def _read(self, path: Path, camera_ids: list[Any], image_ids: list[int], node_id: str) -> dict[tuple[int, Any], Any]:
        name, info, rows = self.tap.name, self.info, self.info.max_instances or 0
        if not path.is_file():
            raise ValueError(f"V-pipeline.taps-4: the replay tap {name!r} has no file {path.name}")
        values: dict[tuple[int, Any], Any] = {}
        with path.open(encoding="utf-8") as file:
            for number, text in enumerate(file, start=1):
                if not text.strip():
                    continue
                line = json.loads(text)
                frame_index, camera_id, row = line.get("frame_index"), line.get("camera_id"), line.get("row")
                where = f"the replay tap {name!r}, line {number}"
                known = isinstance(frame_index, int) and 0 <= frame_index < len(image_ids) and image_ids[frame_index] == line.get("image_id")
                if not known or camera_id not in camera_ids:
                    raise ValueError(f"V-pipeline.taps-4: {where}: the image {line.get('image_id')!r} (frame {frame_index!r}, camera {camera_id!r}) is not an image of the run")
                if info.port_type == "flag":
                    if not isinstance(line.get("flag"), bool) or (frame_index, camera_id) in values:
                        raise ValueError(f"V-pipeline.taps-4: {where}: a flag line has `flag` true or false, one time for each frame and camera")
                    values[frame_index, camera_id] = line["flag"]
                    continue
                if isinstance(row, bool) or not isinstance(row, int) or not 0 <= row < rows:
                    raise ValueError(f"V-pipeline.taps-6: {where}: `row` is {row!r}; it must be an integer in [0, {rows})")
                value = values.setdefault((frame_index, camera_id), info.empty())
                if value.present[row]:
                    raise ValueError(f"V-pipeline.taps-6: {where}: the row {row} occurs twice for one image")
                self._fill(value, row, line, where)
        if info.port_type == "flag":  # a flag is never empty: each frame and camera has its line
            missing = [(frame, camera) for frame in range(len(image_ids)) for camera in camera_ids if (frame, camera) not in values]
            if missing:
                raise ValueError(f"V-pipeline.taps-4: the replay tap {name!r} has no flag line for the frame {missing[0][0]} of the camera {missing[0][1]!r}")
        if info.instance_source == node_id:
            for (frame_index, camera_id), value in values.items():
                count = int(value.present.sum())
                if not value.present[:count].all():
                    raise ValueError(
                        f"V-pipeline.taps-6: the replay tap {name!r}: the rows of the frame {frame_index} of the camera {camera_id!r} "
                        f"are not 0 to {count - 1}; the node {node_id} is an instance source"
                    )
        return values

    def _fill(self, value: Any, row: int, line: Mapping[str, Any], where: str) -> None:
        info = self.info
        if info.port_type == "boxes":
            names = list(info.class_names or ())
            if line.get("class") is not None and line["class"] not in names:
                raise ValueError(f"V-pipeline.taps-7: {where}: the class {line['class']!r} is not a name of the class names {names}")
            value.boxes[row] = line["box"]
            value.instance_score[row] = line["score"]
            value.class_index[row] = -1 if line.get("class") is None else names.index(line["class"])
        else:
            points = np.array([np.nan if item is None else item for item in line["keypoints"]], dtype=np.float64)
            if points.size != 3 * len(info.point_names):
                raise ValueError(f"{where}: `keypoints` has {points.size} numbers; the port has {len(info.point_names)} points")
            points = points.reshape(-1, 3)
            value.xy[row] = points[:, :2]
            value.score[row] = points[:, 2]
            value.raw_score[row] = line["raw_score"]
            value.instance_score[row] = line["score"]
        value.present[row] = True

    def value(self, frame_index: int, camera_id: int | str) -> Any:
        """Return the value of the port for one image. An image with no line gives the empty value."""
        found = self.values.get((frame_index, camera_id))
        return self.info.empty() if found is None else found
