# 0017 — Folder of a sidecar with both roles

**Status:** proposed, 2026-10-23 (from the exporter evidence of Ultralytics-Exporter and
OpenMMLab-Exporter).

## Decision

**Proposed, not decided.** This entry is a gap record (see [Rules](README.md#rules)). It does not
have the eight parts of a proposal.

Add one rule to the
[Storage layout](../../specs/model-sidecar/format/file-layout.md#storage-layout): a sidecar whose `role`
includes `pose_estimator` goes under `detectors/keypoint_detectors/{family}/{part}/`. This rule also
applies when `role` includes `object_detector` too. Only a sidecar with `role: [object_detector]` goes
under `detectors/object_detectors/{family}/`. The `Role` column of the branch table gets the same
text. The change adds no field and no validation rule.

## Reason

- The storage layout gives `object_detectors/` to `role: object_detector` and `keypoint_detectors/`
  to `role: pose_estimator`. It gives no folder to a sidecar with both roles. Thus each exporter must
  guess, and two hosts can look in different folders.
- Both one-stage pose exporters already use `keypoint_detectors/{family}/body/`. The two reference
  examples with both roles (RTMO body7 and YOLO26 pose) use it too. The proposed rule moves no
  exporter output and no example.
- A sidecar with both roles has a `pose` block and a body part. The part folders (`hand`, `face`,
  `body` and `wholebody`) exist only under `keypoint_detectors/`.

## Evidence

- Ultralytics-Exporter `yolo_sidecar.py` at commit `f52ef68`: `_ROLE_BRANCHES` (lines 104-107) maps
  the pose role to `detectors/keypoint_detectors/yolo26/body`. `export_dir` (line 168) uses this map.
  `build_yolo26_pose_sidecar` writes `role: [object_detector, pose_estimator]` (line 593) into
  `yolo26-body.yaml`.
- OpenMMLab-Exporter at commit `eed3361`: `rtmo/sidecar.py:33` sets
  `ROLES = ["object_detector", "pose_estimator"]`. `rtmo/identity.py:27` sets
  `FAMILY_BRANCH = Path("detectors/keypoint_detectors/rtmo/body7")`. The `body7` folder is an exporter
  defect (see the [exporter guide](../../specs/exporter-guide/sidecars/README.md)), but the branch is
  `keypoint_detectors/`.
- The reference examples
  [`rtmo/body/rtmo-body7.yaml`](../../specs/model-sidecar/examples/detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml)
  and
  [`yolo26/body/yolo26-body.yaml`](../../specs/model-sidecar/examples/detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml)
  are under `keypoint_detectors/`.
- The [exporter guide](../../specs/exporter-guide/sidecars/README.md) says: "The spec does not say where a
  sidecar with both roles goes."

## Alternatives rejected

- **`object_detectors/{family}/` for a sidecar with both roles.** That branch has no part level. Two
  pose models of one family with different parts would have one folder. Both exporters and both
  examples would move.
- **A new branch for models with both roles.** No host needs it. Both exporters and both examples would
  move, and each host must search one more branch.
