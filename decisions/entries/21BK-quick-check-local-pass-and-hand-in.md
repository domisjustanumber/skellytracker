# 21BK — Certification: the quick check, the local pass, failures, the passive record and the hand-in

**Status:** accepted, 2026-11-19 (user).

## Decision

[ADR-P0JZ](P0JZ-certify-contract-in-each-package.md) holds the contract, the validity and the two
layers. Built today: `verify()` at L3 and the image run `_wide_run` of `core/eps/certification.py`,
each in a child process, on `yolox-rtmw-wholebody`. A child that hangs after its result keeps the
result, with `hung-at-exit`. The other parts are not built.

1. **Quick check of an EP.** The app asks the user first. Then a child process runs the L3 probe
   and one test image through the pipeline that the user selected, on the EP and on the CPU EP. It
   compares the two results with the thresholds of the `certification` block of `ep_catalog.yaml`.
   It downloads no model. A recording waits for a check that runs. The app shows a cancel button
   and a note that the EP is not usable until a check completes. This changes item 15 of
   [ADR-MF2R](MF2R-ep-store-install-and-certification.md) ("**`certify(key)`.** It always runs the
   probe: `verify()` at level L3. ..."): the image run uses the pipeline of the user, not
   `yolox-rtmw-wholebody`, it runs in a child process, and each quick check runs it.
2. **Local pass.** A passed quick check makes the EP usable on that PC at once. The app shows it as
   passed on this PC and not yet reviewed. For a `field-test` EP, the local pass is the opt-in. This
   changes the second sentence of item 2 of [ADR-Z5X7](Z5X7-field-test-state-and-directml.md)
   ("Only `skellytracker-eps install KEY --field-test` and the certify suite write it."): a local
   quick pass also writes the opt-in. `recommend()` still never gives a field-test EP
   ([ADR-Z5X7](Z5X7-field-test-state-and-directml.md) item 4). An EP with no reviewed row is usable
   on a PC only after the whole quick check passes there: the L3 probe and the image run. This also
   applies to an EP that is not `field-test`. This replaces the sentence of item 15 of
   [ADR-MF2R](MF2R-ep-store-install-and-certification.md) "A probe pass makes the EP usable on that
   host before a review." After the answer "later" on the EP prompt, the app asks again the next
   time that the user selects that EP. This replaces "later (ask again at the next start)" of item 14
   of [ADR-MF2R](MF2R-ep-store-install-and-certification.md) for this prompt.
3. **Failures.** A hard failure is a non-finite output, a crash, a hang or two unclean exits in a
   row. It marks the EP as failed on that PC, and `recommend()` skips it. A disagreement rate above
   a limit only gives a warning after the recording, and offers a re-run on the CPU EP. The app
   never changes the EP during a recording. An exit is unclean only when an EP session was open and
   the app sent no exit notice (`note_exit_requested()`, working name). An exit that the app
   requested and then killed is a different fact.
4. **Passive record.** This is evidence from normal use. It is opt-in one time: the app asks after
   a quick pass, and it stays off until the user says yes. After a recording, at idle, up to 30
   sampled frames of the saved videos run in `image` mode on the EP and on the CPU EP, and the
   results are compared. It stops when a recording starts. The record holds counts and histograms
   only: no frame, path, name, frame number or time finer than a day. A passive record with a quick
   pass on the same version set can give a reviewed row when it has at least 200 compared frames,
   5 recordings and 3 days, and no hard failure. These values are not calibrated. Such a row has a
   marker that tells it apart from a row of a full run (today both are `source: field`). The name
   of the marker is not decided. Such a row never replaces the `maintainer` row of
   [ADR-MF2R](MF2R-ep-store-install-and-certification.md) item 18. Calibrate the disagreement limit
   of item 3 on the pairs with a `maintainer` row before a warning ships.
5. **Hand-in.** One file and one issue hold all pending reports of the backend host. The backend
   gives the file back unchanged. The interface saves it and opens the issue form. Nothing is sent
   automatically, until a relay exists (the later stage of
   [ADR-MF2R](MF2R-ep-store-install-and-certification.md)). The app does not ask at close or at
   start. It offers a hand-in in a failure message, after a full run, and at the first idle time
   after a recording when a passive record gets to its minimum. A quick pass alone gives no hand-in
   prompt. A failure report is always offered, also for an EP with a reviewed row. "Open issue form"
   counts as handed in. This package keeps the hand-in list in the EP store (`pending_reports()`,
   `mark_reports()`, working names). This changes the last sentence of
   [ADR-MF2R](MF2R-ep-store-install-and-certification.md) item 17 ("Nothing leaves the host."): the
   user can hand in the file, and no code sends it.

## Reason

- The maintainer has one host. Normal use on the PCs of users gives evidence with no extra wait.
- A recording must not stop or change its EP.

## Consequences

- `skellytracker/AGENTS.md` names the two writers of the field-test opt-in of today. Change that
  sentence when the local pass is built.

## Alternatives rejected

- **Ask at application close.** The app kills its backend at close, and the interface can be on an
  other machine.

## Open work

See [open-work.md](../open-work.md).
