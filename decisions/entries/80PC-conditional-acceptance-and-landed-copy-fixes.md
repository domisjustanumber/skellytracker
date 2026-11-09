# 80PC — Conditional acceptance and fixes in the landed reference copy

**Status:** accepted, 2026-11-09 (user; PR: pending).

## Decision

1. **Conditional acceptance.**
   [Conditional acceptance](../../specs/model-sidecar/model-addition-workflow/hand-over.md#conditional-acceptance)
   is the home of these rules.
   - When the user accepts a proposal on a condition, the response is `needs-contributor`. Its
     `findings` list each item to close. The entry stays `proposed`.
   - Under "Before acceptance", the entry gets the line
     `User decision YYYY-MM-DD: accept when proposal bundle version N closes X, Y`.
   - When version N closes each named item and changes no other meaning, version N is the
     acceptance of the user. The session does not ask for the acceptance again. The safety review
     and the copy approval of each reference file of version N stay.
   - The session records version N in one non-spec commit before the content commit, and deletes
     the closed items
     ([Record a new version](../../.claude/skills/propose-sidecar-change/SKILL.md#record-a-new-version)).
   - The response `accepted` comes only after the condition is met.
   - The `pack` refusal of [ADR-ZXD7](ZXD7-bundle-process.md) item 3 does not change.
2. **Notes at acceptance.** At acceptance, the heading "Before acceptance" of the entry becomes
   "Notes at acceptance". The closed items go, and the `User decision` line of a conditional acceptance goes. Procedure B step 10 of
   `change-sidecar-spec` is the home of this rule.
3. **Fixes in the landed copy.**
   [Changes at acceptance](../../specs/model-sidecar/model-addition-workflow/hand-over.md#changes-at-acceptance)
   is the home of this rule. The landed copy in `specs/model-sidecar/reference/` is not the record.
   The non-spec commit of Procedure B step 13 can fix docstrings, comments, status notes and
   citation or permalink forms in it. It changes no code and no vector value. The response lists
   each fix in `changes`. A later bundle or version that changes the module starts from the landed copy. At
   Procedure B step 6, a difference only in docstrings or comments is not an older base.

## Reason

- On 2026-11-06, the user accepted four proposals on the condition that the contributor packs a
  new version first. Each one cost a new exporter version and a "Record ... vN" commit on
  2026-11-09. No tracked file held the four decisions for 2.5 days.
- After the rewrites of "Before acceptance", the [ADR-52NQ](../../specs/model-sidecar/decisions/entries/52NQ-model-id-suffix.md) entry had 6081 of 6000 characters, and the
  [ADR-3S5G](../../specs/model-sidecar/decisions/entries/3S5G-affine-crop-matrix.md) entry had 36 characters left.
- Seven entries use the heading "Notes at acceptance", but no rule stated it. The landers copied the
  form of [ADR-50BW](../../specs/model-sidecar/decisions/entries/50BW-verification-batches.md) and
  [ADR-1VMX](../../specs/model-sidecar/decisions/entries/1VMX-nms-key-exclusion.md).
- The 52NQ bundle got `accepted` in response 5 and `needs-contributor` in response 6. `pack` then
  refused a new version, and the fix needed the follow-up bundle of
  [ADR-KZ9J](../../specs/model-sidecar/decisions/entries/KZ9J-model-id-suffix-rtmo-removed.md).
- Response 2 of the affine-crop-matrix bundle said that the session cannot fix stale notes in the
  landed copy. The reference file of version 2 changed only docstring lines. Later on 2026-11-09,
  the commits "Replace the affine crop fixtures with imports and add its guidance" and "Add the
  custom defaults guidance and its plan sentence" fixed docstrings of landed copies with no new
  version.

## Consequences

- A conditional acceptance adds no response state. The `proposed` entry and the
  `needs-contributor` response agree ([States](../../specs/model-sidecar/model-addition-workflow/hand-over.md#states)).
- The safety review and the copy approval of
  [ADR-AD33](AD33-bundles-are-untrusted-input.md) stay at the landing.

## Alternatives rejected

- **Refuse a new version only after `landed`.** It contradicts ZXD7 item 3. A `needs-contributor`
  response already keeps `pack` open.
- **A class for edits that a recorded user ruling names.** On 2026-11-09, the user chose the
  follow-up bundle over this class.
- **A comparison of the landed copy with the record.** Step 6 compares the copy with the target
  file. No test needs the record comparison.

## Open work

See [open-work.md](../open-work.md).
