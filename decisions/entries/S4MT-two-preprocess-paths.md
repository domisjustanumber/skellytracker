# S4MT — Two preprocess paths stay; the CPU path uses a reused batch

**Status:** absorbed into [Running: Behaviour](../../specs/pipeline/running.md#behaviour), [Package: Layout](../../skellytracker/AGENTS.md#layout), [`pre/preprocess.py`](../../skellytracker/core/detectors/processing/pre/preprocess.py), [`core/detectors/generic/__init__.py`](../../skellytracker/core/detectors/generic/__init__.py), [`core/decode/certification.py`](../../skellytracker/core/decode/certification.py), 2026-11-23 (absorb pass of 2026-11-23; PR: pending). It was `accepted` from 2026-11-23 (PR: pending).

## Decision

1. **Two paths.** The package keeps two preprocess paths: the preprocess graph and the CPU code.
2. **The graph path.** By default, a run must use the preprocess graph only when the frame is a JPEG
   buffer, the GPU is an NVIDIA GPU and the EP is `cuda` or `trt-rtx`. This also applies to the
   classic TensorRT EP, if the EP catalog gets it.
3. **The CPU path.** Each other case uses the CPU JPEG decode and the CPU preprocess. A decoded
   array on `cuda` or `trt-rtx` is such a case.
4. **`directml` keeps its opt-in.** The preprocess place `gpu` still runs the graph on `directml`,
   so that a certify run on an AMD GPU can measure it. A reviewed report can add `directml` on AMD
   hardware to the default later.
5. **The reused batch.** The CPU preprocess of the generic detectors is `BatchPreprocessor` of
   `core/detectors/processing/pre/preprocess.py`. It writes the tensors of the images of a call into
   one batch array that the next call uses again. Its output must be equal, byte for byte, to
   `np.stack` over `preprocess_image`. `preprocess_image` stays as the reference of its tests.
6. **One call at a time.** A generic detector holds a lock from its preprocess to the end of its
   model run. Two `detect` calls on one detector object run one after the other.
7. **The AMD timing.** The check `pipeline_amd_ep.gpu_vs_cpu_preprocess` of the JPEG certification
   also records the median of each span of its two runs, as `gpu.<span>_ms` and `cpu.<span>_ms`.

## Reason

- The user decided items 1 to 4 on 2026-11-23: "JPEG is going to be a very (if not the most) common
  form of input, so unfortunately I think we're going to need two separate preprocessor paths". The
  user also wants a certify run on an AMD system to show if the graph is faster there with
  DirectML.
- The numbers are in [ADR-4JFP](4JFP-preprocess-paths-timing.md). With JPEG input
  on `trt-rtx`, the graph path was 3.5 to 9.1 ms faster for one call. With arrays, the reused batch
  with an upload was equal to the graph within 1.3 ms for the two package models. On the CPU, the
  reused batch was faster than each graph for each resize method.
- Item 6: the batch array of a detector has one owner at a time. A pipeline run already makes one
  call at a time. The user confirmed the lock on 2026-11-23: the goal is to use only the pipeline
  for processing, and a pipeline gives one set of images at a time.

## Consequences

- Items 2 and 3 are not built. Today, the preprocess place `auto` uses the graph on `cuda` and
  `trt-rtx` also for a decoded array
  ([ADR-W4NW](W4NW-gpu-preprocess-of-a-model-node-and-its-cpu-warning.md) item 1). The change needs
  a change of the pipeline spec.
- For the resize methods `stretch`, `fit` and `none`, the graph on `trt-rtx` was 2 to 6 times faster
  than the reused batch. With item 3, a decoded array of a model with such a method uses the slower
  path. No package model uses these methods.
- A caller that keeps the batch array of a `BatchPreprocessor` after its model call must copy it.
- A report of the check of item 7 from before the reused batch and a report from after it do not
  compare: the CPU side became faster.

## Open work

- Build items 2 and 3, with the change of the pipeline spec.
- Measure JPEG input on `cuda` and `trt-rtx` with the CPU decode and the reused batch against the
  GPU path. The measured `cpu` rows of ADR-4JFP item 5 used the CPU code before the reused batch.
- No real run of the check of item 7 on an AMD GPU.
