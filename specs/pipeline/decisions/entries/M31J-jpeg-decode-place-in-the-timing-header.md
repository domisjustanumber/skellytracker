# M31J — The timing header gives the place of the JPEG decode

**Status:** absorbed into [`timing.md#fields`](../../timing.md#fields), 2026-11-23 (absorb at landing; PR: pending).

## Decision

1. The header line of a timing file has the field `jpeg_decode`: `gpu`, `cpu` or `mixed`.
2. `gpu`: each device of the run has a GPU JPEG decoder for its JPEG buffers. `cpu`: no device has
   one. `mixed`: some devices have one.
3. The field gives the place that the run starts with. The run writes the header before the first
   call, and the GPU decoder of a device opens at its first JPEG call. A decoder that does not open,
   and a buffer that the GPU decoder refuses, decode on the CPU and give the warning
   `jpeg_decoded_on_cpu`, as before.
4. The field does not tell that a frame is a JPEG buffer. A run with decoded arrays only has the
   same value.
5. The schema id stays `skellytracker.timing/1`. The change adds one field and changes no other
   field.

## Reason

- The user asked for the decode place in the timing header. An application shows the time of the
  span `frame.decode`. It could not tell from the timing data where that decode runs.
- The warning `jpeg_decoded_on_cpu` comes only when a GPU decoder was planned and the CPU decoded.
  It tells nothing on a run with a CPU decode from the start.
- `stage_providers.preprocess` has the same form: it gives the preprocess of a node at the start of
  the run.

## Consequences

- A reader that requires an exact list of the header fields must add the field.
- The value can be wrong for one call: a GPU decoder that does not open decodes on the CPU. The
  warning tells this.

## Open work

- None.
