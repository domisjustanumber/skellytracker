# FDTD — Evidence sources and exporter permalinks

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

This entry supersedes [ADR-0030](0030-no-private-data.md) in full. Item 1 restates the rules of 0030
by a link ([ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md)). Items 2 to 6 are new.

1. **Private data.** [Private data](../AGENTS.md#8-private-data) in `AGENTS.md` states each rule of
   0030: the list of private data, the `plans/` rule, the redaction of a found leak, the tools and
   the GitHub settings. That heading is the only source of these rules.
2. **Exporter permalinks.** A GitHub permalink to a repo of a freemocap exporter is not a private
   URL. This is also true when the repo is private. A reader with no access cannot open the link. The
   SHA and the path still identify the source. The exporter repos are on a personal GitHub account
   of the user. The permalink can contain the user name of that account. That user name stays out of
   prose. `AGENTS.md` [Private data](../AGENTS.md#8-private-data) states this rule.
3. **The primary rule.** An exporter document is a secondary source. A user decision cannot make it
   primary. When a passing committed check maps a claim of the document to an upstream file and
   line, the submission cites that upstream line as primary. It also cites the check ID and the
   document line as support. The workflow
   [Rules](../specs/model-sidecar/model-addition-workflow/rules.md) state this rule.
4. **User decisions.** A user decision is not evidence. A submission names each decision in words,
   with no item number and no plan path. The exporter log records an exporter decision. Part 1 of a
   proposal lists each plan decision about the spec. The user confirms or refuses each one before
   acceptance. The decision entry of the proposal records it in words at acceptance.
   [User decisions](../specs/model-sidecar/model-addition-workflow/rules.md#user-decisions) states
   this rule. The proposal template, `propose-sidecar-change` and Procedure B step 10 of
   `change-sidecar-spec` link to it.
5. **Sources.** The citation forms of the decision-log [Rules](README.md#rules) also apply to an
   intake, a proposal, a reference file and spec guidance. The workflow adds forms for a tag, a
   commit off the default branch, a released package file, an untracked output, a recorded proposal
   and a proposal that is not recorded. A bundle is not a source. Only the tracked copy of its file
   is a source.
   [Sources](../specs/model-sidecar/model-addition-workflow/rules.md#sources) states these forms.
   This is a rule of this entry. It does not change the Rules of the decision log.
6. **A chosen value with no code.** A row for a value that the contributor chooses does not cite a
   plan. If no code writes the value, the row says `none yet (no code)`.

## Reason

- Proposals called an exporter document "primary by user designation". No rule allowed it, and no
  tracked file recorded it. A designation makes a private, secondary document into primary
  evidence. The workflow Rules exist to prevent that.
- The fix exists for MediaPipe. The tracked claim check of MediaPipe-Exporter maps each claim ID of
  its document to an upstream file and line at a full SHA. A citation of the upstream line is public
  and primary.
- Proposals relied on decisions that only an untracked plan held, cited by item number. A reader of
  a tracked file cannot find them. Some of them set skellytracker rules, which an exporter log
  cannot decide.
- Proposals used citation forms that no rule gave: a tag with no SHA, short SHAs, package files,
  untracked outputs and a proposal that cites another proposal.
- Tracked files already held permalinks to private exporter repos. The only record of the user's
  approval was inside a proposal. The account name is already public through the public fork of
  skellytracker, so a text pin protects nothing.

## Consequences

- An implementer with no access to an exporter repo cannot open its permalinks. The primary
  evidence of a check-backed claim is upstream and public.
- A recorded proposal that cites a plan item number or a "user designation" must change in a new
  version before acceptance.
- A spec decision of a plan needs the confirmation of the user in the proposal entry.

## Evidence

- `gh` 2.92.0, 2026-10-28: OpenMMLab-Exporter, MediaPipe-Exporter, Roboflow-Exporter,
  Ultralytics-Exporter and Qualcomm-Exporter are `PRIVATE`. `freemocap/skellytracker` and its fork
  `origin` are `PUBLIC`.
- The claim check of MediaPipe-Exporter:
  [`check_doc_claims.py`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/notes/decisions/scripts/check_doc_claims.py)
  pins the upstream repo at a full SHA (`PIN`) and maps each claim ID to a file and a line range.
- `git grep` on 2026-10-28: 19 tracked files outside `plans/` hold a permalink to an exporter repo,
  for example [`open-work.md`](open-work.md) (the `vNEXT` release step).

## Alternatives rejected

- **Allow the user to designate an exporter document as primary.** The evidence stays private and
  secondary.
- **Public sources only, with a text pin for each private repo.** It needs a redaction of the
  tracked permalinks and a new tool check. The owner name is already public.
- **Extend the source rule of the decision log to submissions.** That changes an accepted rule of the
  Rules. The forms of this entry are a workflow rule.
- **A new evidence file in the workflow.** `rules.md` already owns the evidence rules.
