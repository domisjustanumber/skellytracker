"""The generic detectors: an ONNX model of the sidecar spec runs from its sidecar, with no code of its own.

    detector = create_detector("yolox-person@openmmlab-exporter", execution_provider="cpu")
    detections = detector.detect([frame])

`create_detector` goes from a catalog key to a detector with its session. `open_session` builds
the session alone, also at an other batch than the batch of the artifact.
"""
from skellytracker.core.detectors.generic.batch_conversion import model_batch_convert
from skellytracker.core.detectors.generic.download import ArtifactDownloadError, download_artifact
from skellytracker.core.detectors.generic.keypoint_detector import GenericKeypointDetector, KeypointDetections
from skellytracker.core.detectors.generic.object_detector import GenericObjectDetector, ObjectDetections
from skellytracker.core.detectors.generic.overlay import OverlayGroup, overlay_edges, overlay_groups
from skellytracker.core.detectors.generic.session import create_detector, ensure_artifact, open_session

__all__ = [
    "ArtifactDownloadError",
    "GenericKeypointDetector",
    "GenericObjectDetector",
    "KeypointDetections",
    "ObjectDetections",
    "OverlayGroup",
    "create_detector",
    "download_artifact",
    "ensure_artifact",
    "model_batch_convert",
    "open_session",
    "overlay_edges",
    "overlay_groups",
]
