"""The local GPU gate of the hardware and EP API. Run it with `pytest -m gpu` on an NVIDIA host.

The host needs a GPU with compute capability 8.0 or higher, a driver of R580 or later, and the
packs of `skellytracker-eps install` in the EP store. `SKELLYTRACKER_GPU_GATE_MODELS` names a
folder: the test then builds a session on each `*fp16*.onnx` file under it whose name starts with
`yolox-person` or `rtmw-wholebody133`. The frozen part also needs `-m "gpu and pyinstaller"`.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import skellytracker._pyinstaller as entry
from skellytracker.core import eps, metrics
from skellytracker.core.eps import _probe_model

pytestmark = pytest.mark.gpu
PACKS = {"cuda": "CUDAExecutionProvider", "trt-rtx": "NvTensorRTRTXExecutionProvider"}


def fp16_models() -> list[Path]:
    folder = os.environ.get("SKELLYTRACKER_GPU_GATE_MODELS")
    if not folder:
        return []
    return sorted(path for path in Path(folder).rglob("*fp16*.onnx") if path.name.startswith(("yolox-person", "rtmw-wholebody133")))


def test_l3_passes_for_each_pack():
    verdicts = {verdict.ep_key: verdict for verdict in eps.verify(list(PACKS), force=True)}
    assert all(verdict.ok and verdict.level == "L3" for verdict in verdicts.values()), verdicts
    print({key: verdict.max_abs_diff for key, verdict in verdicts.items()})


@pytest.mark.parametrize("key", PACKS)
def test_a_session_runs_on_the_requested_ep_and_on_the_one_gpu(key):
    (device,) = eps.run_devices(key)
    for device_key in (None, device.device_key):
        session, report = eps.build_session(_probe_model.model_bytes(), execution_provider=key, device_key=device_key)
        assert session.get_providers()[0] == PACKS[key]
        assert (report.requested_ep, report.used_ep, report.device_key) == (key, key, device.device_key)
        assert dict(report.nodes_by_ep)[PACKS[key]] >= 1 and report.cpu_nodes == 0 and report.gpu_uuid
    assert metrics.free_vram(device.device_key) > 0


@pytest.mark.parametrize("key", PACKS)
def test_each_fp16_artifact_has_no_cpu_node(key):
    models = fp16_models()
    if not models:
        pytest.skip("SKELLYTRACKER_GPU_GATE_MODELS names no folder with fp16 files")
    placed = {}
    for path in models:
        session, report = eps.build_session(path, execution_provider=key, ep_options=dict(eps.load_catalog().default_options(key, "fp16")))
        del session  # free the VRAM before the next file
        placed[path.name] = (report.cpu_nodes, report.cpu_op_types)
    print(f"{key}: {len(placed)} fp16 files")
    assert {name: value for name, value in placed.items() if value != (0, ())} == {}


@pytest.mark.pyinstaller
def test_a_frozen_app_installs_trt_rtx_in_a_new_store_and_binds_it(tmp_path):
    script = Path(entry.__file__).parent / "tests" / "frozen_gpu_smoke.py"
    build = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--name", "gpusmoke", "--distpath", str(tmp_path / "dist"),
             "--workpath", str(tmp_path / "work"), "--specpath", str(tmp_path), str(script)]
    done = subprocess.run(build, capture_output=True, text=True, check=False, cwd=tmp_path)  # noqa: S603
    assert done.returncode == 0, done.stderr[-3000:]
    app = tmp_path / "dist" / "gpusmoke" / ("gpusmoke.exe" if sys.platform == "win32" else "gpusmoke")
    env = dict(os.environ, SKELLYTRACKER_EP_STORE=str(tmp_path / "s"))  # a short store path: the path guard
    run = subprocess.run([str(app)], capture_output=True, text=True, check=False, cwd=tmp_path, env=env)  # noqa: S603
    assert run.returncode == 0 and "BOUND NvTensorRTRTXExecutionProvider" in run.stdout, (run.stdout[-3000:], run.stderr[-3000:])
