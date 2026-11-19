#!/usr/bin/env bash
# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
# Stage 2: one factor at a time, short runs (20 measured calls) for more exits per minute. Usage: stage2.sh [steps...]
cd "$SCRATCH/exit_hang" || exit 2
LOOP=(uv run --no-sync --project "$LOOP_CWD" python -I "$SCRATCH_W\exit_hang\loop.py")
WRAP=(uv run --no-sync python "$SCRATCH_W\exit_hang\wrap.py")
MINI=(uv run --no-sync python "$SCRATCH_W\exit_hang\mini.py")
SHORT=(--calls 20 --warmup 2)
: "${LOOP_CWD:?set LOOP_CWD to the project folder of the children}"
# Stage 3: the full-length run (300 measured calls, as the exact config): wrapper normal vs unregister vs terminate; more exact runs.
for s in $*; do
  case $s in
  i) "${LOOP[@]}" --runs ${N:-40} --timeout 150 --gpu-wait --label S3i_wrap_normal_full --env EXIT_MODE=normal EXIT_DUMP_S=60 -- "${WRAP[@]}" --ep cuda --mode M1 --res 1080 --cams 6 --tag EH_s3 ;;
  j) "${LOOP[@]}" --runs ${N:-60} --timeout 150 --gpu-wait --label S3j_wrap_unreg_full --env EXIT_MODE=unreg EXIT_DUMP_S=60 -- "${WRAP[@]}" --ep cuda --mode M1 --res 1080 --cams 6 --tag EH_s3 ;;
  k) "${LOOP[@]}" --runs ${N:-40} --timeout 150 --gpu-wait --label S3k_exact_more -- uv run --no-sync python "$(cygpath -w "$PWD")\measure.py" --ep cuda --mode M1 --res 1080 --cams 6 --tag EH_exact ;;
  l) "${LOOP[@]}" --runs ${N:-60} --timeout 150 --gpu-wait --label S3l_wrap_terminate_full --env EXIT_MODE=terminate EXIT_DUMP_S=60 -- "${WRAP[@]}" --ep cuda --mode M1 --res 1080 --cams 6 --tag EH_s3 ;;
  B) "${LOOP[@]}" --runs ${N:-40} --timeout 150 --gpu-wait --label B_new_exact_cuda_M1_1080x6 -- uv run --no-sync python "$(cygpath -w "$PWD")\measure.py" --ep cuda --mode M1 --res 1080 --cams 6 --tag EH_B ;;
  Bw) "${LOOP[@]}" --runs 1 --timeout 150 --gpu-wait --label B_new_wrap_versions --env EXIT_MODE=normal -- "${WRAP[@]}" --ep cuda --mode M1 --res 1080 --cams 6 --calls 20 --warmup 2 --tag EH_Bw ;;
  esac
done
echo stage3 done
