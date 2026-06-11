"""Tests for hardware-based optimal EP recommendations (Feature 3)."""

from __future__ import annotations

import sys

import pytest

from skellytracker.utilities.gpu_utils.gpu_enumeration import GpuInfo
from skellytracker.utilities.gpu_utils.gpu_extra_resolver import recommend_optimal_execution_provider


@pytest.mark.parametrize(
  ("gpus", "platform", "expected_ep"),
  [
    ([], "darwin", "coreml"),
    (
      [GpuInfo(id="win32:0", name="NVIDIA GeForce RTX 4090", vendor="nvidia", vram_bytes=None)],
      "win32",
      "trt-trx",
    ),
    (
      [GpuInfo(id="win32:0", name="NVIDIA GeForce GTX 1080", vendor="nvidia", vram_bytes=None)],
      "win32",
      "cuda",
    ),
    (
      [GpuInfo(id="win32:0", name="AMD Radeon RX 6800", vendor="amd", vram_bytes=None)],
      "win32",
      "directml",
    ),
    (
      [
        GpuInfo(id="win32:0", name="Intel UHD Graphics", vendor="intel", vram_bytes=None),
        GpuInfo(id="win32:1", name="NVIDIA GeForce RTX 3060", vendor="nvidia", vram_bytes=None),
      ],
      "win32",
      "trt-trx",
    ),
    ([], "linux", "cpu"),
  ],
)
def test_recommend_optimal_execution_provider(
  monkeypatch: pytest.MonkeyPatch,
  gpus: list[GpuInfo],
  platform: str,
  expected_ep: str,
) -> None:
  monkeypatch.setattr(sys, "platform", platform)
  assert recommend_optimal_execution_provider(gpus) == expected_ep
