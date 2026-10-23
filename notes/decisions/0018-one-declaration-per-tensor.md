# 0018 — One declaration for each output tensor, at every version

**Status:** proposed, 2026-10-23 (from the exporter evidence of Ultralytics-Exporter).

## Decision

**Proposed, not decided.** This entry is a gap record (see [Rules](README.md#rules)). It does not
have the eight parts of a proposal.

State in [Outputs](../../specs/sidecar/common/outputs.md#validation-rules)
that `V-common.outputs-1` (unique `outputs[].name`) applies to every `schema_version`, legacy sidecars
included. Thus a legacy sidecar that declares one ONNX tensor twice, once as `detections` and once as
`poses`, is not valid. The spec adds no legacy row that accepts this layout. A one-stage model that
packs its keypoints into the detection rows uses
[`packed_keypoints`](../../specs/sidecar/post/pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows)
at `vNEXT`. Ultralytics-Exporter must then export YOLO26 pose at `vNEXT` with
`packed_keypoints: {offset: 6, components: [x, y, score]}`.

## Reason

- `V-common.outputs-1` has no **(vNEXT)** mark. Thus the spec text already applies it to legacy
  sidecars. The `name` row also says: "A sidecar declares one ONNX tensor exactly once." But the
  validator of the legacy release does not check the rule, and one exporter writes the double
  declaration. The spec must say which reading is correct.
- The `poses` view does not follow the [`poses` layout](../../specs/sidecar/post/pose-bottom-up.md#fields)
  `(B, I, K, 3)`. Its shape is `[1, 300, 57]`, with rank 3. Axis 2 holds 57 values, not 17
  keypoints. The file does not give the keypoint offset `6`. A host must get the offset from outside
  the sidecar.
- A legacy row for this layout must define a decode that no release implements. The front matter of
  [Bottom-up pose](../../specs/sidecar/post/pose-bottom-up.md) records `decode: missing`. Such a row
  makes a legacy meaning after the fact.
- The effect is small. Only Ultralytics-Exporter writes this layout. The YOLO26 pose reference
  example ([`yolo26-body.yaml`](../../specs/sidecar/examples/detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml))
  already uses `packed_keypoints`.

## Evidence

- Ultralytics-Exporter `yolo_sidecar.py` at commit `f52ef68`, `build_yolo26_pose_sidecar`: lines
  574-582 make two output contracts from the one output tensor `output0`. One has
  `semantic: detections`. The other has `semantic: poses`, `keypoint_axis: 2` and
  `keypoint_count: 17`. Line 596 writes both (`"outputs": detections + poses`). Both have the shape of
  the one tensor, `[1, 300, 57]`. Lines 126-132 give the packed row: `6 + 17 * 3 = 57`. Line 19 sets
  `SCHEMA_VERSION = "v2024.09.1019"`.
- The message of commit `f52ef68` says that the packed tensor is "declared as both detections and
  poses views", "the layout the spec validator accepts".
- `SidecarModel._check_pose_output_shapes` in `skellytracker/core/sidecar/model.py` (lines 568-572)
  accepts one `detections` output and one `poses` output for a `coordinate` decoder. It does not
  compare the names, and it does not check the `poses` shape. The front matter of
  [Outputs](../../specs/sidecar/common/outputs.md) records: "No check for unique names
  (V-common.outputs-1)".

## Alternatives rejected

- **A legacy row that accepts two views of one tensor.** It needs a keypoint offset that the legacy
  file does not give. It defines a legacy decode after the fact.
- **Mark `V-common.outputs-1` as (vNEXT).** Then each legacy sidecar can declare a tensor twice, and
  the spec gives no meaning for it.
