# XM9C — Rulings of 2026-11-23: no real model in CI before the pre-release, public reference frames, the certify model account, no upstream reports

**Status:** accepted, 2026-11-23 (user).

## Decision

1. **CI.** CI runs no real model before the 2.0.0 pre-release. The gate on the reference files
   ([ADR-T41E](T41E-reference-files-of-a-model-bundle.md)) runs on a developer system, and its
   result is evidence.
2. **Reference frames.** The still frames that the project chooses from the freemocap recording go
   into this public repository, in a golden folder of
   [ADR-9VN4](9VN4-no-camera-recordings-or-frames-in-git.md). freemocap states their licence and
   the name to credit. Each person in a frame agrees in writing to the public, permanent use.
3. **Certify model files.** They stay on the personal Hugging Face account until the 2.0.0
   release. Before that release, they move to an account of the freemocap organisation.
4. **Upstream reports.** The project sends no report to NVIDIA for the nvImageCodec hang
   ([ADR-975Z](975Z-nvimagecodec-one-image-decode-hang.md)) and no report to ONNX Runtime for the
   exit hang of the CUDA EP plugin ([ADR-C6A5](C6A5-exit-hang-of-the-cuda-ep-plugin.md)).

## Reason

- Item 1: the image list of the reference files is a stop-gap from COCO val2017. A CI job with
  real models needs those images and 100 MB to 400 MB of ONNX files on each OS, and the freemocap
  frames will replace the list.
- Item 2: shipped frames need no local dataset and no recipe for a made image.
- Item 3: volunteers test with the current address.
- Item 4: the user decided it.

## Open work

[open-work.md](../open-work.md)
