# 1GG7 — No compiled files in bundles

**Status:** accepted, 2026-11-06 (user; PR: pending).

## Decision

The user asked to reject the compiled file of a proposal bundle and to make the process clear, "so
it doesn't happen again".

1. **Rule.** A bundle holds no compiled file: no `__pycache__/` folder and no `.pyc` or `.pyo`
   file. The [Payload](../../specs/model-sidecar/model-addition-workflow/hand-over.md#payload) of
   the hand-over bundles states it.
2. **Check.** `refused_file` of `tools/intake_bundle.py` gives the reason. `pack` refuses such a
   file, and `verify` gives a finding for it. The finding gives the response `needs-contributor`.

## Reason

`proposal-simcc-score-rule@openmmlab-exporter` v1 holds
`reference/__pycache__/post_pose_decode_simcc.cpython-314.pyc` and lists it in the manifest
`files`. A session cannot review compiled code as text, and a record is a byte copy, so the file
would go into a tracked folder
([ADR-AD33](AD33-bundles-are-untrusted-input.md)). `pack` copied each file of the payload folder.
`verify` read only `reference/*.py`, so it did not give the finding of
[ADR-AD33](AD33-bundles-are-untrusted-input.md) item 2 for a file in `reference/` that is not a
section module. The rule to run with `python -B` was in the workflow, but it did not stop the file:
its tag is `cpython-314`, and the environment of this checkout runs Python 3.12.

## Alternatives rejected

- A rule in the text only. The text already told exporter agents to run Python with `-B`.
- A refusal of each payload file that the Payload table does not name. The user asked only about
  compiled files.
