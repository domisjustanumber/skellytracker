# P0JZ — Certification: one contract in each package, reports to `skellycertify`, two layers

**Status:** accepted, 2026-11-19 (user).

## Decision

[ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) holds the quick check, the failures and the
hand-in. Built today: sections 1 to 5 of the certify suite, `ep_evidence.yaml`,
`PackStatus.certified`, and the quick level of `skellytracker.certify()` and
`skellytracker.certify_plan()` with the reason codes in `skellytracker/REASON_CODES.md`. The other
parts are not built.

1. **Contract.** Each skelly package owns its checks behind two functions:
   `certify(level, progress=None, cancel=None) -> dict` and `certify_plan(level) -> dict`. `level` is
   `quick` (seconds, the default) or `full` (minutes, opt-in). A document in the public repository
   https://github.com/domisjustanumber/skellycertify holds the contract and the report format. There
   is no shared code package. That repository only receives reports as GitHub issues and holds the
   accepted reports. It replaces the issue form and the label of the fork of this repository.
2. **App and suite.** The freemocap app calls `certify()` of each module and merges the module
   reports into one file. `tools/certify_platform.py` stays the way to certify skellytracker with no
   app. It becomes the `full` level and keeps sections 1 to 5. Sections 6 (cameras) and 7 (JPEG
   encode and decode speed, Quick Sync) leave it: they are of skellycam. This replaces:
   - sections 6 and 7 of item 2 of [ADR-Y14H](Y14H-certify-suite.md) ("**Sections.** (1) Checkout
     and versions. ...");
   - [ADR-Y14H](Y14H-certify-suite.md) item 10 ("**skellycam.** skellycam stays out of the normal
     install. ...");
   - [ADR-Y14H](Y14H-certify-suite.md) item 14 ("**Hand-in.** The volunteer attaches the report to
     a GitHub issue of this repository ..."). A report goes to `skellycertify`
     ([ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) item 5), and that repository holds the
     accepted reports. A person still writes the EP rows (item 3).
3. **Evidence rows.** A reviewed evidence row stays in the package that owns the result:
   `ep_evidence.yaml` here ([ADR-MF2R](MF2R-ep-store-install-and-certification.md) item 12). The app
   reads rows only from the packages that it ships with.
4. **Validity.** Each build can give evidence when the report records the version and the commit of
   each package. A modified source tree, a commit that is not in the public repository, a cancelled
   run and a partial run give a record only. This replaces [ADR-Y14H](Y14H-certify-suite.md)
   item 13 ("**Evidence.** A report is evidence only from a clean checkout of a certification
   tag ..."). Thus a run needs no
   certification tag. The user owns the version scheme: SemVer, and a pin names a version, not a
   commit. This package must give its version and its commit with no git at run time.
5. **Certified, and two layers.** In the app, "certified" means that the build ships a reviewed row
   for the EP, the OS and the GPU model. The OS layer is skellycam (the camera controls of each OS)
   and freemocap (its own checks). The EP layer is this package. A package with no certify function
   has nothing to certify. Thus skellycam causes no start box until it ships its checks.
   - **Start check.** The app shows the certify box at its start only when an item of the OS layer
     has no reviewed row. While this check is necessary, the interface of the app is not usable and
     the box stays open. The box shows the plan, and one click starts the quick level. The full run
     is opt-in. A cancel goes back to the box. Each finished quick check, pass or fail, releases the
     app. A failure shows as a failure. A local quick pass stops the start box until the version of
     freemocap, skellycam or skellytracker changes. The app records these versions. The start box
     has no "later" and no "do not ask again".
   - **freemocap part.** A new minor version of freemocap makes an OS row of freemocap invalid. The
     OS build family is a part of the key of that row. freemocap owns the details.
   - **EP prompt.** When only GPU EPs have no row, there is no box at start. The certify step comes
     when the user selects such an EP. Only this prompt has "later" and "do not ask again".
   - This replaces the time of the prompt of
     [ADR-MF2R](MF2R-ep-store-install-and-certification.md) item 14 ("**Prompt.** The app prompts
     at its start, one time for each pair of EP pack version and GPU model."). The answers and the
     stored answer of that item stay.
   - This replaces the first sentence of item 8 of
     [ADR-Z5X7](Z5X7-field-test-state-and-directml.md) ("**Certified.** For a field-test EP,
     certified means that sections 3 and 4 pass on the host."). A person still moves an EP to
     `ready` with a reviewed report.
6. **GPU busy.** A certify run does not start while a pipeline holds the GPU (live, recording or
   post-hoc). The reason code is `gpu-busy`.
7. **Cameras.** Camera evidence comes later, as its own record type with the key camera model (USB
   VID:PID), backend and OS.

## Reason

- The maintainer has one host. Volunteers and users give the evidence for other hardware.
- The wait of a user must be as short as possible.
- The checks stay with the code that they test.

## Alternatives rejected

- **One certify package that holds all checks.** The user decided that the checks stay in each
  repository.
- **The suite only inside the skellytracker package.** It cannot certify the OS layer.
- **Evidence only from released versions.** The user decided: each build that records its commits.

## Open work

See [open-work.md](../open-work.md).
