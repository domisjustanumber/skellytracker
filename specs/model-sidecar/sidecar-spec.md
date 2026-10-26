# Model Sidecar Specification

This specification is in separate section files. Start at [the section map](README.md).

To add a model or to request a change to the specification, follow the [model addition workflow](model-addition-workflow/README.md).

## Changes in this revision (`vNEXT`)

Moved to [changelog.md](changelog.md#changes-in-this-revision-vnext).

### Summary of changes

Moved to [changelog.md](changelog.md#summary-of-changes).

### Considered and deliberately not added

Moved to [changelog.md](changelog.md#considered-and-deliberately-not-added).

### Compatibility impact

Moved to [changelog.md](changelog.md#compatibility-impact).

## Overview

Moved to [README.md](README.md#overview).

### Core properties

Moved to [README.md](README.md#core-properties).

### Document map

Moved to [README.md](README.md#section-map).

## Format

Moved to [format/file-layout.md](format/file-layout.md).

### File extension and naming

Moved to [format/file-layout.md](format/file-layout.md#file-extension-and-naming).

### Style conventions

Moved to [format/file-layout.md](format/file-layout.md#style-conventions).

### Storage layout

Moved to [format/file-layout.md](format/file-layout.md#storage-layout).

### File pairing rules

Moved to [format/file-layout.md](format/file-layout.md#file-pairing-rules).

## File composition: `$ref` includes and `base` inheritance

Moved to [format/composition.md](format/composition.md).

### `$ref` — reference another file for any value

Moved to [format/composition.md](format/composition.md#ref--reference-another-file-for-any-value).

### `base` — inherit from another sidecar and override

Moved to [format/composition.md](format/composition.md#base--inherit-from-another-sidecar-and-override).

### Resolution pipeline

Moved to [format/composition.md](format/composition.md#resolution-pipeline).

## Common fields

Moved to [README.md](README.md#common-fields).

### Identity

Moved to [common/identity.md](common/identity.md).

### `sizes.<size>.onnx.batch_artifacts`

Moved to [common/sizes-and-artifacts.md](common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts).

### `input`

Moved to [common/input.md](common/input.md).

### `input.resize`

Moved to [common/input.md](common/input.md#inputresize).

### Unprojection

Moved to [post/unprojection.md](post/unprojection.md).

### `sizes`

Moved to [common/sizes-and-artifacts.md](common/sizes-and-artifacts.md#sizes).

### `batching`

Moved to [common/batching.md](common/batching.md).

### `outputs` (common)

Moved to [common/outputs.md](common/outputs.md).

## Detection fields (`object_detector` role)

Moved to [README.md](README.md#detection-fields-object_detector-role).

### Detection output semantics

Moved to [post/detection-outputs.md](post/detection-outputs.md#detection-output-semantics).

### `outputs` (detection)

Moved to [post/detection-outputs.md](post/detection-outputs.md#outputs-detection).

### `decode` (detection)

Moved to [post/detection-decode.md](post/detection-decode.md#decode-detection).

### Selection behaviour

Moved to [post/detection-decode.md](post/detection-decode.md#selection-behaviour).

## Pose-estimation fields (`pose_estimator` role)

Moved to [README.md](README.md#pose-estimation-fields-pose_estimator-role).

### `outputs` (pose)

Moved to [post/pose-schema.md](post/pose-schema.md#outputs-pose).

### `packed_keypoints` (bottom-up packed rows)

Moved to [post/pose-bottom-up.md](post/pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows).

### `pose` (pose estimator)

Moved to [post/pose-schema.md](post/pose-schema.md).

#### `pose.tracked_points`

Moved to [post/pose-schema.md](post/pose-schema.md#posetracked_points).

#### `pose.connections`

Moved to [post/pose-schema.md](post/pose-schema.md#poseconnections).

#### `pose.derived_points`

Moved to [post/pose-schema.md](post/pose-schema.md#posederived_points).

#### `pose.canonical_mapping`

Moved to [post/canonical-mapping.md](post/canonical-mapping.md#posecanonical_mapping).

#### Canonical skeleton

Moved to [post/canonical-mapping.md](post/canonical-mapping.md#canonical-skeleton).

#### Reference implementations

Moved to [post/canonical-mapping.md](post/canonical-mapping.md#reference-mappings-in-skellytracker).

#### `pose.decode`

Moved to [post/pose-schema.md](post/pose-schema.md#posedecode).

#### Bottom-up decode

Moved to [post/pose-bottom-up.md](post/pose-bottom-up.md#bottom-up-decode).

### `overlay` (visualization, pose estimator)

Moved to [post/overlay.md](post/overlay.md).

## Model sizes within a family

Moved to [common/sizes-and-artifacts.md](common/sizes-and-artifacts.md#model-sizes-within-a-family).

## Normalization modes

Moved to [pre/normalization.md](pre/normalization.md).

## Schema versioning

Moved to [format/versioning.md](format/versioning.md).

### Semantics

Moved to [format/versioning.md](format/versioning.md#semantics).

### Version comparison

Moved to [format/versioning.md](format/versioning.md#version-comparison).

### Version-aware compatibility

Moved to [format/versioning.md](format/versioning.md#version-aware-compatibility).

## Validation rules

Moved to [README.md](README.md#validation-rules).

## Changelog

Moved to [changelog.md](changelog.md#schema_version-history).

## Reference examples

Moved to [examples/README.md](examples/README.md).

### YOLO26 detector (Ultralytics-Exporter; NMS-free, graph-final rows)

Moved to [examples/README.md](examples/README.md#yolo26-detector-ultralytics-exporter-nms-free-graph-final-rows).

### YOLO26 pose (Ultralytics-Exporter; bottom-up, packed keypoints)

Moved to [examples/README.md](examples/README.md#yolo26-pose-ultralytics-exporter-bottom-up-packed-keypoints).

### RTMDet person (OpenMMLab-Exporter; NMS-free outputs, host NMS)

Moved to [examples/README.md](examples/README.md#rtmdet-person-openmmlab-exporter-nms-free-outputs-host-nms).

### RTMW WholeBody (OpenMMLab-Exporter; top-down pose)

Moved to [examples/README.md](examples/README.md#rtmw-wholebody-openmmlab-exporter-top-down-pose).

### RTMO body7 (OpenMMLab-Exporter; bottom-up pose, NMS in the graph)

Moved to [examples/README.md](examples/README.md#rtmo-body7-openmmlab-exporter-bottom-up-pose-nms-in-the-graph).
