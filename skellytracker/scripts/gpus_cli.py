"""CLI to list GPUs and install the matching RTMPose ONNX Runtime extra via uv."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from skellytracker.utilities.gpu_utils import (
  list_execution_providers,
  list_installed_gpus,
  recommend_rtmpose_extra,
)
from skellytracker.utilities.gpu_utils.extra_install import build_install_plan
from skellytracker.utilities.gpu_utils.pyproject_cuda_requirements import CudaVersion

_RTMPose_CONFLICT_EXTRAS = frozenset({
  "rtmpose",
  "rtmpose-nvidia",
  "rtmpose-trt",
  "rtmpose-trt-rtx",
  "rtmpose-directml",
  "recommended",
})


def _format_vram(vram_bytes: int | None) -> str:
  if vram_bytes is None:
    return "unknown"
  gib = vram_bytes / (1024 ** 3)
  return f"{gib:.1f} GiB"


def _format_cuda(version: CudaVersion | None) -> str:
  if version is None:
    return "unknown"
  return f"{version[0]}.{version[1]}"


def _print_gpu_report() -> tuple[str, str | None]:
  gpus = list_installed_gpus()
  if not gpus:
    print("No physical GPUs detected.")
  else:
    for gpu in gpus:
      details = [
        f"GPU {gpu.id}: {gpu.name}",
        f"vendor={gpu.vendor}",
        f"vram={_format_vram(gpu.vram_bytes)}",
        f"online={'true' if gpu.online else 'false'}",
      ]
      if gpu.driver_version is not None:
        details.append(f"driver={gpu.driver_version}")
      if gpu.cuda_driver_max is not None:
        details.append(f"cuda_max={_format_cuda(gpu.cuda_driver_max)}")
      if gpu.cuda_required_min is not None:
        details.append(f"cuda_required>={_format_cuda(gpu.cuda_required_min)}")
      print(", ".join(details))
      if gpu.cuda_meets_nvidia_eps is False:
        print(
          f"WARNING: NVIDIA driver CUDA max {_format_cuda(gpu.cuda_driver_max)} is below "
          f"required {_format_cuda(gpu.cuda_required_min)} for RTMPose NVIDIA extras. "
          "Update drivers: https://www.nvidia.com/drivers",
          file=sys.stderr,
        )

  ep_info = list_execution_providers()
  optimal = ep_info.optimal_provider_id
  installed_best = ep_info.recommended_provider_id
  print(f"Optimal EP: {optimal}")
  print(f"Installed best EP: {installed_best}")

  by_id = {provider.id: provider for provider in ep_info.providers}
  optimal_ep = by_id.get(optimal or "")
  if optimal_ep is not None and optimal_ep.driver_cuda_compatible is False:
    print(
      f"WARNING: Installed NVIDIA driver does not meet CUDA requirements for optimal EP {optimal!r}.",
      file=sys.stderr,
    )

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
    help="Install the GPU-optimal pyproject extra (dev repo: uv sync; venv: uv/pip install).",
  )
  parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Print the planned install command without executing it.",
  )
  parser.add_argument(
    "--extra",
    help="Override auto-detected pyproject extra.",
  )
  args = parser.parse_args(argv)

  extra, install_hint = _print_gpu_report()
  if args.extra is not None:
    extra = args.extra

  if not args.install:
    return 0

  if install_hint is None and args.extra is None:
    print("Optimal execution provider packages are already installed.")
    return 0

  if extra not in _RTMPose_CONFLICT_EXTRAS:
    print(f"Unknown extra {extra!r}. Valid extras: {sorted(_RTMPose_CONFLICT_EXTRAS)}", file=sys.stderr)
    return 1

  plan = build_install_plan(extra)
  print(f"Running: {' '.join(plan.command)} ({plan.description})")
  if args.dry_run:
    return 0

  result = subprocess.run(plan.command, cwd=plan.cwd, check=False)  # noqa: S603
  if result.returncode != 0:
    return result.returncode

  print(f"Install completed with extra={extra!r}.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
