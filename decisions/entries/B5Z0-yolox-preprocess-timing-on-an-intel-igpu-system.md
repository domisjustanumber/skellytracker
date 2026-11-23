# B5Z0 — Timing of the yolox preprocess on a system with an Intel iGPU

**Status:** evidence, 2026-11-21 (measurement of 2026-11-21; PR: pending).

## Decision

The question: does a preprocess on an Intel iGPU, or a different CPU form, make the detector call
shorter or lower the CPU load? All times are ms for one call with 3 cameras of 1280x720, as wall
time / process CPU time. The model is `yolox-person` m, fixed batch 3, fp32.

1. **The preprocess alone, back to back.** Package CPU code 16.6 / 17.7. CPU EP graph 8.6 / 20.9.
   OpenVINO EP on the iGPU 5.5 / 5.3. OpenVINO EP on the CPU 5.9 / 28.6. DirectML on the iGPU
   24.8 / 3.6. The CPU load of the system was 22 to 35 % in this part.
2. **Where the CPU code spent its time.** For one frame, of 4.7 ms: the pad fill 1.6 ms, two casts
   to float32 of 0.9 ms each, the change to CHW layout 1.4 ms. The stack of a batch adds 0.8 ms for
   each frame.
3. **The CPU code after two edits** (the pad values cast before the fill; no second copy in the
   normalization): 3.1 ms for one frame, 12.3 / 14.2 with the stack. The output is equal.
4. **A reused output batch.** A scratch form that writes only the content rows into a batch that
   stays between calls took 1.0 / 2.2, and 0.8 / 2.2 with a pool of 6 threads. Its output is equal
   to the package output. The package does not have this form.
5. **The whole detector call, model on the CPU EP with 10 threads.** Package CPU code
   241.7 / 2013. The form of item 4: 226.5 / 1949. CPU EP graph 239.5 / 1975. OpenVINO graph on the
   CPU 234.5 / 2016. OpenVINO graph on the iGPU 332.8 / 2017: its preprocess part took 110 ms.
6. **OpenVINO on the iGPU after an idle gap.** Back to back, one graph call took 5.6 ms. After a gap
   of 50 or 100 ms, 4 of 30 calls took about 490 ms. In a run on the same day with more system
   load, 13 of 15 calls after a gap of 250 ms took about 460 ms. The cause is not known.
7. **The model alone.** CPU EP 246.7 / 2080. OpenVINO on the iGPU 316.3 / 316, with boxes that
   differ from the CPU EP by at most 0.70 pixel for a score above 0.7. OpenVINO on the CPU
   291.9 / 1795.
8. **The `rtmw` preprocess** (affine crop): the package CPU code was the fastest path, 2.2 / 3.0,
   against 5.4 or more for each graph path. On OpenVINO on the iGPU, its output differed from the
   CPU code by 0.19 of the normalized value. The cause is not known.
9. **DirectML on the iGPU ran on the iGPU.** The GPU engine counters of Windows showed load only on
   the adapter of the UHD 770 for each row of that path.

## Evidence

- One Windows 11 system: Intel Core i7-14700K, Intel UHD 770, ONNX Runtime 1.30.0, OpenCV 5.1.0,
  numpy 2.5.5, the OpenVINO EP package of the Windows ML catalog, version 2.1080.97.0. Each GPU
  session ran on the UHD 770. An RTX 3070 was in the system and ran no session.
- Items 3 to 7: the CPU load of the system was 12.8 % before and 12.0 % after the run. The system
  was not quiet: in that time an other session ran a test suite on all cores for 6 to 7 minutes,
  with a start and an end that are not known. Its tests can open short DirectML sessions, so the
  UHD 770 was possibly not free. No number of this entry is from a quiet system. Items 1, 2 and 8 come from earlier runs of the same
  day on a system with more load.
- Items 1 to 4: first call, 10 warm-up calls, then 3 runs of 100 calls (item 2: 1000 repeats). The
  time is the median. The frames are the 30 test frames of the package. The process CPU clock of
  Windows has steps of 15.6 ms, so a CPU time below 2 ms is approximate.
- Items 5 and 7: 3 runs of 20 calls, the candidates in turn in one process.
- The sessions of the OpenVINO EP were built by hand: the package has no OpenVINO path.
- The scripts are scratch scripts (not in git).

## Open work

- The package does not have the reused output batch of item 4. It needs a state for each camera in
  the runner.
- No run on a system with only an Intel iGPU, and no run on Linux.
