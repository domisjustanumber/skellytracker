# NSR2 — ADR citations as links in each text

**Status:** accepted, 2026-10-29 (user; PR: pending); superseded by [Z05A](Z05A-essential-decision-log-rules.md), 2026-10-29 (user; PR: pending).

## Decision

This entry changes the citation rule of the [Rules](../README.md#rules). [ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md)
item 4 restates that rule by a link to the Rules. Thus this entry follows the chain rule of [ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md)
item 3. It cites itself next to the changed rule, and it does not supersede [ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md). [ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md) item 2
names `(ADR-<ID>)` only as the placeholder for the cited ID. This entry does not change that form:
in a file, the parentheses hold the link of item 2 below.
[ADR-FADS](FADS-hand-over-bundles-in-intakes.md) item 4 names the reason "Resolved by ADR-<X>" in
the same way. In a file, the ID in that reason is the link of item 2 below, so this entry does not
supersede FADS. No other entry changes status.

1. **Scope.** The citation rule applies to each text that an agent writes: a tracked file, a plan, a
   PR body and a reply to the user. "New text" in the Rules includes each of them.
2. **The form.** A citation of an entry is a Markdown link. Its link text is `ADR-<ID>`, with the ID
   in upper case. Example: [ADR-JB5J](JB5J-one-batch-form-for-each-sidecar.md). In a tracked file,
   the path is relative to the file. In a reply or a plan, the path is relative to the repo root or
   to the file.
3. **Commit messages.** A commit message cannot hold a working link. The subject of a commit that
   adds or changes an entry ends with `(ADR-<ID>)`, as before. The body writes `ADR-<ID>` with no
   link.
4. **Another repo.** Cite an entry of another repo with the repo name and `ADR-<ID>`, for example
   "OpenMMLab-Exporter ADR-0020". When the entry file is on the default branch of that repo, also
   link it with a GitHub permalink that pins a full 40-character SHA. Cite a provisional entry of
   another repo by the repo name, the PR number and the slug, as before.
5. **The exceptions that stay.** Do not use the prefix in a file name, a heading, an index row, a
   status line or a YAML value. Write an ID in YAML front matter in quotes. Older text stays: a bare
   ID in older text is an entry of this log, and the older form `ADR-[x64y](…)` stays valid. Do not
   edit a decided entry only to add or move the prefix or the link.
6. **The sources.** The citation bullet of the [Rules](../README.md#rules) states items 1 to 5.
   [`AGENTS.md`](../../AGENTS.md#5-decision-log) section 5 states them in short form. The
   `change-sidecar-spec` skill and the
   [Responses](../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses) of the
   hand-over workflow write the "Resolved by" reason as a link.
7. **The kit.** The bootstrap kit takes items 1 to 4 and the parts of item 5 that apply to a new
   repo, as [`AGENTS.md`](../../AGENTS.md#5-decision-log) section 5 requires. A new repo has no older
   text, so the kit does not take the exceptions for older text. Its `AGENTS.md`, its decision-log
   Rules and its guide state these items. The kit templates change by hand in the same commit.

## Reason

- The user decided on 2026-10-29: "It must be the link as well as the ADR- prefix when quoting
  ADRs." The user also asked to sync the change into the kit.
- The Rules said "In new text". Agents read "new text" as files only. They wrote bare IDs, for
  example "JB5J", in replies to the user. A reader cannot open a bare ID, and a bare ID can look
  like a word.
- A commit message shows no links in `git log`. A Markdown link there is noise, so the body keeps
  the plain `ADR-<ID>` form.

## Consequences

- A reply that names an entry is longer. Each citation carries a path.
- Plans now hold links. The rule "Do not cite or link `plans/`" does not change: it is about a
  tracked file that cites a plan.

## Alternatives rejected

- **The prefix with no link in a reply.** The user rejected it. A reader cannot open the entry.
- **Links in commit bodies.** `git log` does not render them.
- **Supersede [ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md).** [ADR-JW9N](JW9N-restate-a-kept-rule-by-a-link.md) states the citation rule only by its link to the Rules. Its item 2
  names `(ADR-<ID>)` only as a placeholder. The chain rule applies, so a supersession is not
  necessary.

_Edited 2026-10-29 (this PR): link repair._
