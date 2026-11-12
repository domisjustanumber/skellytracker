# 6J8E — Exporters run released skellytracker; upstream parity is the independent check

**Status:** absorbed into [`AGENTS.md#6-git-rules`](../../AGENTS.md#6-git-rules), [`author-sidecar/SKILL.md#procedure`](../../.claude/skills/author-sidecar/SKILL.md#procedure), [`change-sidecar-spec/SKILL.md#procedure-a-land-a-model-with-the-verdict-describes`](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-a-land-a-model-with-the-verdict-describes), [`change-sidecar-spec/SKILL.md#procedure-b-land-an-accepted-proposal`](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-b-land-an-accepted-proposal), [`implement-sidecar-section/SKILL.md#step-5-port-or-compare`](../../.claude/skills/implement-sidecar-section/SKILL.md#step-5-port-or-compare), [`proposal-gate.md#acceptance-gate`](../../.claude/skills/implement-sidecar-section/proposal-gate.md#acceptance-gate), [`proposal-gate.md#steps`](../../.claude/skills/implement-sidecar-section/proposal-gate.md#steps), [`proposal-gate.md#a-model-with-the-verdict-describes`](../../.claude/skills/implement-sidecar-section/proposal-gate.md#a-model-with-the-verdict-describes), [`propose-sidecar-change/SKILL.md#step-3-write-each-proposal`](../../.claude/skills/propose-sidecar-change/SKILL.md#step-3-write-each-proposal), [`hand-over.md#patches`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#patches), [`hand-over.md#patch-review`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#patch-review), [`hand-over.md#states`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#states), [`sidecar-files.md#independence`](../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence), [`change-proposal.md#3-reference-implementation`](../../specs/model-sidecar/templates/change-proposal.md#3-reference-implementation), [`model-intake.md#proposals-and-reference-files`](../../specs/model-sidecar/templates/model-intake.md#proposals-and-reference-files), [`intake_bundle.py`](../../tools/intake_bundle.py), 2026-11-12 (absorb sweep, user; PR: pending).

## Decision

1. **Shared runtime.** Each exporter runs a pinned skellytracker release as its ONNX host. This
   starts when a release loads `"2.0.0"` sidecars and runs a sidecar model with no hand-written
   detector. Then the exporter host code for the spec sections retires.
2. **Code changes as a patch.** A proposal that needs a change of the package code has two parts:
   the proposal text, and a patch file against the tag of the pinned release. Until the GitHub
   Issues channel exists, the patch goes in the bundle. After that, the text goes in an issue and the
   patch in a fork PR. Fork PRs start only after the CI hardening that stage M10 of
   [`specs/sidecar-implementation-plan.md`](../../specs/sidecar-implementation-plan.md) gives.
3. **Patch scope.** A patch changes only `skellytracker/`. A change to `pyproject.toml`,
   `uv.lock`, `.github/`, `.pre-commit-config.yaml`, `tools/`, `specs/` or a `conftest.py` stops
   the review. A new dependency is a gap for the user, not a part of a patch.
4. **Patch safety.** A patch is untrusted input
   ([ADR-AD33](AD33-bundles-are-untrusted-input.md)). The session reads the whole diff before a
   run, and the user approves the run. The session applies the patch only in a disposable checkout,
   with no network and no credentials. The session never commits a patch as sent. It rebases the
   patch onto `development`, runs the gate again and commits the result as its own implementation
   commit.
5. **Independence.** An exporter that runs skellytracker is not independent of skellytracker. A
   vector is verified when the skellytracker code, with the patch, agrees with it, and the vector
   comes from an upstream reference output. The `note` of each case gives the upstream tool and its
   version. This replaces "an exporter and skellytracker" as two independent implementations.
6. **Acceptance gate.** The user accepts a proposal only after skellytracker implements it and
   passes the gate: the vectors agree, the package loads the sidecar, the model run matches the
   parity output, and the model is in the package catalog. A model with the verdict `describes` passes
   only the model run and the catalog steps.
7. **When.** Items 1 to 6 apply from stage M10 of the plan. Until then, the current rules stay:
   text proposals, exporter reference implementations, and two independent implementations.

## Reason

- The user, in words: "update exporters so they use released skellytracker as their onnx runtime,
  so any code changes they propose will then be to the released skellytracker code, not their own
  onnx implementation."
- The user, in words: "a new sidecar proposal [must] only be approved once relevant implementation
  work has been done in skellytracker to accommodate the change."
- With one shared runtime, the exporter run and the skellytracker run are the same code. Only the
  upstream library stays independent. The user accepted this change on 2026-11-10.
- A patch keeps the code that the exporter tested. A text description would make skellytracker
  write that code again.
- A bundle already has the pack, verify and record steps and the safety review. A patch file is
  text, and it does not run in GitHub CI.

## Consequences

- Each gated proposal waits for M6, the catalog of M7 and the package model of M8.
- The work of a rejected proposal is lost. The gate thus starts with a decision question to the
  user.
- The workflow, the hand-over rules, the skills, `AGENTS.md` section 6 and the draft exporter guide
  change in stage M10. The user changes the exporter guide
  ([ADR-x64y](x64y-draft-exporter-guide-folder.md)).
- Step 5 of `implement-sidecar-section` ("port") becomes "apply the patch".

## Alternatives rejected

- **Fork PRs now.** They need CI hardening first. They also break the one-PR rule of the spec-build
  stage ([ADR-R39S](R39S-test-fix-on-the-working-branch.md)) and the rule that exporter agents change
  only `intakes/`.
- **Text only.** skellytracker would write the tested code again, and the two copies can differ.
- **A clean-room skellytracker implementation as the independent check.** It is necessary only
  while each exporter has its own host code. With a shared runtime, it is not necessary.
