# Decision log

This log records technical decisions for skellytracker, with their reasons and evidence. Most entries
are about the model sidecar spec ([`specs/model-sidecar/sidecar-spec.md`](../../specs/model-sidecar/sidecar-spec.md)), the sidecar
code and the workflow that changes them. Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). Then
read the Active entries that apply to your task. Then you do not repeat a settled question or a
completed measurement. Read a Proposed entry only for spec work in its section, or when a skill tells
you to. Read an entry of [historical.md](historical.md) only to find the reason for a decision
([z934](z934-decision-log-index-and-read-path.md)).

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012 are
backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry that supersedes the old entry in full. The body of a
decided entry changes only by the edits that the [Rules](#rules) allow. To write an entry, use
[template.md](template.md).

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [k6dz](k6dz-model-sidecar-folder.md) | The sidecar spec folder and its entry point `sidecar-spec.md` move to `specs/model-sidecar/`; a move with no change of rule | accepted |
| [p3n3](p3n3-ai-attribution-warning.md) | No AI attribution in check-ins; a commit-msg hook warns and does not stop the commit | accepted |
| [x64y](x64y-draft-exporter-guide-folder.md) | The workflow, with the sidecar-file, validation and publishing rules, is in `model-addition-workflow/`; the exporter-only guide is a draft; no stub | accepted |
| [b9fm](b9fm-finished-sidecar-plans.md) | The reference-examples procedure moves to the workflow; the implementation plan links to the spec backlog; the coverage note is frozen evidence | accepted |
| [ngnb](ngnb-supersede-an-absorbed-entry.md) | An absorbed entry can be superseded: its status changes from `absorbed into <path>#<anchor>` to `superseded by XXXX` | accepted |
| [hxy8](hxy8-scoped-agent-instructions.md) | Core root `AGENTS.md`; folder rules in a nested `AGENTS.md` with an importing `CLAUDE.md`; procedures as skills; supersedes 0001 | accepted |
| [a33q](a33q-vector-case-form.md) | One vector case form: optional `function` and `compare`, errors by rule ID, NaN, exporter entries; 64 KiB; one writer | accepted |
| [yve0](yve0-example-fragments.md) | An example fragment has one source: a package copy with the same bytes, or a `fragments` entry in `inventory.yaml` | accepted |
| [pykx](pykx-submission-folders.md) | Submission files in `plans/sidecar/`: a folder for each model and each proposal, with target file names; candidate examples allowed | accepted |
| [HJNP](HJNP-upper-case-entry-ids.md) | Upper-case entry IDs in new entries and new citations; older IDs stay; restates the prefix, ID, edit and record-again rules of b1c0 | accepted |

### Proposed

These entries wait for a decision of the user. Section is the spec section of the change, or `none`
when the change has no one section. The spec change proposals and the gap records of the sidecar spec
are in the [spec log](../specs/model-sidecar/decisions/README.md#proposed).

| # | Decision | Section | Status |
|---|----------|---------|--------|

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work and the repository state are in [open-work.md](open-work.md). The spec defects are
in the [open work of the spec log](../specs/model-sidecar/decisions/open-work.md).

## Rules

- Write one entry for each decision or measurement. Use [template.md](template.md).
- The read path is this file, `open-work.md` and the Active entries that apply to your task. Read a
  Proposed entry only for spec work in its section, or when a skill tells you to. Read an entry of
  `historical.md` only to find the reason for a decision.
- The body of an entry that is not `proposed` does not change, except for four edits: a link or
  anchor repair, a typo that does not change the meaning, the redaction of private data, and a
  change of ID with the repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._`
  at the end of the entry. `<kind>` is `link repair`, `typo`, `redaction`, `re-ID from XXXX` or
  `citation repair` ([gtwq](gtwq-random-entry-ids.md)). An old `renumber from NNNN` line stays.
- A `proposed` entry can change until the user decides it.
- To change a decision, add a new entry. It restates each rule of the old entry that stays, and it
  supersedes the old entry in full. Do not supersede a part of an entry.
- The status line of an entry can change. These changes are allowed: `proposed` to `accepted` or
  `rejected`, `accepted` to `superseded by XXXX`, `accepted` to `absorbed into <path>#<anchor>`,
  `absorbed into <path>#<anchor>` to `superseded by XXXX`, `accepted` to `done`, and `evidence` to
  `evidence; used by XXXX`. Each change adds its date and the PR that made it. An absorbed entry is
  superseded when a new entry changes one of its rules ([ngnb](ngnb-supersede-an-absorbed-entry.md)).
  In the same PR, change the status in the index and move the row to the table for the new status.
  An `evidence` entry becomes `evidence; used by XXXX` when an accepted entry cites
  it for its decision. Its Decision cell keeps the one-line result.
- The tables and their status forms: Active (`accepted`, `evidence`) and Proposed (`proposed`) in this
  file, and Historical (`rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
  `evidence; used by XXXX`, `done`) in [historical.md](historical.md). The Status cell has only a
  status form of its table. `XXXX` must be an entry that is not `proposed` or `rejected`. The
  Decision cell has 160 characters or fewer
  ([z934](z934-decision-log-index-and-read-path.md)).
- A Proposed row has a Section cell: the section ID of the change in backticks, or `none`. A new
  section ID is allowed.
- An accepted entry is absorbed when one of these documents states all of its rules: the spec,
  the root or a nested `AGENTS.md` ([hxy8](hxy8-scoped-agent-instructions.md)), the skills, the model addition workflow, the exporter guide, the templates of
  `specs/model-sidecar/templates/`, and the Rules of this file with [template.md](template.md). Then that document is the source of the rules.
- An accepted entry that records a one-off action, with no rule that stays, is `done` when the action
  is complete.
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. It changes no decision. Write one at the end of the spec-build stage, and when
  the read-path limit fails.
- Delete an open-work item when the work is done. Delete a spec defect when its content PR lands.
- Keep the log inside its limits: 18,000 characters for this file, 20,000 for `open-work.md`, 6,000
  for each entry after 0025, and 160,000 for the read path: this file, `open-work.md` and the Active
  entries. Proposed and Historical entries are not in the read path. Put long evidence in a tracked
  file next to the entry, and link to it. Put the script that produced a measurement in
  `notes/decisions/scripts/`. The Evidence section names it. Run
  `uv run python tools/check_decision_log.py` to see the read-path size and the warnings at 80% of a
  limit. The doc tests run the same check.
- The tool counts characters after it changes CRLF to LF. It checks the rows, the tables, the cells,
  the status forms, the `XXXX` of each status and the limits. A warning does not fail the doc tests.
  An entry does not warn. A PR can lower a limit. A PR that raises a limit must add an entry.
- The [model addition workflow](../../specs/model-sidecar/model-addition-workflow/README.md) is
  normative for the process that adds a model or changes the spec, and for the rules of the sidecar
  files, the validation and the publishing ([x64y](x64y-draft-exporter-guide-folder.md)). The
  exporter guide is normative for the rules that it adds for exporters. The sidecar spec is
  normative for the meaning of a sidecar.
- The bootstrap kit takes these rules. Its tool keeps the limits 14,000 for the index and 220,000 for
  the read path. The kit keeps an optional mirror rule.
- A decision can be accepted before its spec text lands. Its spec text then comes in a later content
  PR.
- An entry ID has 4 characters from `0123456789ABCDEFGHJKMNPQRSTVWXYZ`. The first character of a new
  ID is a letter. The entries 0001 to 0048 keep their numbers. Do not make a new all-digit ID. An
  older entry keeps its lower-case ID in its file name, heading and index row. Do not edit older text
  only to change the case. IDs that differ only in case are one ID
  ([ADR-HJNP](HJNP-upper-case-entry-ids.md)).
- Before you add an entry, run `git fetch --all` when you can. Then run
  `uv run python tools/check_decision_log.py --new`. Give the entry the ID of the `new:` line. Create
  its file immediately. Add its index row at the end of the table for its status, in the same PR. The
  index order is the order of addition.
- The pre-push hook runs `--collisions`, the same check without the `new:` line. Act on each `re-ID:`
  line. Both sides of a collision get the same verdict: an entry on `development` wins, then an entry
  on a remote-tracking branch, then the entry whose first commit has the earlier author date, then
  the file name that sorts first. An uncommitted file loses to a committed file. Refs merged into
  `HEAD`, the upstream and push refs of the branch, `backup/` branches and an old file name of an
  entry are not collisions. An ID does not change for a different reason.
- To change an ID, run `--new`. Rename the file to the new ID. Change the ID in its heading and in its
  index row. Find the citations with `git grep -n -i -E "\bXXXX\b|XXXX-"`, and repair each one. Ask the
  user before you change a PR title or a PR body. If the entry is on `development`, add
  `_Edited YYYY-MM-DD (#PR): re-ID from XXXX._` to it, and a `citation repair` line to each entry on
  `development` that you repair.
- Do not give an ID that an entry had on `development` to a different entry. Do not keep two index
  rows with one ID.
- Cite a tracked file with a relative link. Cite a commit, or the code of another repo, with a GitHub
  permalink that pins a full SHA on the default branch of that repo
  ([gtwq](gtwq-random-entry-ids.md)). Do not cite or link `plans/`. Git does not track it
  ([hxy8](hxy8-scoped-agent-instructions.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA
  ([0027](0027-single-working-branch.md)).
- In new text, cite an entry of this log as `ADR-<ID>`, with the ID in upper case. Do this also for
  an older entry. Put the prefix in the link text, for example
  `[ADR-X64Y](x64y-draft-exporter-guide-folder.md)`. The older form `ADR-[x64y](…)` stays valid.
  Write the ID of another repo's entry with the repo name and the prefix, for example
  "OpenMMLab-Exporter ADR-0020". A bare ID in older text, for
  example 0016 or gtwq, is an entry of this log. Do not edit a decided entry only to add the prefix.
  Do not use the prefix in a file name, a heading, an index row, a status line or a YAML value. Write
  an ID in YAML front matter in quotes. Cite a provisional entry of another repo by the repo name,
  the PR number and the slug. End each commit subject that adds or changes an entry with
  `(ADR-<ID>)` ([ADR-HJNP](HJNP-upper-case-entry-ids.md)).
- A spec change proposal is an entry with the status `proposed`. Phase 2 of the
  [model addition workflow](../../specs/model-sidecar/model-addition-workflow/phase-2-proposal.md)
  gives its parts ([0014](0014-spec-lifecycle.md)).
- A gap record is also an entry with the status `proposed`. It gives a gap or a conflict with the
  spec text, its evidence and the direction of a change, but not all eight parts of a proposal. Its
  Decision section says that it is a gap record. The user can accept or reject a gap record.
- A later proposal for a gap record edits the gap record. It adds the parts that the gap record does
  not have, and the status stays `proposed`. The status line adds the date and the source, for
  example `completed 2026-11-02 (OpenMMLab-Exporter proposal)`. Do not add a second entry for the
  same gap.
- When the exporter changes a recorded proposal, record it again in the same entry. Replace the copy
  in full, and tick the closed items of "Before acceptance". The status line adds
  `recorded again <YYYY-MM-DD> (<source>)` (ADR-[b1c0](b1c0-adr-citation-prefix.md)).
- An entry that waits for a decision of another repo has a `**Depends on:**` line under its status
  line.
- Do not put a dated status line in `AGENTS.md`. Put a dated fact in `open-work.md` or in an entry.
- Do not import a file, a test or a tool from another repo. The rules of this log do not follow the
  log of another repo.
- Write entries in ASD-STE100 Simplified Technical English. Use short sentences, the active voice and
  one instruction in each sentence. "must" is the requirement word. Technical names, field names, enum
  values, formulas, code and YAML stay unchanged.
