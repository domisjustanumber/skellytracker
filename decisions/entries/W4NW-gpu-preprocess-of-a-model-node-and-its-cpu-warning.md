# W4NW — GPU preprocess of a model node and its CPU warning

**Status:** absorbed into [Running: Fields](../../specs/pipeline/running.md#fields), [Running: Behaviour](../../specs/pipeline/running.md#behaviour), [Running: Implementer guidance](../../specs/pipeline/running.md#implementer-guidance), [Timing: Fields](../../specs/pipeline/timing.md#fields), [Timing: Implementer guidance](../../specs/pipeline/timing.md#implementer-guidance), [ONNX model node: Implementer guidance](../../specs/pipeline/nodes/onnx_model.md#implementer-guidance), 2026-11-18 (user; PR: pending).

## Decision

1. On the EPs `cuda` and `trt-rtx`, an `onnx_model` node runs its preprocess as a graph of ONNX
   nodes in its own session. The run binds the output of the graph to the input of the model session
   in GPU memory. On each other EP, the node uses the CPU preprocess. This is the value `auto` of
   item 6. Item 6 gives the other values.
2. A node that runs the graph uses the CPU preprocess when the graph refuses the combination of
   the sidecar, when a graph session does not build, or when the node has graph sessions for 4 sets
   of frame sizes on the device.
3. In each case of item 2, the run gives the warning `preprocessed_on_cpu`, one time for each node
   and reason. With `auto`, a node on an other EP gives no such warning. With `cpu`, the run gives
   no such warning. With `gpu`, a node on an EP with no wiring for the graph gives the warning with
   the reason `ep_not_wired`, one time for each node, at the start of the run.
4. The node builds a graph session at the first call with a set of frame sizes. The run has no
   parameter for the frame sizes.
5. The timing header shows the preprocess provider at the start of the run. A later change to the
   CPU preprocess gives the warning and does not change the header. In a run with the value `cpu`
   of item 6, the header shows the CPU preprocess (null) from the start of the run.
6. The run has one parameter for the place of the preprocess: `auto`, `cpu` or `gpu`. Its default
   is `auto`. Another value fails at the start of the run.
   - `auto` uses the graph on the EPs that a certification report confirms, `cuda` and `trt-rtx`.
     It uses the CPU preprocess on each other EP.
   - `cpu` uses the CPU preprocess on each EP. It also forces the JPEG decode to the CPU: no GPU
     JPEG decoder opens, and no frame uploads. Only the model runs on the EP. The run gives no
     warning `preprocessed_on_cpu` and no warning `jpeg_decoded_on_cpu`. `cpu` is for a benchmark
     of the CPU path against the GPU path.
   - `gpu` uses the graph on each EP that has the wiring for it, also on an EP that no
     certification report confirms yet. In this version, only `cuda` and `trt-rtx` have the wiring.
     On an EP with no wiring, the node uses the CPU preprocess. `gpu` is for a certification run on
     an EP that is not confirmed yet.
   - The CLI flag is `--preprocess`, with the value `auto`, `cpu` or `gpu`. Its default is `auto`.

## Reason

- The CPU preprocess of the detector is the largest host cost of a call: the graph takes it from
  16.2 ms to 1.9 ms for 3 frames of 1280x720 on one RTX 3070
  (["Cost of the detector preprocess"](../open-work.md)).
- A warning must show a lost gain. A run on the EP `cpu` loses none, so it gets no warning.
- The run cannot know the frame size before the first frame.
- A set of frame sizes needs its own session, because the graph has one input for each frame. In a
  run whose image size changes at each call, a session for each size costs build time and GPU
  memory. The cap of 4 limits that cost.
- An accuracy run uses the EP `cpu`, so it has the CPU preprocess with the default `auto`.
- A benchmark of the CPU path against the GPU path must run both paths on the same EP. With `cpu`,
  the caller asks for the CPU path, so no gain is lost without notice, and the run gives no warning.
- A certification run must test the graph on an EP before a reviewed report confirms that EP.
  With `gpu`, the caller asks for the graph. An EP with no wiring cannot give it, so the run gives
  the warning.

## Consequences

- The graph and the CPU preprocess agree within the resize limit of `pre.resize.interpolation`
  ([ADR-J1HK](../../specs/model-sidecar/decisions/entries/J1HK-resize-pixel-tolerance.md)), not
  bit for bit.
- The first call with a new set of frame sizes is slower by the build time of the session.
