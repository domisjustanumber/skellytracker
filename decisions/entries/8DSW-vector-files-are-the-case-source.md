# 8DSW — Vector files are the case source

**Status:** absorbed into [`change-proposal.md#4-vectors`](../../specs/model-sidecar/templates/change-proposal.md#4-vectors), [`spec-edit-rules.md#examples-and-vectors`](../../.claude/skills/change-sidecar-spec/spec-edit-rules.md#examples-and-vectors), [`change-sidecar-spec/SKILL.md#procedure-b-land-an-accepted-proposal`](../../.claude/skills/change-sidecar-spec/SKILL.md#procedure-b-land-an-accepted-proposal), [`reference-implementations.md#full-section`](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#full-section), [`reference-implementations.md#when-the-other-section-has-no-module`](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#when-the-other-section-has-no-module), [`reference-implementations.md#code-for-the-cases`](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#code-for-the-cases), [`reference-implementations.md#run-a-module-that-imports-another-module`](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#run-a-module-that-imports-another-module), [`AGENTS.md#repository-instructions`](../../AGENTS.md#repository-instructions), [`make_vectors.py`](../../tools/make_vectors.py), [`vector_form.py`](../../tools/vector_form.py), [`post.det.selection.nms.yaml`](../../specs/model-sidecar/vectors/post.object.selection.nms.yaml), [`post.det.selection.top_k.yaml`](../../specs/model-sidecar/vectors/post.object.selection.top_k.yaml), [`post.det.selection.none.yaml`](../../specs/model-sidecar/vectors/post.object.selection.none.yaml), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes [ADR-TA0G](TA0G-vector-cases-and-reference-modules.md) in full. Items 1 to 6
are new. Item 3 replaces TA0G item 3, and item 5 replaces TA0G item 5. Item 7 restates the other
rules of TA0G by links ([ADR-Z05A](Z05A-essential-decision-log-rules.md)).

1. **One source for each case.** A landed case is only in
   `specs/model-sidecar/vectors/<section>.yaml`. The generator holds no copy of it. A person, or
   `make_vectors.py land`, writes the author keys: `section`, `notes`, `tolerance`, `checks`,
   `verified_against` or `unverified`, and the case keys `id`, `note`, `function`, `checks`,
   `params`, `input`, `compare` and `verified_against`. `make_vectors.py` writes `expect` on each
   run, with 6 decimals. Only the author of a data-only case (item 2) writes its `expect`.
2. **The case form.** `note` is a case key. A `no-rule` case must have one. The reading notes are a
   top-level `notes` list. One file-level `tolerance` replaces the case `tolerance`. `compare`
   stays. A case is one call: an Inverse case has the `id` `<forward id>-inverse` and
   `function: inverse`. A selection case always gives `boxes_xyxy`. Without `function`, a case
   calls `run`. A validator case with `function: none` is data only: the generator does not run it.
   The exact-digits option of a33q item 7 goes. `spec_revision` and `generated_by` go. A 2-line
   header names the keys that `make_vectors.py` writes and says that hosts ignore `checks`. The keys
   of `params` and `input` are disjoint, and `function` must be in the producer.
   `tools/vector_form.py` checks this form for the generator, the tests and
   `intake_bundle.py verify`.
3. **The producer.** The producer of a section is
   `specs/model-sidecar/reference/<section_module>.py` when it exists, else
   `tools/vector_formulas/<section_module>.py`. It has `run(params, input)` and, for an inverse,
   `inverse(params, input)`. The generator calls each case through `make_vectors.outcome`, where a
   `ValueError` is a refusal. A broken case or formula calls `vector_form.defect`. Its `CaseDefect`,
   and each other exception, stops the generator. An `error` result without the check `refused`
   also stops it. While a reference is the producer and the formula module has `run`, the two must
   agree within the tolerance. No rule keeps that `run`.
4. **Named checks.** Each claim of a case is a check in the `CHECKS` registry of its formula
   module. A case or a file names its checks in `checks`. A check calls the producer. An unknown
   name stops the generator.
5. **Landing.** Step 9 of Procedure B runs
   `make_vectors.py land <part 4 file> [--contribution <file>...] --replaces <id>...`. It checks the
   form. It keeps the current cases and puts a part 4 case in the place of the case with its `id`.
   That overlap must equal `--replaces`. A contribution case with a known `id` must agree with that
   case, ignoring `verified_against`. Each other new case goes at the end. Then the tool runs the
   landed producer and compares each given `expect` within the tolerance. It writes the file only
   when each check passes and the file is 256 KiB or smaller.
6. **The exporter command `fill`.** Before `pack`, an exporter agent runs
   `make_vectors.py fill <bundle vectors file> --reference <bundle reference folder>` in the
   environment of this checkout. It writes `expect` into that file only, in the bundle folder of the
   agent ([ADR-FADS](FADS-hand-over-bundles-in-intakes.md)). The root `AGENTS.md` lists it.
7. **The rules that stay.** TA0G items 1, 2, 4 and 6, the last sentence of item 3, and the a33q and
   0013 rules of item 7 stay, except where items 1 to 6 change them. They stay where TA0G item 7
   puts them: [4. Vectors](../../specs/model-sidecar/templates/change-proposal.md#4-vectors),
   [Examples and vectors](../../.claude/skills/change-sidecar-spec/spec-edit-rules.md#examples-and-vectors),
   [Reference implementations](../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#reference-implementations)
   and
   [Rules for each spec edit](../../.claude/skills/change-sidecar-spec/SKILL.md#rules-for-each-spec-edit).
   TA0G item 1 loses its clause for a sidecar before `vNEXT`: no case uses it.

## Reason

- Each of the 129 cases was in two places: a Python literal in a builder and the vector file. A
  landing translated part 4 into builder code by hand.
- Under TA0G item 3, a builder bug that raised `ValueError` became a published `no-rule` case.
- A contributor rounded and set the tolerance with its own code. No tool checked the form of a
  bundle vector file.
- `spec_revision` changes each `vectors_sha256` at each revision. `generated_by` changes it at each
  landing. The folder and the producer give the same facts.
- A case with `unproject` mixed two calls.

## Consequences

- The next run removes a hand edit of `expect`. `--check` finds a file that nobody regenerated, not
  a wrong edit.
- The renderer writes a whole float as an integer. A reference that branches on the dtype can
  differ. The template rule "cast each input" stays, and `fill` shows the difference.
- Each edit of a vector file changes `vectors_sha256` and so cancels a pending run. A hash of the
  cases only is later work.

## Evidence

- `tools/vector_form.py`, `tools/vector_formulas/` and `run_checks` in `tools/make_vectors.py`.
- `tools/tests/test_vectors.py`: the form, check-registry, cross-folder import, anchor, `outcome`
  and renderer tests.

## Alternatives rejected

- **One Python module for each section, with case rows.** Python stays a second copy of each case,
  and a landing still copies part 4 by hand.
- **Reference modules first.** skellytracker would publish its own reading of the text as spec
  code. That weakens exporter independence and removes Procedure C.
- **No data-only validator case.** A rule would then wait for a function.

_Edited 2026-11-11 (this PR): link repair._
