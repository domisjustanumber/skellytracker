"""The pipeline API: load a pipeline config and run it on the frames of one or more cameras.

    config = load_pipeline("yolox-rtmw-wholebody@skellytracker")
    with start_pipeline(config, camera_ids=[0], running_mode="live", execution_provider="cpu") as run:
        result = run.process(Frame(image, frame_index=0, timestamp_ms=0.0))

The result of a camera has one key for each key of the `outputs` block: `wholebody` and
`holistic` hold a `CanonicalKeypoints` value, and `boxes` holds an `OutputBoxes` value. This
version tracks one person, so read row 0:

    body, boxes = result["wholebody"], result["boxes"]
    if body.present[0]:
        nose_x, nose_y = body.xy[0, body.point_names.index("body/nose")]
    detector_ran = bool(boxes.detector_ran[0])
    x1, y1, x2, y2 = boxes.xyxy[0]                  # NaN when boxes.present[0] is false

A plain import of this package loads no `onnxruntime` and no `mediapipe`.

The names of this API follow the group "Public names" of `skellytracker/AGENTS.md`. These names
are fixed: `list_pipelines`, `get_pipeline`, `load_pipeline`, `check_pipeline` with its result
`PipelineCheck`, `export_pipeline`, `start_pipeline`, `PipelineRun` with `models`, `Frame`,
`annotate`, `to_canonical` with `CanonicalKeypoints.point_names`, `OutputBoxes` with `xyxy` and `detector_ran`,
`PipelineEntry.needs_execution_provider`, and the errors `CallRefusedError`,
`SetParamsRefusedError` and `RunClosedError`. No name has an alias.
"""
from skellytracker.core.errors import CallRefusedError, MissingDependencyError, RunClosedError, SetParamsRefusedError
from skellytracker.core.pipelines.annotate import annotate
from skellytracker.core.pipelines.canonical import CanonicalKeypoints, to_canonical
from skellytracker.core.pipelines.catalog import (
    PipelineEntry,
    PipelineNotFoundError,
    PipelineUnavailableError,
    get_pipeline,
    list_pipelines,
)
from skellytracker.core.pipelines.config import PipelineConfig
from skellytracker.core.pipelines.loading import PipelineCheck, check_pipeline, export_pipeline, load_pipeline
from skellytracker.core.pipelines.nodes import list_node_types
from skellytracker.core.pipelines.run import Frame, PipelineRun, start_pipeline
from skellytracker.core.pipelines.values import InstanceBoxes, InstanceKeypoints, OutputBoxes
from skellytracker.core.pipelines.warnings import PipelineWarning

__all__ = [
    "CallRefusedError",
    "CanonicalKeypoints",
    "Frame",
    "InstanceBoxes",
    "InstanceKeypoints",
    "MissingDependencyError",
    "OutputBoxes",
    "PipelineCheck",
    "PipelineConfig",
    "PipelineEntry",
    "PipelineNotFoundError",
    "PipelineRun",
    "PipelineUnavailableError",
    "PipelineWarning",
    "RunClosedError",
    "SetParamsRefusedError",
    "annotate",
    "check_pipeline",
    "export_pipeline",
    "get_pipeline",
    "list_node_types",
    "list_pipelines",
    "load_pipeline",
    "start_pipeline",
    "to_canonical",
]
