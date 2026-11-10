# 37CD — Session rules that the intake retro left out

**Status:** accepted, 2026-11-10 (user; PR: pending).

## Decision

1. **Questions of the user.** The session answers each question of the user in text before it
   continues ([Decision questions](../../specs/model-sidecar/model-addition-workflow/hand-over.md#decision-questions)).
2. **Part 7 at record time.** At record time, the session finds the sidecar groups of each section
   that part 2 changes in the section rows of `TRACEABILITY.md`. Each group that part 7 does not list
   is a finding of the same response (Session steps step 4).
3. **No finding against an uncommitted edit.** The session commits the edit first, or writes the
   finding as `deferred: <pending entry>` (Session steps step 6).
4. **A new required key.** A decision that adds a required sidecar key lands with the text of its
   section, or the response says `exporters: do not implement until <section ID> lands` (Session
   steps step 6).
5. **Spec defects.** A review finding that only a change of the spec text can fix is a spec defect,
   not a `needs-contributor` finding. It goes to the spec-defect list, and the session asks the user
   in the same session (Session steps step 7;
   [Full section](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#full-section)).
6. **Inactive owners and cycles.** When the owner of a bundle that a proposal waits for defers it or
   is not active, the decision question asks the user: remove the example, or wait. Before the
   session writes a wait, it checks the chain of waits for a cycle
   ([Deferral](../../specs/model-sidecar/model-addition-workflow/hand-over.md#deferral)).
7. **Permalinks.** A permalink to an older commit of the default branch stays valid. A new version
   changes only the permalinks whose cited lines changed
   ([Sources](../../specs/model-sidecar/model-addition-workflow/rules.md#sources)).
8. **One parity run.** The contributor records one committed parity run at the final commit of the
   host code: after the host changes, the vector runs and the reference modules. Then it does the dry
   pack and the pack (`author-sidecar` Step 8 item 1).

The model addition workflow states items 1 to 7. The skill `author-sidecar` states item 8.

## Reason

The retro of the YOLOX and RTMW intakes (2026-11-06 to 2026-11-09) gave these items as parts of
four proposals. The user approved the proposals. Their entries
([ADR-3HZ4](3HZ4-decision-questions-and-rule-defaults.md), [ADR-FM0B](FM0B-one-response-for-each-commit-group.md),
[ADR-G45G](G45G-one-review-wave-and-the-question-channel.md) and
[ADR-Q6P7](Q6P7-reference-module-notes-and-unused-cases.md)) left them out. A completeness check
found the gap.

- A simcc response was written against text that an uncommitted edit changed.
- The SE3Y and 52NQ wait chain was a deadlock for three days. The owner of one example had no
  sidecar commit after 2026-10-06.
- The license key came before `common/license.md` existed.
- The "Full section" request of a simcc response sent a spec defect to the exporter. The next
  response withdrew it.
- The exporters pinned again 69, 144 and 133 permalinks for each version. No rule asked for it.
- Parity ran three times for one model.

## Alternatives rejected

- **A scratch tree and `land --check` at record time.** `land` runs the landed producer, so it
  reports each changed case before the copy approval
  ([ADR-AD33](AD33-bundles-are-untrusted-input.md)).
- **A `--sections` option of `sidecar_trace.py impact`.** The section rows of `TRACEABILITY.md`
  already give the groups. Part 7 tells the contributor to use them.
