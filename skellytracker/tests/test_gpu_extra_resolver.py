"""Tests for hardware-based EP and pyproject extra recommendations."""

from __future__ import annotations

import sys

import pytest

from skellytracker.utilities.gpu_utils.gpu_enumeration import GpuInfo
from skellytracker.utilities.gpu_utils.gpu_extra_resolver import (
  recommend_optimal_execution_provider,
  recommend_rtmpose_extra,
)


@pytest.mark.parametrize(
  ("gpus", "platform", "expected_ep", "expected_extra"),
  [
    ([], "darwin", "coreml", "rtmpose"),
    (
      [GpuInfo(id="win32:0", name="NVIDIA GeForce RTX 4090", vendor="nvidia", vram_bytes=None)],
      "win32",
      "trt-trx",
      "rtmpose-trt-rtx",
    ),
    (
      [GpuInfo(id="win32:0", name="NVIDIA GeForce GTX 1080", vendor="nvidia", vram_bytes=None)],
      "win32",
      "cuda",
      "rtmpose-nvidia",
    ),
    (
      [GpuInfo(id="win32:0", name="AMD Radeon RX 6800", vendor="amd", vram_bytes=None)],
      "win32",
      "directml",
      "rtmpose-directml",
    ),
    (
      [
        GpuInfo(id="win32:0", name="Intel UHD Graphics", vendor="intel", vram_bytes=None),
        GpuInfo(id="win32:1", name="NVIDIA GeForce RTX 3060", vendor="nvidia", vram_bytes=None),
      ],
      "win32",
      "trt-trx",
      "rtmpose-trt-rtx",
    ),
    ([], "linux", "cpu", "rtmpose"),
    (
      [
        GpuInfo(
          id="win32:0",
          name="Intel(R) UHD Graphics 770",
          vendor="intel",
          vram_bytes=None,
          online=False,
        ),
        GpuInfo(
          id="nvidia:0",
          name="NVIDIA GeForce RTX 3070",
          vendor="nvidia",
          vram_bytes=8_000_000_000,
          online=True,
        ),
      ],
      "win32",
      "trt-trx",
      "rtmpose-trt-rtx",
    ),
    (
      [
        GpuInfo(
          id="win32:0",
          name="Intel(R) UHD Graphics 770",
          vendor="intel",
          vram_bytes=None,
          online=False,
        ),
      ],
      "win32",
      "cpu",
      "rtmpose",
    ),
  ],
)
def test_recommend_optimal_and_extra(
  monkeypatch: pytest.MonkeyPatch,
  gpus: list[GpuInfo],
  platform: str,
  expected_ep: str,
  expected_extra: str,
) -> None:
  monkeypatch.setattr(sys, "platform", platform)
  assert recommend_optimal_execution_provider(gpus) == expected_ep
  assert recommend_rtmpose_extra(gpus) == expected_extra
