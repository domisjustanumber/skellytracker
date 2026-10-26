# a33q — One case form for the test vectors of skellytracker and of a proposal

**Status:** accepted, 2026-10-26 (user).

## Decision

1. **One writer.** `tools/make_vectors.py` stays the only writer of
   `specs/model-sidecar/vectors/`. A vector file in this repo has
   `generated_by: tools/make_vectors.py`. Nobody edits a vector file by hand.
2. **One case form.** The vectors of a proposal (part 4 of the change proposal template) use the case
   form of `tools/make_vectors.py`. `tools/tests/test_vectors.py` checks this form for the files of
   this repo and for that case form. The keys of a case are `id`, `function`, `params`, `input`,
   `expect`, `unproject`, `tolerance`, `compare` and `verified_against`.
3. **`function`.** An optional key. It names the function of the reference implementation that the
   case runs. A reference function returns a mapping with the keys of `expect`.
4. **`tolerance` and `compare`.** `tolerance` stays the default for each fractional value of a case.
   The optional `compare` gives the tolerance of one field, with `atol` or `period` or both. A case
   with a fractional value has `tolerance` or `compare`. A case without a fractional value has no
   `tolerance`.
5. **Errors by rule ID.** A case that expects a validation error writes
   `expect: {error: V-<section-id>-<n>}`, and no other `expect` key. The rule must be in a section
   file. An error with no rule is a gap of the spec.
6. **NaN and infinity.** The generator writes `.nan`, `.inf` and `-.inf`. The data check treats
   NaN as equal to NaN.
7. **Digits.** The default stays 6 decimals. A builder can write each expected value exactly
   (`digits=None`).
8. **Exporter entries.** A `verified_against` entry is a skellytracker function (`path::function`),
   which the test imports, or an exporter function (`{<Exporter repo>: <file>::<function>}`), which
   the test checks for its form only.
9. **Reference import.** `make_vectors.load_reference(section)` loads
   `specs/model-sidecar/reference/<section_module>.py` by its path. The builders and the tests use it.
10. **Size.** A vector file must be smaller than 64 KiB.
11. **Landing check.** When a proposal lands, the generator calls the reference implementation and
    writes the file again. Its `cases` must be equal to the cases of part 4. If they are not equal,
    the landing stops. This check proves the copy and the generator wiring. It does not verify an
    independent implementation.

## Reason

- Six recorded proposals list the same item in "Before acceptance": the template form (`function`,
  `compare`, `generated_by` of the reference file, error messages) fails `test_vectors.py`. They ask
  for one decision for all proposals, in a non-spec tools PR before the content PRs.
- Each new key is optional. The 9 vector files of this repo do not change
  (`uv run python tools/make_vectors.py --check` gives "vectors are current").
- A rule ID is the stable name of a refusal in the spec. An error message differs between
  implementations, so a message cannot be compared.
- `heatmap-decode-refinement`, `landmark-depth-divisor` and `landmark-extra-outputs` need two
  tolerances in one case, more than 6 digits, or NaN values. The rotated crop of
  `roi-transform-and-source` needs a period for an angle.
- Procedure C of the skill `change-sidecar-spec` adds an exporter function to `verified_against`.
  Before this entry, the test imported each entry as a skellytracker function, so that step failed.
- `landmark-extra-outputs` has a vector file of about 35 KB. The cases are still small arrays.

## Consequences

- Each recorded proposal with vectors must give part 4 again in this form. skellytracker records it
  again (ADR-[b1c0](b1c0-adr-citation-prefix.md), the record-again rules).
- The generator no longer refuses NaN. A builder defect that makes NaN gives a case with a
  `tolerance`, and the hand-computed anchors of `test_vectors.py` still check the values.

## Evidence

- `tools/tests/test_vectors.py`: `check_case` and
  `test_the_generator_writes_the_case_form_of_a_proposal` render and check each new form.
- The "Vectors and tooling" items of `specs/model-sidecar/proposals/*/proposal.md`, for example
  [`keypoint-visibility`](../../specs/model-sidecar/proposals/keypoint-visibility/proposal.md) and
  [`landmark-depth-divisor`](../../specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md).

## Alternatives rejected

- **Change the tools to the template form in full.** A per-field `compare` in place of `tolerance`
  changes all 9 files and each test that reads `tolerance`.
- **Choose the function by the prefix of the case ID.** The choice is then implicit, and the test
  cannot check it.
- **Copy the vector file of the exporter.** Then two writers exist, and the generator test fails.
- **Expect the error message.** See Reason.
