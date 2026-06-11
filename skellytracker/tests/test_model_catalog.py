"""Tests for @catalog_model registry and list APIs."""

from __future__ import annotations

import skellytracker.utilities.gpu_utils as gpu_utils
from skellytracker.trackers.rtmpose_tracker.rtmpose_session import WHOLEBODY_MODE_CONFIG
from skellytracker.utilities.gpu_utils.model_registry import (
  MODEL_CATALOG,
  MODEL_REGISTRY,
  ModelSpec,
  _CATALOG_META_ATTR,
  list_detection_models,
  list_pose_models,
)

_EXPECTED_IDS = {
  "yolox-tiny",
  "yolox-m",
  "rtmw-l-m_256x192",
  "rtmw-x-l_256x192",
  "rtmw-x-l_384x288",
  "rtmo-s",
  "rtmo-m",
  "rtmo-l",
  "rtmpose-hand",
  "rtmpose-face",
}


def test_model_registry_size_and_ids() -> None:
  assert set(MODEL_REGISTRY) == _EXPECTED_IDS
  assert MODEL_CATALOG.keys() == MODEL_REGISTRY.keys()
  assert len(MODEL_REGISTRY) == 10


def test_catalog_decorator_metadata_on_rtmo_light() -> None:
  assert getattr(ModelSpec.rtmo_light.__func__, _CATALOG_META_ATTR) is not None
  assert MODEL_REGISTRY["rtmo-s"].display_name == "RTMO-S"


def test_mediapipe_factories_not_catalogued() -> None:
  mediapipe_ids = {
    "mediapipe-hand-landmark",
    "mediapipe-pose-landmark",
    "mediapipe-palm-detector",
    "mediapipe-face-detector-short",
    "mediapipe-face-landmark",
  }
  assert mediapipe_ids.isdisjoint(MODEL_REGISTRY.keys())


def test_wholebody_mode_config_sync_with_catalog() -> None:
  for mode in ("performance", "lightweight", "balanced"):
    det_id, det_size, pose_id, pose_size = WHOLEBODY_MODE_CONFIG[mode]
    det_entry = MODEL_CATALOG[det_id]
    pose_entry = MODEL_CATALOG[pose_id]
    assert det_entry.role == "detector"
    assert pose_entry.role == "pose"
    assert det_entry.input_size == det_size
    assert pose_entry.input_size == pose_size


def test_list_functions_and_gpu_utils_import() -> None:
  detectors = list_detection_models()
  assert len(detectors) >= 2
  assert all(entry.role == "detector" for entry in detectors)

  pose_models = list_pose_models()
  rtmw = [m for m in pose_models if m.id.startswith("rtmw-")]
  assert len(rtmw) == 3
  assert any(m.id == "rtmo-s" and not m.requires_detector for m in pose_models)
  assert any(m.id == "rtmpose-hand" and m.requires_detector for m in pose_models)

  assert len(gpu_utils.list_detection_models()) >= 2
  assert len(gpu_utils.MODEL_REGISTRY) == 10
