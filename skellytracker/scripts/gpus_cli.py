"""CLI to list GPUs and install the matching RTMPose ONNX Runtime extra via uv."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from skellytracker.utilities.gpu_utils import (
  list_execution_providers,
  list_installed_gpus,
  recommend_rtmpose_extra,
)

_RTMPose_CONFLICT_EXTRAS = frozenset({
  "rtmpose",
  "rtmpose-nvidia",
  "rtmpose-trt",
  "rtmpose-trt-rtx",
  "rtmpose-directml",
  "recommended",
})


def _find_project_root(start: Path) -> Path | None:
  for directory in [start, *start.parents]:
    pyproject = directory / "pyproject.toml"
    if not pyproject.is_file():
      continue
    try:
      data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
      continue
    if data.get("project", {}).get("name") == "skellytracker":
      return directory
  return None


def _format_vram(vram_bytes: int | None) -> str:
  if vram_bytes is None:
    return "unknown"
  gib = vram_bytes / (1024 ** 3)
  return f"{gib:.1f} GiB"


def _print_gpu_report() -> tuple[str, str | None]:
  gpus = list_installed_gpus()
  if not gpus:
    print("No physical GPUs detected.")
  else:
    for gpu in gpus:
      print(
        f"GPU {gpu.id}: {gpu.name} "
        f"(vendor={gpu.vendor}, vram={_format_vram(gpu.vram_bytes)})"
      )

  ep_info = list_execution_providers()
  optimal = ep_info.optimal_provider_id
  installed_best = ep_info.recommended_provider_id
  print(f"Optimal EP: {optimal}")
  print(f"Installed best EP: {installed_best}")

  install_hint: str | None = None
  if ep_info.install_recommended_provider_id is not None:
    extra = recommend_rtmpose_extra(gpus)
    install_hint = extra
    print(
      f"Install for best results: {ep_info.install_recommended_provider_id} "
      f"(pyproject extra: {extra})"
    )
    print("Run: skellytracker-gpus --install")

  return recommend_rtmpose_extra(gpus), install_hint


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="List GPUs and RTMPose EP guidance.")
  parser.add_argument(
    "--install",
    action="store_true",
    help="Run uv sync --extra for the GPU-optimal pyproject extra.",
  )
  parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Print the planned uv command without executing it.",
  )
  parser.add_argument(
    "--extra",
    help="Override auto-detected pyproject extra.",
  )
  args = parser.parse_args(argv)

  extra, _ = _print_gpu_report()
  if args.extra is not None:
    extra = args.extra

  if not args.install:
    return 0

  if extra not in _RTMPose_CONFLICT_EXTRAS:
    print(f"Unknown extra {extra!r}. Valid extras: {sorted(_RTMPose_CONFLICT_EXTRAS)}", file=sys.stderr)
    return 1

  project_root = _find_project_root(Path.cwd())
  if project_root is None:
    print(
      "Could not find skellytracker pyproject.toml in the current directory tree. "
      'Install from PyPI with: pip install "skellytracker[rtmpose-nvidia]"',
      file=sys.stderr,
    )
    return 1

  uv_path = shutil.which("uv")
  if uv_path is None:
    print(
      "uv is not on PATH. Install it from https://docs.astral.sh/uv/ "
      'or use pip install "skellytracker[rtmpose-nvidia]".',
      file=sys.stderr,
    )
    return 1

  command = [uv_path, "sync", "--extra", extra]
  print(f"Running: {' '.join(command)} (in {project_root})")
  if args.dry_run:
    return 0

  result = subprocess.run(command, cwd=project_root, check=False)  # noqa: S603
  if result.returncode != 0:
    return result.returncode

  print(f"uv sync completed with extra={extra!r}.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
