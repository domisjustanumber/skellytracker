# P245 — A run takes a JPEG buffer for each camera frame and decodes it to frame.image

**Status:** absorbed into [`running.md#fields`](../../running.md#fields), [`running.md#behaviour`](../../running.md#behaviour), [`running.md#validation-rules`](../../running.md#validation-rules), [`running.md#implementer-guidance`](../../running.md#implementer-guidance), [`running.md#authoring-guidance`](../../running.md#authoring-guidance), [`timing.md#fields`](../../timing.md#fields), [`timing.md#validation-rules`](../../timing.md#validation-rules), [`graph.md#fields`](../../graph.md#fields), 2026-11-17 (user, decisions on the native JPEG input of 2026-11-17 and the review of the draft; PR: pending).

## Decision

1. **No node.** The run decodes a JPEG buffer to `frame.image` before the first node. Each node
   reads `frame.image` as before. No pipeline file changes. One file serves a JPEG caller and an
   array caller. The rule "An image is only the camera frame. No node gives an image." of
   [ADR-9HTX](../../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 4 stays.
2. **Two input forms.** The caller gives the image of each frame as a JPEG buffer (the bytes of one
   JPEG image) or as a decoded array: BGR, `uint8`, `(H, W, 3)`, in CPU memory
   ([Running](../../running.md#fields)). The array form stays, because MediaPipe, Charuco, ArUco and
   video files give or need CPU pixels. The concrete type of the JPEG buffer is open work.
3. **One decode.** The run decodes each JPEG buffer one time. Each reader gets the same decoded
   frame.
4. **Timing spans.** The reserved source `frame` has the spans `decode` (`frame.decode`) and
   `upload` (`frame.upload`, the copy of frames from CPU memory to GPU memory), both inside
   `pipeline.run` ([Timing](../../timing.md#fields); `V-pipeline.timing-1`):
   - a decoded array that goes to GPU memory gives `upload` and no `decode`;
   - a JPEG buffer that the run decodes on the CPU and then copies to GPU memory gives `decode` and
     then `upload`;
   - a JPEG buffer of the GPU decoder gives `decode` and no `upload`: its copy is in `decode`;
   - a call in which no frame goes to GPU memory gives no `upload` event.
5. **Decoded frame.** 8-bit, 3 channels, BGR, with the stored width and height of the JPEG. It can
   be in GPU memory when an `onnx_model` node that runs uses `cuda` or `trt-rtx`. Else it is in CPU
   memory.
6. **Pixels.** The decoder is an implementation choice. The spec does not require equal pixels
   across decoders. It requires the width, the height, the channel count, the channel order and the
   bit depth.
7. **EXIF.** The decode ignores the EXIF orientation.
8. **Fallbacks.** Each gives the warning `jpeg_decoded_on_cpu`
   ([Running](../../running.md#behaviour) item 8):
   - a JPEG that the GPU decoder refuses is decoded on the CPU for that frame. The call continues.
     One warning for each camera.
   - on `cuda` or `trt-rtx` with no GPU decoder package, the run decodes on the CPU. One warning,
     at the first call with a JPEG buffer, that names the package. A run that gets only decoded
     arrays gets no such warning.
9. **Error.** A JPEG buffer that no decoder can read breaks the new rule `V-pipeline.running-12`.
   The call raises `CallRefusedError`. A cut-off MJPEG frame of a USB camera is a noted risk, not a
   rule.
10. **Implementer guidance only.** The package type name (for example `DecodedFrame`), the decoders,
    the decode batch of the cameras with the same width and height, the wait for the GPU decode
    before a reader uses the frame, and at most one upload of a frame for each call, before the
    first reader that needs it in GPU memory ([Running](../../running.md#implementer-guidance)).

## Consequences

- This entry does not change the sidecar spec or the camera layer. The proposal
  `resize-pixel-tolerance` of the sidecar spec covers a pixel limit of the resize.

## Reason

- The cameras give MJPEG. A decode in the run lets the GPU path decode on the GPU, and keeps one
  pipeline file for each kind of caller.
- A node that gives an image breaks
  [ADR-9HTX](../../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 4, and
  needs a second file for array callers. The user rejected that design.
- Two decoders do not give equal pixels, so a pixel rule would refuse a correct decoder.
- A camera with a GPU decoder problem must not stop a live run, so the fallbacks warn and continue.
- `CallRefusedError` is the error of a call that breaks a rule of the call
  ([Running](../../running.md#behaviour) item 2). The decode is before the first node, so the call
  changes no state.

## Evidence

- nvJPEG through nvImageCodec against `cv2.imdecode`: at most 3 `uint8` steps, mean 0.024, on 148
  frame variants, JPEG quality 90, 4:2:2 and 4:2:0 chroma. Measured by the user.

## Alternatives rejected

- A `decode` node type: it gives an image, and a file for array callers cannot have it.
- JPEG input only: MediaPipe, Charuco, ArUco and video files give or need CPU pixels.
- Equal pixels across decoders: see the evidence.
- A start failure when the GPU decoder package is missing: the CPU decoder gives a correct frame.
- The missing-package warning at start: a run that gets only decoded arrays does not need it.

## Open work

See [open-work.md](../open-work.md).
