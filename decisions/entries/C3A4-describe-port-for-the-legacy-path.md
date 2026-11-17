# C3A4 — A temporary public `describe_port` for the legacy path of the freemocap metrics stage

**Status:** absorbed into [`skellytracker/AGENTS.md#onnx-runtime`](../../skellytracker/AGENTS.md#onnx-runtime), [`sidecar-implementation-plan.md#24-delete-the-old-run-code-was-dc`](../../specs/sidecar-implementation-plan.md#24-delete-the-old-run-code-was-dc), [`skellytracker/core/pipelines/loading.py`](../../skellytracker/core/pipelines/loading.py), 2026-11-17 (user).

## Decision

1. `skellytracker.core.pipelines` exports `describe_port(config, port, *, user_root=None)`. It
   gives the resolved facts of one port of a config, for example `"wholebody.keypoints"`: the raw
   `point_names` and the raw `groups` of the port. The delivered output schema and the result of a
   camera do not change
   ([ADR-9HTX](9HTX-pipeline-node-and-port-redesign.md) item 14).
2. Its one caller is the legacy path of the freemocap metrics stage
   ([ADR-92BE](92BE-legacy-path-for-the-freemocap-metrics-stage.md)). That path puts the 133 points
   of the old tracker in the raw names of `wholebody.keypoints` of the built-in
   `yolox-rtmw-wholebody`, then calls `to_canonical(value, groups)` to get the delivered names.
3. It is temporary. Stage 2.4 of the implementation plan deletes it with the rest of the legacy
   path. No other code uses it.

## Reason

After stage 4 of ADR-9HTX, the output schema holds only the delivered canonical names and the
groups that pass through. No public interface gave the raw point names and groups of a port, so
the legacy path could not convert the old points. The user chose to keep the legacy path working
with a new public function only for it.

## Alternatives rejected

- A raw layout in the output schema. The main reader of freemocap reads the delivered form.
- Stop the legacy comparison of the keypoints until stage 2.4.
