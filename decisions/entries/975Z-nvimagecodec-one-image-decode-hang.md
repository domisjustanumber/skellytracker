# 975Z — nvImageCodec never returns from a decode of one image with fewer CUDA streams than threads

**Status:** evidence, 2026-11-19 (measurements of 2026-11-17 and 2026-11-19; PR: pending).

## Decision

1. **The hang.** nvImageCodec 0.10.0.9 never returns from `Decoder.decode()` of exactly one image
   when the decoder has fewer CUDA streams than worker threads. A batch of 2 or more images
   returns. The waiting thread is in `nvimgcodecFutureWaitForAll` and `Cnd_wait`, and the process
   uses no CPU (`stacks.txt`).
2. **The matrix of 2026-11-19.** 62 cells of threads (1, 2, 3, 4, 7 and 8), streams and images (1
   or 2): 19 cells hang and 43 return. Each cell that hangs has 1 image and fewer streams than
   threads. Each other cell returns. A stream count above the thread count gives a warning, and
   the library uses the thread count.
3. **More runs (9).** Without the option `num_cuda_streams`, or with a value out of range, the
   library uses `NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS`. With the value 1 and 2 or 4 threads, one
   image hangs. One image also hangs after 3 batches of 2 images (4 threads, 1 stream). A JPEG
   with no DHT segment also hangs with fewer streams than threads. This was a wrong prediction: the
   expectation was that the decoder refuses such a JPEG and returns. With equal counts, it returns
   a refusal.
4. **The matrix of 2026-11-17.** An earlier script gave the same pattern on ONNX Runtime 1.31.1
   and 1.30.0, also after a model session on `cuda` or `trt-rtx`. The ONNX Runtime version and a
   session do not change the hang.
5. **The mechanism.** This is a reading of the upstream source, not a measurement
   ([`src/image_generic_codec.h`](https://github.com/NVIDIA/nvImageCodec/blob/66a43a0f88de8896392e58b2027ea6e8cf4b7a25/src/image_generic_codec.h)
   at the tag v0.10.1): the threads that share a stream wait at a barrier, and one image wakes only
   one thread. The same reading finds the same code in 0.8.0 to 0.10.1.12.
6. **The workaround.** On this branch, the decoder sets the thread count and the stream count to
   the same value, at most 8 and at most the CPU count minus 1. It removes the environment variable
   before it makes the decoder. At the open, it decodes one test JPEG in a separate thread and
   waits at most 10 s (`skellytracker/core/decode/nvidia.py`;
   [ADR-88ZB](88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md);
   [Running](../../specs/pipeline/running.md#implementer-guidance)).
7. **The self-test.** With the library decoder forced to 2 threads and 1 stream, the open gives no
   decoder after 10.01 s and logs a warning. The process with the abandoned decoder exits with code
   0 in 7 of 7 runs: 4 plain runs, 2 runs with a model session on `cuda` first, and 1 run with the
   environment variable set again at the decoder create. The test decode costs about 12 ms at the
   open (4.2 to 4.3 ms without it, 15.9 to 17.0 ms with it), and the first decode of a 1280x720
   frame takes 4.0 to 5.0 ms instead of 12.8 to 14.4 ms.
8. **The reproducer.** `repro.py` needs only nvImageCodec, nvJPEG, the CUDA runtime and numpy. In
   a clean child process, one image hung in 3 of 3 runs, and a batch of 2 returned in 3 of 3 runs.

## Evidence

- Conditions: Windows 11, one RTX 3070, 28 logical CPUs, Python 3.13.18, nvImageCodec 0.10.0.9,
  nvJPEG 13.3.2.43. Each run is one process with a time limit of 12 s to 25 s. A run that did not
  return was ended. No run on Linux and no run on a host with few CPU cores. With a CPU affinity of
  2 or 4 cores, the library still counts 28 CPUs and uses 8 threads, so the affinity runs
  (`core.txt`) do not show a host with few cores.
- The scripts and outputs are in [`975z_nvimgcodec_hang/`](../scripts/975z_nvimgcodec_hang/):
  `probe.py`, `drive.py` and `grade.py` with `matrix.txt` (item 2) and `env_disc.txt` (item 3);
  `core.py` with `core.txt`; `forced.py` with `forced.txt` (item 7); `cost.py` with `cost.txt`;
  `capture.py` with `stacks.txt`; `repro.py` and `runrepro.py` with `repro_runs.txt` (item 8). The
  folder `matrix_2026_11_17/` holds the script `hang2.py`, its run scripts and `hang2_matrix.txt`
  (item 4). The first block of `hang2_matrix.txt` has a cell `--n 1` that hangs with no option: its
  run set `NVIMGCODEC_DEFAULT_NUM_CUDA_STREAMS=1` (`matrix_h2.sh`).

## Open work

See [open-work.md](../open-work.md).
