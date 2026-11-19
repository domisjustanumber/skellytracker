#!/bin/sh
# Evidence of ADR-S1TG. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
# Wait (up to 15 min) for a quiet GPU: no python process on it and utilization <= 30 % over 10 samples of 1 s.
for attempt in $(seq 1 60); do
  gpu_pids=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | tr -d ' \r')
  py_pids=$(tasklist //FO CSV //NH | grep -i '^"python' | cut -d, -f2 | tr -d '"')
  busy_py=""
  for p in $gpu_pids; do for q in $py_pids; do [ "$p" = "$q" ] && busy_py="$busy_py $p"; done; done
  peak=0
  for i in $(seq 1 10); do
    u=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | tr -d ' \r')
    [ "$u" -gt "$peak" ] && peak=$u
    sleep 1
  done
  echo "gpu check $(date +%H:%M:%S): python on GPU=[${busy_py# }] peak util=${peak}% (10 s)"
  if [ -z "$busy_py" ] && [ "$peak" -le 30 ]; then exit 0; fi
  sleep 5
done
echo "NO QUIET GPU after 15 min"
exit 1
