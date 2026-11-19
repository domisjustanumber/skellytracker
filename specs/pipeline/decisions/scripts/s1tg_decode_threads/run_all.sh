#!/bin/sh
# Evidence of ADR-S1TG. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
# One GPU process at a time; a quiet-GPU check before each; a sampler logs other python processes on the GPU and GPU util.
D=$SCRATCH/decode_threads
LOG=$D/results.log
cd $SKELLYTRACKER_CHECKOUT || exit 1
: > $LOG
for a in "--res 720" "--res 1080" "--res 720 --spin"; do
  sh $D/gpu_wait.sh >> $LOG 2>&1 || exit 1
  echo "### $a --iters 200 --rounds 5 $(date +%H:%M:%S)" >> $LOG
  timeout 900 uv run --no-sync python $D/decode_threads.py $a --iters 200 --rounds 5 > $D/run.tmp 2>&1 &
  pid=$!
  while kill -0 $pid 2>/dev/null; do
    gp=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | tr -d ' \r' | sort)
    pp=$(tasklist //FO CSV //NH | grep -i '^"python' | cut -d, -f2 | tr -d '"' | sort)
    u=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | tr -d ' \r')
    echo "$(date +%H:%M:%S) util=$u python-on-gpu=$(comm -12 <(echo "$gp") <(echo "$pp") 2>/dev/null | tr '\n' ' ')" >> $D/sampler.log
    sleep 5
  done
  wait $pid; echo "rc=$?" >> $LOG
  grep -v -e nvjpeg2k -e nvTIFF -e nvtiff -e nvJPEG2000 -e PrimaryCtxRelease $D/run.tmp >> $LOG
done
rm -f $D/run.tmp
echo ALLDONE >> $LOG
