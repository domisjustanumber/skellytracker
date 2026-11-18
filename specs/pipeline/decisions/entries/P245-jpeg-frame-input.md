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
   `pipeline.run`. The copy of the GPU decoder is in `decode`. [Timing](../../timing.md#fields)
   gives the events of each frame form.
5. **Decoded frame.** 8-bit, 3 channels, BGR, turned by the EXIF orientation (item 7). It can
   be in GPU memory when an `onnx_model` node that runs uses `cuda` or `trt-rtx`. Else it is in CPU
   memory.
6. **Pixels.** The decoder is an implementation choice. The spec does not require equal pixels
   across decoders. It requires the width, the height, the channel count, the channel order and the
   bit depth.
7. **EXIF orientation.** The caller turns a frame with the EXIF Orientation tag in the JPEG bytes.
   The run applies it in the decode, and has no rotation input of its own. `1` or no Exif segment:
   no turn; `3`: 180 degrees; `6`: 90 degrees clockwise; `8`: 270 degrees clockwise. For `6` and
   `8`, the width and the height swap. The turn is exact for the same decoder.
   The caller must not give two or more Exif APP1 segments, or the orientation `2`, `4`, `5` or
   `7`. The run does not examine the segments, so the result of such a buffer is not defined. A
   decoded array has no orientation: the caller turns its pixels.
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
    the decode batch, the wait for the GPU decode and the upload
    ([Running](../../running.md#implementer-guidance)).

## Consequences

- No change to the sidecar spec or the camera layer. The proposal `resize-pixel-tolerance` covers
  a pixel limit of the resize.
- The user reversed "the decode ignores the EXIF orientation" before the push, after the
  measurement in the Evidence.

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
- freemocap turns a frame with the EXIF tag, and both decoders apply it by default, exactly.
- With two Exif APP1 segments, the decoders apply different segments. A check needs a scan of the
  markers of each buffer, so the caller owns the rule. The mirrored values are not tested.

## Evidence

- nvJPEG through nvImageCodec against `cv2.imdecode`: at most 3 `uint8` steps, mean 0.024, on 148
  frame variants, JPEG quality 90, 4:2:2 and 4:2:0 chroma. Measured by the user.
- The turn with the orientations `1`, `3`, `6` and `8` against the turn of the decode in the stored
  orientation by the same decoder: maximum difference 0, for `cv2.imdecode` and for nvJPEG, 4:2:2
  and 4:2:0 chroma, several sizes. One decode call with the orientations `1`, `6` and `8` gives
  correct frames. With two Exif APP1 segments, `cv2.imdecode` applies the first and nvImageCodec
  applies the last. Measured by the user.

## Alternatives rejected

- A `decode` node type: it gives an image, and a file for array callers cannot have it.
- JPEG input only: MediaPipe, Charuco, ArUco and video files give or need CPU pixels.
- Equal pixels across decoders: see the evidence.
- A start failure when the GPU decoder package is missing: the CPU decoder gives a correct frame.
- The missing-package warning at start: a run that gets only decoded arrays does not need it.
- A `V-` rule for one Exif segment: see the Reason.
- A lossless turn of the JPEG data: it cannot turn each size, and it is slower.

## Open work

See [open-work.md](../open-work.md).
