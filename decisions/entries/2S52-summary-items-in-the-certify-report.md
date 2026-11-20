# 2S52 — The summary items in each report of `certify()`, and the format 1.2.0

**Status:** absorbed into [`certification.py`](../../skellytracker/certification.py), 2026-11-20 (user, through the freemocap session; PR: pending).

## Decision

Built today: each item. Only tests and the data of one full run on one Windows host gave a `summary`.

1. **Format.** A report of `certify()` has the schema id `skellycertify.report/1.2.0` and the field
   `summary`: a list of items with `group`, `name`, `device` and `result`. The field is in each
   report, also as an empty list. The certify suite keeps it in its module report.
2. **`ep` items.** Each EP that ran on a GPU has one item of the group `ep`. Its result is the result
   of the check of that EP on that GPU. An EP whose check is `not-run`, or has no result, has no item.
3. **Names.** `name` is the short fixed name of the EP: `TensorRT RTX`, `CUDA`, `DirectML`,
   `Core ML`, `AMD GPU`, `MIGraphX` and `CPU` (`SUMMARY_NAMES`). A name does not change.
4. **Device.** `device` is the `id` of the GPU in `host.gpus`, for example `10de:2484`. It is null for
   the CPU EP.
5. **`gpu-jpeg` items.** An item of the group `gpu-jpeg` follows the `ep` item, with the same `name`
   and `device`, only when a check of the GPU JPEG decode ran. At the level `quick`, its result is
   the result of the check `jpeg-decode`. At the level `full`, it is `fail` when one check
   `jpeg:gpu_decode.*` failed, else `pass`.
6. **CPU EP.** The CPU EP has the last item, only when one of its checks ran. Its result is `fail`
   when one of them failed, else `record-only`.

## Reason

- The repository `skellycertify` added the field in its format 1.2.0 (skellycertify ADR-MC7T), so
  that a report file starts with a short summary for a person. A writer of the file prints the
  items and does not compute them.
- The user told the freemocap session to get the fields from this package. The freemocap session
  gave that request to this session. Items 2, 5 and 6 are choices of this session where the format
  says that skellytracker decides.
- The CPU EP is the reference of each comparison. It has no result of its own to pass.

## Consequences

- Two GPUs of one model have the same `id`. Their items differ only in their order.
- For `coreml`, `device` is the chip value of `details.eps.coreml.gpu`, which is not in `host.gpus`.
  No Mac ran it.
- The Markdown part of the suite report file keeps its earlier layout. A reader of the format
  accepts it.
