#!/usr/bin/env bash
# Evidence of ADR-975Z. This scratch script ran on 2026-11-17. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
# One bounded hang2.py run. Appends a result row to hang2_matrix.txt. Args go to hang2.py.
# V130=1: run under onnxruntime 1.30.0 (hang_study/ort130 + ort130_shim.py).
H=$SCRATCH/hang_study
HW=$(cygpath -w "$H")
cd $SKELLYTRACKER_CHECKOUT || exit 2
if [ "${V130:-0}" = 1 ]; then
  export PYTHONPATH="$SKELLYTRACKER_CHECKOUT_W"
  CMD=("$H/ort130/Scripts/python.exe" -B "$HW\\ort130_shim.py" "$HW\\hang2.py"); TAG=v130
else
  CMD=(uv run --no-sync python -B "$H/hang2.py"); TAG=v131
fi
t0=$(date +%s%N)
timeout -k 10 60 "${CMD[@]}" --watchdog "${WD:-12}" "$@" > "$H/h2_tmp.log" 2>&1
e=$?
d=$(( ($(date +%s%N) - t0) / 1000000 ))
if grep -aq "Timeout (" "$H/h2_tmp.log"; then res=HANG; elif grep -aq "main done" "$H/h2_tmp.log"; then res=ok; else res=ERR; fi
echo "$TAG $res exit=$e ms=$d ctxrel=$(grep -ac PrimaryCtx "$H/h2_tmp.log") :: $*" | tee -a "$H/hang2_matrix.txt"
