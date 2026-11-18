#!/usr/bin/env bash
# The Linux gate of the change to ONNX Runtime 1.30.0: the CUDA pack and the TRT-RTX pack on bare-metal
# Ubuntu 24.04 with an NVIDIA driver of 590.48.01 or later. WSL2 is not a valid host for this gate.
#
# Usage: bash linux_ep_gate.sh SOURCE_TREE [WORK_DIR]
#
# SOURCE_TREE is the skellytracker working tree with its ONNX files in `core/model_zoo/`, for example on
# the mounted Windows drive. The script only reads it. It copies the tree to WORK_DIR (default:
# ~/skellytracker-linux-gate), and it puts the environment, the EP store and the results there.
# Each step writes a log to WORK_DIR/results. A failed step does not stop the next steps.
# The last line gives the result. Bring back the folder WORK_DIR/results.
set -uo pipefail

SRC=$(realpath "${1:?give the path of the skellytracker working tree}")
WORK=${2:-$HOME/skellytracker-linux-gate}
OUT=$WORK/results
TREE=$WORK/tree
mkdir -p "$OUT"
: > "$OUT/summary.txt"

for tool in uv nvidia-smi rsync; do
    command -v "$tool" > /dev/null || { echo "STOP: $tool is not installed"; exit 2; }
done
if grep -qi microsoft /proc/version; then
    echo "STOP: this host is WSL. The gate needs bare-metal Linux."; exit 2
fi
driver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -n 1)
if [ "$(printf '%s\n' 590.48.01 "$driver" | sort -V | head -n 1)" != 590.48.01 ]; then
    echo "STOP: the NVIDIA driver is $driver. The gate needs 590.48.01 or later."; exit 2
fi
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader > "$OUT/gpu.txt"
grep PRETTY_NAME /etc/os-release >> "$OUT/gpu.txt"

rsync -a --delete --exclude .venv --exclude .git --exclude graphify-out --exclude intakes --exclude plans \
    --exclude __pycache__ --exclude .pytest_cache "$SRC/" "$TREE/" || { echo "STOP: the copy failed"; exit 2; }
cd "$TREE" || exit 2
export SKELLYTRACKER_EP_STORE=$WORK/store
export SKELLYTRACKER_GPU_GATE_MODELS=$TREE/skellytracker/core/model_zoo

failed=0
step() {  # step NAME COMMAND...
    local name=$1; shift
    echo "== $name"
    if "$@" > "$OUT/$name.log" 2>&1; then
        echo "PASS $name" | tee -a "$OUT/summary.txt"
    else
        echo "FAIL $name (see $OUT/$name.log)" | tee -a "$OUT/summary.txt"; failed=1
    fi
}

cat > "$OUT/loaded_libraries.py" <<'EOF'
"""Run two fp16 models on one EP, then print the CUDA and TensorRT libraries of this process."""
import sys
from pathlib import Path

import numpy as np

from skellytracker.core import eps

key, root = sys.argv[1], Path(sys.argv[2])
kinds = {"tensor(float)": np.float32, "tensor(float16)": np.float16, "tensor(uint8)": np.uint8}
for name in ("yolox-person-m_b3_fp16.onnx", "rtmw-wholebody133-m_b3_fp16.onnx"):
    (path,) = root.rglob(name)
    session, report = eps.build_session(path, execution_provider=key, ep_options=dict(eps.load_catalog().default_options(key, "fp16")))
    feed = {i.name: np.zeros([d if isinstance(d, int) else 1 for d in i.shape], kinds[i.type]) for i in session.get_inputs()}
    outputs = session.run(None, feed)
    print(key, name, "cpu_nodes", report.cpu_nodes, "nan", int(sum(np.isnan(o).sum() for o in outputs if o.dtype.kind == "f")))
    del session
marks = ("nvrtc", "cudart", "cublas", "cudnn", "tensorrt", "onnxruntime")
maps = Path("/proc/self/maps").read_text(encoding="utf-8", errors="replace").splitlines()
loaded = sorted({line.rsplit("/", 1)[-1] for line in maps if "/" in line and any(mark in line.rsplit("/", 1)[-1] for mark in marks)})
print(key, "loaded:", loaded)
print(key, "nvrtc loaded:", [name for name in loaded if "nvrtc" in name])
EOF

step 01-sync uv sync --all-extras --locked
step 02-catalog-check uv run python tools/ep_catalog.py --check
step 03-status-before uv run skellytracker-eps status --json
step 04-install uv run skellytracker-eps install cuda trt-rtx --yes
step 05-verify uv run skellytracker-eps verify --all --force
step 06-gpu-gate uv run pytest -m gpu -s skellytracker/tests/test_eps_gpu_gate.py
step 07-libraries-cuda uv run python "$OUT/loaded_libraries.py" cuda "$SKELLYTRACKER_GPU_GATE_MODELS"
step 08-libraries-trt-rtx uv run python "$OUT/loaded_libraries.py" trt-rtx "$SKELLYTRACKER_GPU_GATE_MODELS"
step 09-status-after uv run skellytracker-eps status --json
step 10-cpu-tests uv run pytest tools/tests/test_ep_catalog.py tools/tests/test_dependency_pins.py \
    skellytracker/tests/test_eps_cli.py skellytracker/tests/test_eps_store.py skellytracker/tests/test_eps_session.py \
    skellytracker/tests/test_system_runtime.py

if [ "$failed" = 0 ]; then echo "RESULT: PASS. Bring back $OUT"; else echo "RESULT: FAIL. Bring back $OUT"; fi
exit "$failed"
