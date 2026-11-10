# P8Q0 — The response `closed` for a model with no known license

**Status:** absorbed into [`model-addition-workflow/hand-over.md`](../../specs/model-sidecar/model-addition-workflow/hand-over.md), [`tools/intake_bundle.py`](../../tools/intake_bundle.py), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes no entry. It gives the response for the refusal of
[ADR-V8FK](V8FK-license-evidence-and-models-with-no-license.md) item 2.

1. **The response.** When row LC2 of a `model` bundle is `unknown`, the session writes the
   response `closed`. Its finding names `V-common.license-5`. The model gets no sidecar. Step 5 of
   [Session steps](../../specs/model-sidecar/model-addition-workflow/hand-over.md#session-steps)
   states this.
2. **A new version.** A new version of a `closed` model bundle is `submitted` again, for example
   when the contributor finds the license of the weights later. The `model` row of
   [States](../../specs/model-sidecar/model-addition-workflow/hand-over.md#states) states this.
   `pack` already accepts the new version.
3. **The tool.** `bundles` of [`intake_bundle.py`](../../tools/intake_bundle.py) gives the state
   `submitted` to a `closed` model bundle whose current version is newer than the
   `answers_version` of its latest response. Then `list` does not mark it `(can delete)`, and
   `verify` runs the drift checks on it.

## Reason

- The user, 2026-11-10: `closed`, because the decision of
  [ADR-V8FK](V8FK-license-evidence-and-models-with-no-license.md) was "reject".
- Before, step 5 gave such a bundle `needs-contributor`, because it has the verdict
  `does not describe` and no proposal bundle. That response asks for more work, but phase 1 forbids
  a proposal for row LC2.
- A model bundle ID is `model-<name>@<contributor>`. The contributor cannot send a new bundle for
  the same model, so a new version is the only path back.

## Alternatives rejected

- **`needs-contributor` with an LC2 finding.** The bundle stays open for a license that can be
  absent for all time. This is softer than "reject".
- **`pack` refuses a new version of a `closed` model bundle.** Then a model whose license is found
  later can never come back.
