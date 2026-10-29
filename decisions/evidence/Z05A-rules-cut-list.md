# Z05A: cut units of the Rules

Evidence for [ADR-Z05A](../Z05A-essential-decision-log-rules.md). R1 to R150 are the units of the
[Rules](../README.md#rules) at commit `2ff24e4`. Line numbers are at that commit.

Kept (28): R13, R14, R19, R22, R23, R26, R30, R33, R34, R43, R45, R46, R47, R48, R49, R56, R66, R79,
R80, R93, R99, R100, R107, R117, R118, R120, R143, R144. Each other unit is cut. The evidence column
gives the place that already states the unit, the tool that enforces it, or the reason.

## CUT-ELSEWHERE (another loaded text states it)

| id | short text | class | evidence |
|---|---|---|---|
| R1 | One entry for each decision or measurement | CUT-ELSEWHERE | AGENTS.md:119, verbatim |
| R2 | Use template.md | CUT-ELSEWHERE | decisions/README.md:18-19 intro (stays); spec log README:5-6; propose-sidecar-change:181-182 |
| R4 | Rules and template.md apply to each log | CUT-ELSEWHERE | spec log README:5-6; template.md:3 and :7-8 |
| R5 | Module-log placement condition | CUT-ELSEWHERE | AGENTS.md:112-114 (ADR-GN3D); template.md:7-8 |
| R6 | All other entries go in the root log | CUT-ELSEWHERE | AGENTS.md:113-114 |
| R8 | The read path | CUT-ELSEWHERE | AGENTS.md:106-107; decisions/README.md:5-7 intro |
| R9 | Module-log files join the read path | CUT-ELSEWHERE | AGENTS.md:108-111; spec log README:6-7 |
| R10 | Read a Proposed entry only for spec work or on a skill's word | CUT-ELSEWHERE | decisions/README.md:8-9 intro (stays); propose-sidecar-change:109-111 |
| R11 | Read historical.md only for a reason | CUT-ELSEWHERE | decisions/README.md:9-10 intro (stays); spec log README:7-8 |
| R12 | A decided body changes only by the allowed edits | CUT-ELSEWHERE | decisions/README.md:17-18 intro; R13 keeps the list |
| R18 | To change a decision, add a new entry | CUT-ELSEWHERE | decisions/README.md:15 intro |
| R20 | The new entry supersedes the old in full | CUT-ELSEWHERE | decisions/README.md:15 intro |
| R21 | Do not supersede a part of an entry | CUT-ELSEWHERE | decisions/README.md:15 intro; STATUS_FORMS has no partial form |
| R27 | A change under a linked heading does not supersede | CUT-ELSEWHERE | decisions/README.md:15-17 intro, verbatim (ADR-JW9N) |
| R29 | The status line can change | CUT-ELSEWHERE | template.md:31-34; change-sidecar-spec:142, :235 |
| R31 | A status change adds its date and PR | CUT-ELSEWHERE | change-sidecar-spec:142-143, :235; template.md:13; every status line |
| R50 | Delete a spec defect when its content PR lands | CUT-ELSEWHERE | change-sidecar-spec:152-153 step 11; also a case of R49 |
| R57 | Script in scripts/ of the log | CUT-ELSEWHERE | AGENTS.md:115 (ADR-EY8R); template.md:42-43 |
| R58 | The Evidence section names the script | CUT-ELSEWHERE | template.md:42-44 |
| R67 | The workflow is normative for the process | CUT-ELSEWHERE | model-addition-workflow/README.md:10-13; exporter-guide/sidecars/README.md:10-14; AGENTS.md:19-22 |
| R68 | The exporter guide is normative for its added rules | CUT-ELSEWHERE | exporter-guide/sidecars/README.md:14-16; AGENTS.md:19 |
| R69 | The spec is normative for the meaning of a sidecar | CUT-ELSEWHERE | specs/model-sidecar/AGENTS.md:9; author-sidecar:19; propose-sidecar-change:19 |
| R70 | The bootstrap kit takes these rules | CUT-ELSEWHERE | AGENTS.md:133-134 |
| R73 | A decision can be accepted before its spec text lands | CUT-ELSEWHERE | change-sidecar-spec:215 and :49 |
| R74 | The spec text comes in a later content PR | CUT-ELSEWHERE | change-sidecar-spec:105-113; propose-sidecar-change:204-205 |
| R78 | Do not make a new all-digit ID | CUT-ELSEWHERE | AGENTS.md:120 gives `--new`; new_id() draws a letter first |
| R83 | Run `check_decision_log.py --new` | CUT-ELSEWHERE | AGENTS.md:120; template.md:6-7; propose-sidecar-change:222 |
| R84 | Give the entry the ID of the `new:` line | CUT-ELSEWHERE | AGENTS.md:120; propose-sidecar-change:222-223 |
| R94 | To change an ID, run `--new` | CUT-ELSEWHERE | AGENTS.md:120; tool docstring line 46; the kept R93 sentence names `--new` |
| R98 | Ask the user before a PR title or body change | CUT-ELSEWHERE | AGENTS.md:151-152 |
| R105 | Do not cite or link plans/ | CUT-ELSEWHERE | AGENTS.md:143-144 |
| R106 | Git does not track plans/ | CUT-ELSEWHERE | AGENTS.md:143 |
| R108 | Cite an entry as a link with `ADR-<ID>` | CUT-ELSEWHERE | AGENTS.md:122-123 |
| R109 | Also for an older entry | CUT-ELSEWHERE | AGENTS.md:126 |
| R110 | New text is each text that you write | CUT-ELSEWHERE | AGENTS.md:124-125 |
| R111 | Path in a reply or a plan | CUT-ELSEWHERE | AGENTS.md:125 |
| R112 | Commit body writes `ADR-<ID>` with no link | CUT-ELSEWHERE | AGENTS.md:127 |
| R114 | Another repo's entry: repo name and prefix | CUT-ELSEWHERE | AGENTS.md:128; propose-sidecar-change |
| R115 | Permalink when the entry is on the default branch | CUT-ELSEWHERE | AGENTS.md:128-129; duplicates R104 |
| R121 | Commit subject ends with `(ADR-<ID>)` | CUT-ELSEWHERE | AGENTS.md:121; propose-sidecar-change:285-286 |
| R122 | A proposal is a `proposed` entry | CUT-ELSEWHERE | propose-sidecar-change:27; specs/model-sidecar/AGENTS.md:38-40; template.md:31-32 |
| R123 | Its source is a `proposal` bundle | CUT-ELSEWHERE | specs/model-sidecar/AGENTS.md:36-38; propose-sidecar-change:26-27, :83 |
| R124 | Phase 2 gives its parts | CUT-ELSEWHERE | propose-sidecar-change:14-17 and :46 |
| R125 | An empty part says `none` and the reason | CUT-ELSEWHERE | propose-sidecar-change:150 |
| R126 | A gap goes on the spec-defect list | CUT-ELSEWHERE | specs/model-sidecar/AGENTS.md:33-35; propose-sidecar-change:75-76 |
| R127 | A gap is not an entry | CUT-ELSEWHERE | specs/model-sidecar/AGENTS.md:35-40; propose-sidecar-change:77, :196-198 |
| R128 | Record a new version in the same entry | CUT-ELSEWHERE | propose-sidecar-change:183-185, :273 |
| R129 | Replace the record with a byte copy | CUT-ELSEWHERE | propose-sidecar-change:274 |
| R130 | Status line adds `recorded again ...` | CUT-ELSEWHERE | propose-sidecar-change:282 |
| R131 | Procedure B step 1 stops a landing until then | CUT-ELSEWHERE | propose-sidecar-change:267-268; change-sidecar-spec:106-109 |
| R132 | After `accepted` the record does not change | CUT-ELSEWHERE | propose-sidecar-change:271-272, :296 |
| R133 | ID, slug and status stay | CUT-ELSEWHERE | propose-sidecar-change:273 |
| R134 | Keep the old "Before acceptance" items in order | CUT-ELSEWHERE | propose-sidecar-change:275-276 |
| R135 | Tick a closed item with its reason | CUT-ELSEWHERE | propose-sidecar-change:277 |
| R136 | Mark a changed item `(changed <date>)` | CUT-ELSEWHERE | propose-sidecar-change:278 |
| R137 | Put a new item last, marked `(new <date>)` | CUT-ELSEWHERE | propose-sidecar-change:279 |
| R138 | Change Decision, Reason, Evidence only where the version changes them | CUT-ELSEWHERE | propose-sidecar-change:280-281 |
| R139 | Change the index row when a cell changes | CUT-ELSEWHERE | propose-sidecar-change:283-284 |
| R140 | Use a non-spec commit | CUT-ELSEWHERE | propose-sidecar-change:285, :257-258; change-sidecar-spec:50 |
| R141 | A contributor that packs a new version tells the user | CUT-ELSEWHERE | propose-sidecar-change:171-173 |
| R142 | `**Depends on:**` line | CUT-ELSEWHERE | template.md:14 and :36-37 |
| R147 | Entries in ASD-STE100 | CUT-ELSEWHERE | AGENTS.md:15-17 |
| R148 | Short sentences, active voice, one instruction | CUT-ELSEWHERE | AGENTS.md:18 |
| R149 | "must" is the requirement word | CUT-ELSEWHERE | AGENTS.md:19 |
| R150 | Technical names stay unchanged | CUT-ELSEWHERE | AGENTS.md:20 |

## CUT-TOOL (a check reports the breach with a clear fix)

| id | short text | class | evidence |
|---|---|---|---|
| R7 | All logs have one ID space | CUT-TOOL | id_space_errors() :295-310; `--new` draws from every log; test_one_id_in_two_logs_fails |
| R36 | Active and Proposed tables and their forms | CUT-TOOL | STATUS_FORMS/TABLE_FILES :110-121; "status 'proposed' must not be in the Active table" |
| R37 | Historical table and its forms | CUT-TOOL | same; "the Historical table must be in historical.md"; test_done_is_historical |
| R38 | Status cell holds only a form of its table | CUT-TOOL | status_match() fullmatch :234; "unknown status '...'" |
| R39 | `XXXX` is not `proposed` or `rejected` | CUT-TOOL | NOT_DECIDED in status_errors(); "names an entry that is 'proposed'" |
| R40 | Decision cell 160 characters or fewer | CUT-TOOL | DECISION_CELL_LIMIT = 160; "Decision cell has N characters, limit 160"; z934 citation moved to the status bullet |
| R41 | Proposed row has a Section cell | CUT-TOOL | table_rows() width 4; SECTION regex; propose-sidecar-change:245-246 |
| R51 | 18,000 for each README.md | CUT-TOOL | INDEX_LIMIT; check() "{label}: {used} characters, limit {limit}" |
| R52 | 20,000 for each open-work.md | CUT-TOOL | OPEN_WORK_LIMIT; same message |
| R53 | 6,000 for each entry after 0025 | CUT-TOOL | ENTRY_LIMIT, LAST_UNLIMITED_ENTRY, unlimited(); remedy is R56 (kept) |
| R54 | 160,000 for the read path | CUT-TOOL | READ_PATH_LIMIT, read_path_size(); remedy is R46/R48 (kept) |
| R75 | ID: 4 characters from the alphabet | CUT-TOOL | ALPHABET/ID regex :101-107; name_errors() "is not a valid ID"; `--new` composes the ID |
| R76 | First character of a new ID is a letter | CUT-TOOL | new_id() draws a letter first; regex rejects a hand-made digit-first ID |
| R81 | IDs that differ only in case are one ID | CUT-TOOL | entry_id() upper-cases :222-224; id_space_errors(); name_errors() .upper(); JW9N citation kept on the R79/R80 bullet |
| R82 | Run `git fetch --all` first | CUT-TOOL | fetch_note() :505-517 prints the fetch reminder on each stale `--new` run; propose-sidecar-change:222 |
| R86 | Add the index row in the same PR | CUT-TOOL | check() "{n} index rows, expected 1"; status_errors() wrong-table message; test_repository_log_passes |
| R89 | Act on each `re-ID:` line | CUT-TOOL | main() returns 1 on a `re-ID:` line; pre-push hook blocks the push |
| R90 | Collision verdict order | CUT-TOOL | rank() in new_lines() :659-664 computes it and prints `keep:`/`re-ID:` |
| R91 | An uncommitted file loses | CUT-TOOL | rank() third key :661; docstring line 49 |
| R92 | Refs that are not collisions | CUT-TOOL | sources.quiet, SKIPPED_BRANCHES, `renamed` handling :545-555, :648-652 |
| R95 | Rename the file to the new ID | CUT-TOOL | `re-ID:` names the file; exit 1 until renamed; name_errors() heading mismatch |
| R96 | Change the ID in heading and index row | CUT-TOOL | name_errors() :331-337; check() "row links to missing file" |
| R102 | No two index rows with one ID | CUT-TOOL | id_space_errors() :303-309; check() "{n} index rows, expected 1" |
| R104 | Permalink with a full 40-character SHA | CUT-TOOL | check_links.py check_file() :114-118 "GitHub link must pin a full SHA"; AGENTS.md:128-130 |
| R119 | Write an ID in YAML front matter in quotes | CUT-TOOL | no front matter holds an entry ID; the bundle response is JSON and intake_bundle.py verify rejects an unquoted value |

## CUT-DEFAULT (Claude does it without the sentence)

| id | short text | class | evidence |
|---|---|---|---|
| R15 | The `<kind>` list | CUT-DEFAULT | no tool reads the kind word; the one parsed kind `re-ID from XXXX` stays as the example in the kept edit bullet |
| R16 | An old `renumber from NNNN` line stays | CUT-DEFAULT | R13 forbids every other body edit; Claude does not strip such lines unprompted |
| R17 | A `proposed` entry can change | CUT-DEFAULT | complement of README.md:17-18; propose-sidecar-change:264-285 changes one step by step |
| R24 | The heading must state the rule | CUT-DEFAULT | tautological once R22-R23 stand (kept in the merged sentence anyway) |
| R28 | A change of a self-stated rule supersedes the linking entry | CUT-DEFAULT | plain application of README.md:15 with the R27 carve-out; JW9N citation kept on the change bullet |
| R32 | An absorbed entry is superseded when a rule changes | CUT-DEFAULT | follows from README.md:15 and the R30 transition list; JW9N citation kept on that transition |
| R35 | The used-evidence Decision cell keeps the result | CUT-DEFAULT | Claude keeps the cell; the 160 limit is enforced |
| R42 | A new section ID is allowed | CUT-DEFAULT | SECTION regex accepts any well-formed ID; the worst case is `none` in one cell |
| R85 | Create its file immediately | CUT-DEFAULT | the agent writes the file next anyway; `--collisions` at pre-push catches a redraw |
| R97 | The `git grep` command for citations | CUT-DEFAULT | the agent greps the old ID; check_links.py and name_errors() report each stale link |
| R101 | Do not reuse an ID that an entry had on development | CUT-DEFAULT | `--new` excludes every ID in every tree; residual chance about 1 in 720,000 |
| R103 | Cite a tracked file with a relative link | CUT-DEFAULT | the default form; AGENTS.md:192; specs/model-sidecar/AGENTS.md:11; check_links.py verifies |
| R145 | Do not import from another repo | CUT-DEFAULT | not a default move; specs/model-sidecar/AGENTS.md:58 keeps exporters read-only; CI has no sibling |
| R146 | The rules do not follow another repo's log | CUT-DEFAULT | an agent applies the rules of the repo it works in |

## CUT-DESCRIPTION (describes; no action depends on it)

| id | short text | class | evidence |
|---|---|---|---|
| R3 | A root log and a log for each module in LOG_DIRS | CUT-DESCRIPTION | AGENTS.md:49-51, :106-111 name both logs; check() reports a LOG_DIRS folder without README.md |
| R25 | Then that document is the only source | CUT-DESCRIPTION | duplicate of R44; the absorb bullet carries the meaning |
| R44 | Then that document is the source of the rules | CUT-DESCRIPTION | consequence of R43; the entry leaves the read path |
| R55 | Proposed and Historical entries are not in the read path | CUT-DESCRIPTION | read_path_size() :412-428; the error label names the parts |
| R59 | Run the tool to see the size and the 80% warnings | CUT-DESCRIPTION | warnings() runs only in main(); the limit fails later with the same cheap fix |
| R60 | The doc tests run the same check | CUT-DESCRIPTION | tools/tests/test_decision_log.py; AGENTS.md:84 |
| R61 | Counts characters after CRLF to LF | CUT-DESCRIPTION | size() :164-166 |
| R62 | What the tool checks | CUT-DESCRIPTION | tool docstring :14-29 |
| R63 | A warning does not fail the doc tests | CUT-DESCRIPTION | main() :685-690 |
| R64 | An entry does not warn | CUT-DESCRIPTION | warnings() :400-409 |
| R65 | A PR can lower a limit | CUT-DESCRIPTION | permission nothing depends on |
| R71 | Kit limits 14,000 and 220,000 | CUT-DESCRIPTION | tools/sync_bootstrap_kit.py:41-42; test_bootstrap_kit.py:30-36 |
| R72 | The kit keeps an optional mirror rule | CUT-DESCRIPTION | kit feature; AGENTS.md:133-139 |
| R77 | Entries 0001 to 0048 keep their numbers | CUT-DESCRIPTION | ID regex accepts \d{4}; the re-ID guard is the kept R93 |
| R87 | The index order is the order of addition | CUT-DESCRIPTION | no tool or rule depends on row order |
| R88 | The pre-push hook runs `--collisions` | CUT-DESCRIPTION | .pre-commit-config.yaml:18-25; tool docstring :58-59 |
| R113 | The older form `ADR-[x64y](…)` stays valid | CUT-DESCRIPTION | ENTRY_LINK accepts it; AGENTS.md:153 and stack-commit:12 use it; R117 forbids the sweep |
| R116 | A bare ID in older text is an entry of this log | CUT-DESCRIPTION | resolved by file name; the only wrong action is R117's subject |

## Citations that disappear with the cut rules

Targets that leave the Rules (the links still resolve from `decisions/`):

- `template.md` at L3 (R2). The intro of the index keeps `[template.md](template.md)`. The link also
  stays in the absorb bullet (R43).
- `GN3D-module-decision-logs.md` at L8 (R7, one ID space) and at L96 (R105/R106, `plans/`). The
  citation stays once, on the absorb bullet (R43). AGENTS.md:112-114 and :143-144 cite ADR-GN3D for
  the cut rules.
- `JW9N-restate-a-kept-rule-by-a-link.md` at L95 (R104, the permalink rule) and at L113 (R121, the
  commit subject). The four other JW9N citations stay with their groups: the edit list (from R15),
  the change bullet (from R28), the absorbed-to-superseded transition (from R32) and the case rule
  (from R81). The L113 citation now closes the citation bullet (R117, R118, R120), which JW9N item 4
  governs.
- `x64y-draft-exporter-guide-folder.md` at L64 (R67, the normative workflow). AGENTS.md:55-56 cites
  ADR-x64y for the same fact. The code-span example `[ADR-X64Y](x64y-...)` at L100 (R108) also
  leaves.
- `NSR2-adr-citations-as-links-in-each-text.md` at L104 (R108-R112) and L107 (R115). Both runs are
  in AGENTS.md:121-129. No NSR2 citation stays in the Rules; NSR2 item 6 says the citation bullet of
  the Rules states items 1 to 5, so NSR2 needs a chain-rule citation at AGENTS.md section 5 or an
  edit of item 6 when this rewrite lands.
- `FADS-hand-over-bundles-in-intakes.md` at L119 (R122-R127) and L129 (R128-R141). The
  propose-sidecar-change skill and specs/model-sidecar/AGENTS.md state these rules.
- `../specs/model-sidecar/model-addition-workflow/README.md` at L62 (R67), `hand-over.md` at L115
  (R123) and `phase-2-proposal.md` at L116 (R124).

Moved, not lost: `z934-decision-log-index-and-read-path.md` from L39 (R40, the 160-character cell)
to the end of the status bullet (R30, R33, R34, R45; z934 items 2, 4 and 6).
