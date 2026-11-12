# Q6P7 — Reference modules implement the text, and unused cases are `not used`

**Status:** absorbed into [`model-addition-workflow/reference-implementations.md#the-step`](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#the-step), 2026-11-09 (user; PR: pending).

## Decision

1. **The text, not the host.** An exporter reference module implements the current section text.
   Each host departure goes in the intake or in a proposal of the same pack. One section has one
   module across all bundles of an exporter. Step 1 of
   [The step](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#the-step)
   is the home.
2. **The module note.** The note holds only the section ID, the source commit, and the section IDs of the imports and
   the fixtures. The
   results go in `vector-runs.yaml`, the intake or parts 4 and 5 of a proposal. Step 4 of the same
   heading is the home.
3. **`not used`.** A case of a mode that the model does not use is `not used` in `vector-runs.yaml`.
   It does not block the verdict. It is not a pass, so it does not close the Gate item `vectors`.
   [Payload](../../specs/model-sidecar/model-addition-workflow/hand-over.md#payload) is the home
   ([ADR-ZXD7](ZXD7-bundle-process.md) item 5). `verify` accepts the value.
4. **Proposal checks.** Part 2 gives the NaN, inf, tie and empty-input behaviour of each new step,
   or `out of scope`. A case with a partial input names its rules in `note`. "The parts of a
   proposal" of `phase-2-proposal.md` is the home. The template boxes name it
   ([ADR-ESP4](ESP4-one-home-for-each-workflow-rule.md) item 1).

## Reason

- The YOLOX and RTMW intakes of 2026-11-06 to 2026-11-09: the reference modules copied host
  behaviour. Response r1 of `model-yolox-person` (state `needs-contributor`) and response r1 of
  `model-rtmw-wholebody133` asked for a module that implements the current text exactly. Two bundles gave two modules of one section.
- Results in the note made docstring-only versions, and a stale `to run` landed in
  `reference/pre_resize_interpolation.py`.
- "Must pass them first" in `parity.md` made an exporter run the cases of modes that its model does
  not use.
- A proposal got a new version for its NaN rule and its permalinks.

## Alternatives rejected

- **Carry the parity evidence over when the AST is equal.** It needs a static tool first
  ([ADR-AD33](AD33-bundles-are-untrusted-input.md)).
