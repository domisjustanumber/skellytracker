# 3HZ4 — Decision questions and the defaults that a rule decides

**Status:** superseded by [BQZ9](BQZ9-intake-process-consolidation.md), 2026-11-10 (user; PR: pending).

## Decision

1. **One form for each decision question.**
   [Decision questions](../../specs/model-sidecar/model-addition-workflow/hand-over.md#decision-questions)
   is the one home of the form. Procedure B step 1 of `change-sidecar-spec` and Step 5 of
   `propose-sidecar-change` link to it. Each question gives the change in one sentence, one worked
   example with numbers from the record, the effect on each open bundle, the plan decisions that
   acceptance confirms, the full extra scope of each option and a recommended option. It writes
   "proposal bundle version N", never a bare "vN". The session asks one question for each proposal,
   or one batch if the user asks for it.
2. **Approvals in the same message.** The message of the decision shows the result of the safety
   review of each reference file, with its path and its SHA-256, and asks for the copy approval. A
   changed SHA-256 gets a new review. No approval carries over. The answer of the user also approves
   the landings and the responses that follow, with no separate go-ahead question. The push approval
   is for one plain push of the working branch at the end of the round, when the local checks pass.
   A force-push still needs its own approval.
3. **A rule decides first.** Before the session asks the user, it finds the rule that decides the
   question, and applies it.
4. **Defaults of the skills.**
   - When part 2 changes no text, the landing is the non-spec kind of the commit table, with no
     changelog row and no fingerprint change.
     [ADR-1VMX](../../specs/model-sidecar/decisions/entries/1VMX-nms-key-exclusion.md) is the
     precedent.
   - In Procedure B, an `expect` change within `FILE_TOLERANCE` of `tools/tests/test_vectors.py` is
     not a stop when it comes from a case that part 4 lists or names, or from the fixture-to-import swap of
     step 13. The change must also be within the `compare` tolerance of the case. The commit body gives it. A
     change beyond the tolerance stays a stop. The stop row for
     a changed expected value applies to Procedure C only.
   - The session records a proposal bundle that has no `verify` finding with no question. It reports
     the side effects, for example the new section owner.
5. **Independence.** Host code that an exporter wrote from, or checked against, its own reference
   module is not independent of that module
   ([Independence](../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence)).

## Reason

The YOLOX and RTMW intake sessions of 2026-11-06 to 2026-11-09 asked questions that a full question
form or an existing rule could answer:

- Three user turns asked "explain" after a one-line decision. The user asked for examples with the
  questions, and asked if "v3" was the proposal version or the spec version. The
  [ADR-52NQ](../../specs/model-sidecar/decisions/entries/52NQ-model-id-suffix.md) question came three times.
- The 1VMX copy approval was a turn of its own on 2026-11-07. "Shall I go ahead with steps 1 to 4?"
  got only "yes".
- In the [ADR-3S5G](../../specs/model-sidecar/decisions/entries/3S5G-affine-crop-matrix.md) content commit, `crop_h` of `wide-box-grows-height` changed from 666.666667 to
  666.666687, inside the tolerance 1e-4, as part 4 says. Three sessions judged it again against the
  stop row.
- The 1VMX landing found no path for a changed reference module with no text change. The user chose
  the non-spec landing.
- The independence question came twice. The user answered "How else can it be verified?".
- "Should I record it now?" asked about a recording whose only effect was a new section owner.

## Consequences

- [ADR-AD33](AD33-bundles-are-untrusted-input.md) does not change. Each file gets its own review
  before the copy. A doubt stops that file.
- Section 6 of `AGENTS.md` does not change. An approval that the user gives earlier in the round is
  the approval of the user.

## Alternatives rejected

- **One message for all proposals, always.** On 2026-11-06, the user asked for the proposals one at
  a time.
- **An approval that carries over to a later version with the same AST.** It narrows AD33 item 3. A
  new approval line costs no extra turn.
- **A doc-test edit in the content commit.** It breaks the rule of one kind of change in each commit
  ([ADR-R39S](R39S-test-fix-on-the-working-branch.md)).
- **A fix of a landed module that the session writes.** It goes against Step 2 item 5 of
  `propose-sidecar-change`, and nothing independent verifies the fix.

## Open work

See [open-work.md](../open-work.md).
