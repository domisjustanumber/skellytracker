# V6G2 — The implementation stage starts at the rebuild at the gate of phase 0

**Status:** accepted, 2026-11-12 (user).

## Decision

1. **Declaration.** The project enters the implementation stage
   ([Stages](../../specs/model-sidecar/model-addition-workflow/README.md#stages)) at the
   [rebuild at the gate](../../.claude/skills/stack-commit/after-spec-build.md#rebuild-at-the-gate)
   of phase 0. This entry lands in the last commit before the rebuild. From the rebuild, each stage
   of phase 1 of the [implementation plan](../../specs/sidecar-implementation-plan.md) changes the
   package code in one stacked PR, from `dom/54-dependencies`
   ([ADR-BH7C](BH7C-two-spec-build-prs-and-a-pr-for-each-stage.md)).
2. **Rules that end.** These stage rules of [ADR-0014](0014-spec-lifecycle.md) end. The commit of
   this entry deletes each of them:
   - No file under `skellytracker/` changes, and a test fix in `skellytracker/tests/` is the only
     exception. A code defect that a test shows is now fixed in its own PR
     ([section 3](../../AGENTS.md#3-install-and-test) of `AGENTS.md`).
   - `implement-sidecar-section` and `implement-pipeline-node` do only steps 1 to 4 and report the
     plan. They now run each step.
   - A sub-agent changes no file under `skellytracker/`. The brief now names the files that the
     agent can change.
3. **The spec still changes.** A spec change comes through `propose-sidecar-change`,
   `change-sidecar-spec` or `change-pipeline-spec`, as in the spec-build stage. It lands before the
   stage of phase 1 that implements it. There is no spec freeze.
4. **Rules that stay.**
   - Until the stage of the pre-release, the current proposal rules stay: text proposals,
     exporter reference implementations and two independent implementations
     ([ADR-6J8E](6J8E-exporters-run-released-skellytracker.md) item 7).
   - The release step and the publish ban stay
     ([Publishing](../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing)).
5. **The git rules of the spec-build stage.** The commit of this entry also deletes them, because no
   commit comes between this entry and the rebuild:
   - the section "Spec-build stage" of `stack-commit`, with a link to
     [`after-spec-build.md`](../../.claude/skills/stack-commit/after-spec-build.md) in its place. Its
     rules that stay, the CI read and the old PR references, get their own headings in the skill;
   - the bullet of the two spec-build PRs in [section 6](../../AGENTS.md#6-git-rules) of `AGENTS.md`,
     and the spec-build clause of the test fix in section 3;
   - each "in the spec-build stage, one kind of change in each commit" clause.

   The rebuild steps of `after-spec-build.md` stay until the rebuild is done.
6. **Section 1 of `AGENTS.md`.** It says that the project is in the implementation stage, that the
   stages of phase 1 implement the spec, and that the spec can still change through a proposal.

## Reason

- The plan gives the gate of phase 0 to the user (stage 0.5). Stages 0.1 to 0.4 are done, and the
  consolidation entry [ADR-W5QD](W5QD-pipeline-entries-consolidation.md) has landed.
- The rebuild puts the final process files in `dom/52-process`. A stage rule that is no longer true
  would go into that PR as dead text.
- A start at the landing of this entry would let package code change on the working branch before
  the rebuild. BH7C keeps the spec-build rules until the rebuild.
- The spec has no freeze ([ADR-0014](0014-spec-lifecycle.md), "Who writes what"). An
  implementation stage finds spec defects, and the proposal skills already handle them.

## Alternatives rejected

- **A start at the landing of this entry.** Package code would change before the rebuild.
- **Keep the spec-build clauses as history.** Git history keeps them. Dead rules cost read path.
- **Only defect fixes to the spec until the exporter checkpoint.** It adds a rule that no stage
  needs.
