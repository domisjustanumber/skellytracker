# Decision log

This log records the technical decisions for skellytracker that affect more than one module, with
their reasons and evidence. The [spec log](../specs/model-sidecar/decisions/README.md) holds the
decisions of the sidecar spec only ([ADR-GN3D](GN3D-module-decision-logs.md)). Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). Then
read the Active entries that apply to your task. Then you do not repeat a settled question or a
completed measurement. Read a Proposed entry only for spec work in its section, or when a skill tells
you to. Read an entry of [historical.md](historical.md) only to find the reason for a decision
([z934](z934-decision-log-index-and-read-path.md)).

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012, here and in
the spec log, are backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry that supersedes the old entry in full. The body of a
decided entry changes only by the edits that the [Rules](#rules) allow. To write an entry, use
[template.md](template.md).

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [p3n3](p3n3-ai-attribution-warning.md) | No AI attribution in check-ins; a commit-msg hook warns and does not stop the commit | accepted |
| [x64y](x64y-draft-exporter-guide-folder.md) | The workflow, with the sidecar-file, validation and publishing rules, is in `model-addition-workflow/`; the exporter-only guide is a draft; no stub | accepted |
| [b9fm](b9fm-finished-sidecar-plans.md) | The reference-examples procedure moves to the workflow; the implementation plan links to the spec backlog; the coverage note is frozen evidence | accepted |
| [yve0](yve0-example-fragments.md) | An example fragment has one source: a package copy with the same bytes, or a `fragments` entry in `inventory.yaml` | accepted |
| [GN3D](GN3D-module-decision-logs.md) | Core and nested `AGENTS.md` and skills; a root log and a log for each module in `LOG_DIRS`; placement; one ID space; supersedes hxy8 | accepted |
| [EY8R](EY8R-tools-and-scripts.md) | Tools are in the root `tools/`; a script is in `scripts/` of the log that holds its entry; a script that a later step runs becomes a tool | accepted |
| [D9VT](D9VT-decision-log-move.md) | The log moves to `decisions/` and `specs/model-sidecar/decisions/`; no stub; old plain-text paths stay; proposal-copy paths; supersedes k6dz | accepted |
| [AB79](AB79-one-pr-for-the-spec-build-work.md) | Exception to 0027: the spec-build work goes to `development` in one PR; one kind of change in each commit; no new `dom/NN-*` branch | accepted |
| [JW9N](JW9N-restate-a-kept-rule-by-a-link.md) | A link to a heading that states a kept rule restates it; later edits there cite their entry; the chain rule; supersedes ngnb and HJNP | accepted |
| [FADS](FADS-hand-over-bundles-in-intakes.md) | Hand-over bundles in `intakes/`: versions, manifest, states, responses, byte-copy proposal records; no gap records; supersedes pykx, faac and 0014 | accepted |
| [TA0G](TA0G-vector-cases-and-reference-modules.md) | Refusals as a rule ID or `no-rule`, `failed` lists, `outcome()`, 256 KiB, union landing check, module imports and fixtures; supersedes a33q and 0013 | accepted |

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
- This repo has a root log in `decisions/` and a log for each module in `LOG_DIRS` of
  `tools/check_decision_log.py`. These Rules and `template.md` apply to each log. Put an entry in the
  log of a module only when each file that its Decision section names or changes is in that module.
  Put all other entries in this log. All logs have one ID space
  ([ADR-GN3D](GN3D-module-decision-logs.md)).
- The read path is this file, `open-work.md` and the Active entries that apply to your task. For a
  task in a module, the same files of the module log are also in the read path. Read a
  Proposed entry only for spec work in its section, or when a skill tells you to. Read an entry of
  `historical.md` only to find the reason for a decision.
- The body of an entry that is not `proposed` does not change, except for four edits: a link or
  anchor repair, a typo that does not change the meaning, the redaction of private data, and a
  change of ID with the repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._`
  at the end of the entry. `<kind>` is `link repair`, `typo`, `redaction`, `re-ID from XXXX` or
  `citation repair` ([ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md)). An old `renumber from NNNN` line stays.
- A `proposed` entry can change until the user decides it.
- To change a decision, add a new entry. It restates each rule of the old entry that stays, and it
  supersedes the old entry in full. Do not supersede a part of an entry. A link can restate a rule.
  The link must go to a heading of a document of the absorb rule below, and that heading must state
  the rule. Then that document is the only source of the rule. The commit that changes the text
  under such a heading cites its own entry next to the changed rule ([ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md)).
- An entry can restate a rule by a link to a heading of a document of the absorb rule. A later entry
  can change the text under that heading. The later entry cites itself at the heading. It does not
  supersede the linking entry. A later entry that changes a rule that the linking entry states in its
  own text supersedes the linking entry in full ([ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md)).
- The status line of an entry can change. These changes are allowed: `proposed` to `accepted` or
  `rejected`, `accepted` to `superseded by XXXX`, `accepted` to `absorbed into <path>#<anchor>`,
  `absorbed into <path>#<anchor>` to `superseded by XXXX`, `accepted` to `done`, and `evidence` to
  `evidence; used by XXXX`. Each change adds its date and the PR that made it. An absorbed entry is
  superseded when a new entry changes one of its rules ([ngnb](ngnb-supersede-an-absorbed-entry.md)).
  In the same PR, change the status in the index and move the row to the table for the new status.
  An `evidence` entry becomes `evidence; used by XXXX` when an accepted entry cites
  it for its decision. Its Decision cell keeps the one-line result.
- The tables and their status forms: Active (`accepted`, `evidence`) and Proposed (`proposed`) in
  the `README.md` of each log, and Historical (`rejected`, `superseded by XXXX`, `absorbed into
  <path>#<anchor>`, `evidence; used by XXXX`, `done`) in its `historical.md`. The Status cell has
  only a status form of its table. `XXXX` must be an entry that is not `proposed` or `rejected`. The
  Decision cell has 160 characters or fewer ([z934](z934-decision-log-index-and-read-path.md)).
- A Proposed row has a Section cell: the section ID of the change in backticks, or `none`. A new
  section ID is allowed.
- An accepted entry is absorbed when one of these documents states all of its rules: the spec,
  the root or a nested `AGENTS.md` ([ADR-GN3D](GN3D-module-decision-logs.md)), the skills, the model
  addition workflow, the exporter guide, the templates of `specs/model-sidecar/templates/`, and the
  Rules of this file with [template.md](template.md). Then that document is the source of the rules.
- An accepted entry that records a one-off action, with no rule that stays, is `done` when the action
  is complete.
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. It changes no decision. Write one at the end of the spec-build stage, and when
  the read-path limit fails.
- Delete an open-work item when the work is done. Delete a spec defect when its content PR lands.
- Keep the logs inside their limits: 18,000 characters for each `README.md`, 20,000 for each
  `open-work.md`, 6,000 for each entry after 0025, and 160,000 for the read path: the `README.md`,
  the `open-work.md` and the Active entries of all logs. Proposed and Historical entries are not in
  the read path. Put long evidence in a tracked file next to the entry, and link to it. Put the
  script that produced a measurement in `scripts/` of the log that holds its entry. The Evidence
  section names it. Run `uv run python tools/check_decision_log.py` to see the read-path size and
  the warnings at 80% of a limit. The doc tests run the same check.
- The tool counts characters after it changes CRLF to LF. It checks the rows, the tables, the cells,
  the status forms, the `XXXX` of each status and the limits. A warning does not fail the doc tests.
  An entry does not warn. A PR can lower a limit. A PR that raises a limit must add an entry.
- The [model addition workflow](../specs/model-sidecar/model-addition-workflow/README.md) is
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
  permalink that pins a full 40-character SHA on the default branch of that repo
  ([ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md)). Do not cite or link `plans/`. Git does not track it
  ([ADR-GN3D](GN3D-module-decision-logs.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA
  ([0027](0027-single-working-branch.md)).
- In new text, cite an entry of this log as `ADR-<ID>`, with the ID in upper case. Do this also for
  an older entry. Put the prefix in the link text, for example
  `[ADR-X64Y](x64y-draft-exporter-guide-folder.md)`. The older form `ADR-[x64y](…)` stays valid.
  Write the ID of another repo's entry with the repo name and the prefix, for example
  "OpenMMLab-Exporter ADR-0020". A bare ID in older text, for
  example 0016 or gtwq, is an entry of this log. Do not edit a decided entry only to add or move the prefix.
  Do not use the prefix in a file name, a heading, an index row, a status line or a YAML value. Write
  an ID in YAML front matter in quotes. Cite a provisional entry of another repo by the repo name,
  the PR number and the slug. End each commit subject that adds or changes an entry with
  `(ADR-<ID>)` ([ADR-HJNP](HJNP-upper-case-entry-ids.md)).
- A spec change proposal is an entry with the status `proposed`. Its source is a `proposal` bundle
  ([Hand-over bundles](../specs/model-sidecar/model-addition-workflow/hand-over.md)). Phase 2 of the
  [model addition workflow](../specs/model-sidecar/model-addition-workflow/phase-2-proposal.md) gives its parts. A part that the
  contributor cannot fill says `none` and the reason. A gap that a session finds goes on the
  spec-defect list of the spec log `open-work.md`. It is not an entry
  ([ADR-FADS](FADS-hand-over-bundles-in-intakes.md)).
- When the contributor packs a new version of a recorded proposal, record it again in the same entry.
  Replace the record in full with a byte copy of the new version. The status line adds
  `recorded again <YYYY-MM-DD> (<bundle id>@v<k>)`. Until then, Procedure B step 1 of
  `change-sidecar-spec` stops a landing. After the row state `accepted`, the record does not change.
  The ID, the slug and the status stay. In "Before acceptance" of the entry, keep the old items in
  their order. Tick a closed item, and give its reason. Mark a changed item `(changed <YYYY-MM-DD>)`.
  Put a new item last in its group, and mark it `(new <YYYY-MM-DD>)`. Change the Decision, the
  Reason and the Evidence only where the new version changes them. Change the index row when a cell
  changes. Use a non-spec commit. A contributor that packs a new version tells the user
  ([ADR-FADS](FADS-hand-over-bundles-in-intakes.md)).
- An entry that waits for a decision of another repo has a `**Depends on:**` line under its status
  line.
- Do not put a dated status line in `AGENTS.md`. Put a dated fact in `open-work.md` or in an entry.
- Do not import a file, a test or a tool from another repo. The rules of this log do not follow the
  log of another repo.
- Write entries in ASD-STE100 Simplified Technical English. Use short sentences, the active voice and
  one instruction in each sentence. "must" is the requirement word. Technical names, field names, enum
  values, formulas, code and YAML stay unchanged.
