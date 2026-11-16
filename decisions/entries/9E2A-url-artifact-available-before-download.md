# 9E2A — A `url` artifact that is not downloaded is available

**Status:** absorbed into [`catalog.py`](../../skellytracker/core/detectors/catalog.py), 2026-11-16 (user, question K1 of 2026-11-16; PR: pending).

## Decision

1. **Available before the download.** An artifact of a sidecar that has a `url` and no ONNX file is
   available in the catalog: `available` is true and `unavailable_reason` is empty. The host
   downloads the file when a session needs it.
2. **`downloaded`.** `ArtifactEntry` has the field `downloaded`. It is true when the ONNX file is
   present with the `sha256` of the sidecar, beside the sidecar or in the download folder. A `url`
   artifact with no file has `downloaded` false.
3. **No `url` and no file.** An artifact with no `url` and no file stays unavailable. A file beside
   the sidecar with a different hash also stays unavailable.
4. **The entry.** An `onnx` entry is available when one artifact or more is available.

This refines the text "Each entry of `list_detectors()` and `list_pipelines()` has `available` and
`unavailable_reason`" of [ADR-V7GZ](V7GZ-pipeline-api-device-and-vram-reserve.md) item 7: an
available artifact of `list_detectors()` can be a file that the host must download first. It
changes no rule of that item. It replaces the rule of stage 1.6 of the
[implementation plan](../../specs/sidecar-implementation-plan.md#16-catalog-and-the-detectors-entry-point-was-n3)
"An artifact with a `url` and no file is unavailable, and its reason says that the file is not
downloaded".

## Reason

- The user confirmed the rule on 2026-11-16 (question K1).
- `create_detector` can download and run such a model. A model that the host can run must not
  read as unavailable in the model list of an application.
- `downloaded` lets an application show that the first start needs a download.

## Consequences

- An available entry does not show that the host can get the file: the download can fail. The
  session start then raises `ArtifactDownloadError`.

## Alternatives rejected

- Unavailable until the file is downloaded, with the reason "is not downloaded". An application
  then hides or disables a model that one call can download and run.
