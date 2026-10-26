# ngnb — An absorbed entry can be superseded

**Status:** accepted, 2026-10-26 (user).

## Decision

1. **A new status change.** The status line of an entry can change from
   `absorbed into <path>#<anchor>` to `superseded by XXXX`. Make this change when a new entry changes
   a rule that the absorbed entry records.
2. **Complete supersession.** The new entry supersedes the absorbed entry in full. It restates each
   rule of the absorbed entry that stays. Do not supersede a part of an entry.
3. **The same steps.** The change adds its date and the PR that made it, as each other status change
   does. The row stays in the Historical table. Its Status cell changes to `superseded by XXXX`.
4. **The other status changes do not change.** These changes stay allowed: `proposed` to `accepted`
   or `rejected`, `accepted` to `superseded by XXXX`, `accepted` to `absorbed into <path>#<anchor>`,
   `accepted` to `done`, and `evidence` to `evidence; used by XXXX`.
5. **The bootstrap kit.** The kit takes this rule. Its decision-log Rules and its guide state it.

## Reason

- An absorbed entry records rules that a document now states. A later decision can change one of
  these rules. Before this entry, no status form recorded that. The old entry kept
  `absorbed into` a document that no longer stated its rule, and a reader of the old entry did not
  find the entry that changed it.
- [0034](0034-sidecar-guide-folder.md) was absorbed into `AGENTS.md`. Its folder rule changes:
  [x64y](x64y-draft-exporter-guide-folder.md) moves the process to the model addition workflow and
  the exporter-only guide to a draft folder. The user chose `superseded by x64y` for 0034
  (2026-10-26).
- The open work said "An absorbed entry cannot be superseded". So
  [0008](0008-vnext-scope.md) and [0011](0011-rtmdet-host-nms.md) stayed Active, only to keep a later
  supersession possible.

## Consequences

- Absorption no longer blocks a later supersession. An accepted entry can be absorbed when a
  document states all of its rules, also when a proposal that supersedes it waits for the user.

## Alternatives rejected

- **A new entry with no change of the old status.** The old entry then points to a document that no
  longer states its rule.
- **A new status form, for example "absorbed, then superseded".** It adds a form and a change of
  `tools/check_decision_log.py`. `superseded by XXXX` already gives the reader the entry to read.
- **Change the absorbed entry back to `accepted` first.** That is not an allowed status change. It
  also puts the entry on the read path again for no reason.
