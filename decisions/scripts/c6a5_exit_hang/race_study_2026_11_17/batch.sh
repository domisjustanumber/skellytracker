#!/usr/bin/env bash
# Evidence of ADR-C6A5. This scratch script ran on 2026-11-17. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
# usage: batch.sh v131|v130 [stages...]   stages: A B C T R (default: B C T R)
# Every child run is bounded by loop.py (deadline per run) and by the outer timeout of the caller.
TAG=$1; shift
STAGES=${*:-B C T R}
H=$SCRATCH/hang_study
HW=$(cygpath -w "$H")
PH="$TEST_PHOTO"
ZOO=../skellytracker/skellytracker/core/model_zoo/detectors
WT="$SKELLYTRACKER_CHECKOUT_W"
LOOP=(uv run --no-project python -I "$HW\\loop.py")
if [ "$TAG" = v130 ]; then
  PYC=("$HW\\ort130\\Scripts\\python.exe" -B "$HW\\ort130_shim.py")
  ENV=(--env "PYTHONPATH=$WT")
else
  PYC=("$WT\\.venv\\Scripts\\python.exe" -B)
  ENV=(--env "HANG_STUDY=1")
fi
OUT="$HW\\rows_$TAG.txt"
RACE=("$HW\\race_wrap.py" --model-root $ZOO --photo "$PH" --wait 100 --no-wait 30 --watchdog 120)
cd "$H" || exit 2
for s in $STAGES; do
  case $s in
  A) "${LOOP[@]}" --runs 40 --timeout 150 --label "${TAG}_A_alone" --out "$OUT" "${ENV[@]}" -- "${PYC[@]}" "${RACE[@]}" --ep cuda ;;
  B)
    rm -f "$H/stop_load"
    "${LOOP[@]}" --runs 200 --timeout 240 --label "${TAG}_B_load" --out "$OUT" --stop-file "$HW\\stop_load" "${ENV[@]}" -- "${PYC[@]}" "${RACE[@]}" --ep cuda trt-rtx &
    LP=$!
    "${LOOP[@]}" --runs 40 --timeout 150 --label "${TAG}_B_withload" --out "$OUT" "${ENV[@]}" -- "${PYC[@]}" "${RACE[@]}" --ep cuda
    touch "$H/stop_load"
    wait $LP
    ;;
  C)
    "${LOOP[@]}" --runs 20 --timeout 150 --label "${TAG}_C_pipe" --stdout pipe --out "$OUT" "${ENV[@]}" -- "${PYC[@]}" "${RACE[@]}" --ep cuda
    "${LOOP[@]}" --runs 3 --timeout 90 --label "${TAG}_C_pipe_pad64k" --stdout pipe --out "$OUT" "${ENV[@]}" PAD_KB=64 -- "${PYC[@]}" "${RACE[@]}" --ep cuda
    "${LOOP[@]}" --runs 3 --timeout 90 --label "${TAG}_C_pipe_pad3k" --stdout pipe --out "$OUT" "${ENV[@]}" PAD_KB=3 -- "${PYC[@]}" "${RACE[@]}" --ep cuda
    ;;
  T)
    for cfg in "interp" "interp --gc" "fwd" "fwd --gc" "rev" "rev --gc" "osexit"; do
      lab=$(echo "$cfg" | tr -d ' -')
      # shellcheck disable=SC2086
      "${LOOP[@]}" --runs 20 --timeout 150 --label "${TAG}_T_$lab" --out "$OUT" "${ENV[@]}" -- "${PYC[@]}" "$HW\\race_teardown.py" --order $cfg --iters 30 --photo "$PH"
    done
    ;;
  R) "${LOOP[@]}" --runs 20 --timeout 200 --label "${TAG}_R_trt_interp" --out "$OUT" "${ENV[@]}" -- "${PYC[@]}" "$HW\\race_teardown.py" --order interp --ep trt-rtx --iters 30 --photo "$PH" ;;
  esac
done
echo "batch $TAG done"
