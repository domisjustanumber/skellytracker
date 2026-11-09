# Reference examples

Revision: [Changes in this revision](../changelog.md#changes-in-this-revision).

Each example is a byte copy of a sidecar that an exporter wrote for this revision
([Reference examples](../model-addition-workflow/reference-examples.md)). The provenance of each
example is in [`inventory.yaml`](../inventory.yaml). Each example has `schema_version: "2.0.0"`
([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)), the top-level
[`source`](../common/identity.md#fields), the real `sha256` of each artifact, the
[`license`](../common/license.md) block and the batch `3` with `batching.batch_conversion`
([Batching](../common/batching.md)). A user ruling removed the examples that get no rebuild. Their
headings stay, because other files link them
([ADR-YS4C](../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md)).

## YOLO26 detector (Ultralytics-Exporter; NMS-free, graph-final rows)

Removed by the content commit of [ADR-NBG2](../decisions/entries/NBG2-license-and-training-data-without-the-deferred-examples.md). A user ruling gives this example no rebuild ([ADR-YS4C](../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md)). Git history keeps the file.

## YOLO26 pose (Ultralytics-Exporter; bottom-up, packed keypoints)

Removed by the content commit of [ADR-NBG2](../decisions/entries/NBG2-license-and-training-data-without-the-deferred-examples.md). A user ruling gives this example no rebuild ([ADR-YS4C](../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md)). Git history keeps the file.

## RTMDet person (OpenMMLab-Exporter; NMS-free outputs, host NMS)

Removed by the content commit of [ADR-NBG2](../decisions/entries/NBG2-license-and-training-data-without-the-deferred-examples.md). A user ruling gives this example no rebuild ([ADR-YS4C](../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md)). Git history keeps the file.

## RTMW WholeBody (OpenMMLab-Exporter; top-down pose)

mmpose `input_size` is `(width, height)`: the `256x192` sizes (`m`, `l-256`, `x-256`) take `[N, 3, 256, 192]` input and the `384x288` sizes (`l-384`, `x-384`) `[N, 3, 384, 288]`. The model consumes RGB (`bgr_to_rgb=True`) normalized with ImageNet statistics, so the input is `normalization: imagenet` with `color_format: rgb` ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). SimCC bin counts are twice the input width and height (`simcc_split_ratio=2.0`) and come from `onnx.output_shapes`. The sidecar writes the 133 tracked points and the `wholebody` connections inline, with no `$ref`. The id and the folder follow [Keypoint detector id](../common/identity.md#keypoint-detector-id).

Sidecar: [`rtmw-wholebody133.yaml`](detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml).

For comparison, skellytracker's in-repo `rtmw/wholebody/rtmw-wholebody.yaml` describes the rtmlib `onnx_sdk` downloads (with `url`/`url_sha256`) at `schema_version: v2024.09.1019`. The spec does not describe that file. Its `imagenet_bgr` is not a mode of [Normalization](../pre/normalization.md). The package sidecars stay outside the spec until they migrate ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).

## RTMO body7 (OpenMMLab-Exporter; bottom-up pose, NMS in the graph)

Removed by the content commit of [ADR-52NQ](../decisions/entries/52NQ-model-id-suffix.md). A user ruling gives this example no rebuild ([ADR-YS4C](../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md)). Git history keeps the file.
