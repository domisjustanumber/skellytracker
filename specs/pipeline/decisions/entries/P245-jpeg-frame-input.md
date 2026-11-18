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
   `pipeline.run`. The copy of the GPU decoder and the turn are in `decode`.
   [Timing](../../timing.md#fields) gives the events of each frame form.
5. **Decoded frame.** 8-bit, 3 channels, BGR, turned by `rotation_deg` (item 7). It can
   be in GPU memory when an `onnx_model` node that runs uses `cuda` or `trt-rtx`. Else it is in CPU
   memory.
6. **Pixels.** The decoder is an implementation choice. The spec does not require equal pixels
   across decoders. It requires the width, the height, the channel count, the channel order and the
   bit depth.
7. **Rotation.** A JPEG frame can have `rotation_deg`: `0`, `90`, `180` or `270` degrees
   clockwise, default `0`. The run decodes, then turns the frame one time, before the first node.
   For `90` and `270`, the width and the height swap. The turn is exact. The run does not apply the
   EXIF orientation. A decoded array has no `rotation_deg`: the caller turns its pixels. Another
   value, or a `rotation_deg` on a decoded array, breaks the new rule `V-pipeline.running-13`, and
   the call raises `CallRefusedError`.
8. **Fallbacks.** Each gives the warning `jpeg_decoded_on_cpu`
   ([Running](../../running.md#behaviour) item 8):
   - a JPEG that the GPU decoder refuses is decoded on the CPU for that frame. The call continues.
     One warning for each camera.
   - on `cuda` or `trt-rtx` with no GPU decoder package, the run decodes on the CPU. One warning,
     at the first call with a JPEG buffer, that names the package. A run that gets only decoded
     arrays gets no such warning.
9. **Error.** A JPEG buffer that no decoder can read breaks the new rule `V-pipeline.running-12`.
   The call raises `CallRefusedError`. A cut-off MJPEG frame of a USB camera is a noted risk, not a
   rule: nvJPEG can give a full-size frame with wrong pixels and no error, so the capture side must
   not give a frame that it knows is damaged.
10. **Implementer guidance only.** The decoders, the type name, the CPU fallback, the buffer types,
    the turn graph, the decode batch, the wait for the GPU decode and the upload
    ([Running](../../running.md#implementer-guidance)).

## Consequences

- No change to the sidecar spec or the camera layer. The proposal `resize-pixel-tolerance` covers
  a pixel limit of the resize.
- Before the push, the user changed the turn two times: from no turn, to the EXIF orientation in
  the decode, to `rotation_deg` after the decode. The last change follows the turn cost in the
  Evidence.

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
- On the GPU, a turn after the decode costs less than a decode that applies an EXIF tag. On the CPU,
  the costs are equal. The camera layer gives the rotation as a value in its frame header.
- The run can check `rotation_deg`, so a `V-` rule refuses a wrong value. A `rotation_deg` on a
  decoded array is a caller mistake that the run can see.

## Evidence

- nvJPEG through nvImageCodec against `cv2.imdecode`: at most 3 `uint8` steps, mean 0.024, on 148
  frame variants, JPEG quality 90, 4:2:2 and 4:2:0 chroma. Measured by the user.
- On the GPU, a turn after the decode costs 0.06 to 0.15 ms for each frame. A decode that applies
  an EXIF tag costs about 0.1 to 0.3 ms more for 90 and 270 degrees. On the CPU, the costs are
  equal. With two Exif APP1 segments, `cv2.imdecode` and nvImageCodec apply different segments.
  Measured by the user.

## Alternatives rejected

- A `decode` node type: it gives an image, and a file for array callers cannot have it.
- JPEG input only: MediaPipe, Charuco, ArUco and video files give or need CPU pixels.
- Equal pixels across decoders: see the evidence.
- A start failure when the GPU decoder package is missing: the CPU decoder gives a correct frame.
- The missing-package warning at start: a run that gets only decoded arrays does not need it.
- The EXIF orientation in the decode: it costs more on the GPU, and two Exif segments give two
  different frames.
- A turn inside each resize graph: measured and not chosen.
- A lossless turn of the JPEG data: it cannot turn each size, and it is slower.

## Open work

See [open-work.md](../open-work.md).
