#!/usr/bin/env bash
# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
# Stage 1: the exact hung configuration, as the S8 driver ran it (uv run --no-sync python measure.py ..., stdout+stderr to a file).
cd "$SCRATCH/exit_hang" || exit 2
LOOP=(uv run --no-sync --project $SKELLYTRACKER_CHECKOUT python -I "$SCRATCH_W\exit_hang\loop.py")
"${LOOP[@]}" --runs 100 --timeout 180 --gpu-wait --label S1_exact_cuda_M1_1080x6 -- uv run --no-sync python "$SCRATCH_W\exit_hang\measure.py" --ep cuda --mode M1 --res 1080 --cams 6 --tag EH_exact
echo stage1 done
