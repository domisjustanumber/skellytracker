# X7WD — Rulings of 2026-11-20 on the two certify levels: what each level checks, the limit, the test frames, one path

**Status:** accepted, 2026-11-20 (user).

## Decision

1. **The purpose of each level.** The level `quick` checks that unknown things are safe to use. It
   never checks a thing that is known-good. The level `full` measures this system. It can also check
   known-good things. A quick run that checks nothing is a correct run.
2. **Reviewed.** An EP on a GPU is reviewed only when a row of `ep_evidence.yaml` records a pass for
   the EP, the GPU model, the OS and the version set of this release. This changes item 1 of
   [ADR-ER5X](ER5X-check-rule-unclean-exits-and-coreml.md), where a row counted for each version set.
3. **Quick skips each reviewed pair,** also when the caller names the EP or the GPU. The pair has no
   check. It has a summary item with the result `skipped` and the reason `reviewed`. This changes
   item 1 of [ADR-R53H](R53H-quick-check-default-eps-and-each-gpu.md), where only the default
   selection left out a reviewed pair.
4. **One check for each test.** Each test has its own check. The check `<label>` of an EP on a GPU is
   a roll-up check: it runs no test, and it passes only when `<label>:probe`, `<label>:video` and
   `<label>:live` pass.
5. **The limit of quick.** A quick run of this package has a hard limit of 75 seconds. A check that
   does not fit is `not-run` with `over-budget`. Such a check stores no result, so it never blocks an
   EP. A run that names one EP has the whole limit for that EP. The value is not calibrated.
6. **No download in `certify()`.** The test frames are a file of the package. With no such file, a
   session check is `not-run` with `test-media-missing`. The model files and the EP packs come with
   the installer of the app.
7. **The test frames in git.** `skellytracker/core/model_zoo/test_media/quick_frames.zip` holds 30
   JPEG frames of the public freemocap sample recording: camera 3, frames 499 to 528. `GOLDEN_PATHS`
   of `tools/check_camera_media.py` is `("skellytracker/core/model_zoo/test_media/",)`. This changes
   item 3 of [ADR-9VN4](9VN4-no-camera-recordings-or-frames-in-git.md). Each other rule of that
   entry stays.
8. **The plan.** `certify_plan()` gives `total`, the count of the checks that the run will do, and
   `risks`. Its `details.os_known` tells if the evidence file has a reviewed pass for the OS of this
   system. The key of an OS is its name and its release, for example `Windows 11`, `Ubuntu 24.04`
   and `macOS 15`. An update of the OS is not a new OS.
9. **Two call sites, one path.** An app calls `certify_plan("quick")` and `certify("quick")` at its
   start on an unknown OS. It calls the same two functions with one EP and one GPU when the user
   selects an unknown EP. `eps.certify()`, its report format, the image run and the certify offer
   go. This replaces the certify offer and `certify(key)` of items 14 and 15 of
   [ADR-MF2R](MF2R-ep-store-install-and-certification.md).
10. **The order of the level `full`.** The CPU reference, then each pair with no reviewed pass on
    the GPU that the package recommends, then the CPU timings, then the rest: the pairs with no
    reviewed pass on other GPUs, then the reviewed pairs.
11. **MediaPipe.** Quick runs one smoke run of 30 frames of the pipeline `mediapipe-holistic-tasks`,
    as its own check, only when no row records a pass for the MediaPipe version, the Python minor
    version and the OS of item 8. Such a row is in a list `mediapipe` of `ep_evidence.yaml`.
12. **The report format.** The reports follow the format `skellycertify.report/1.4.0`: the `module`
    label of a check, the `benchmark` items of the summary, and `source` and `sha256` in each
    download of a plan. `certify()` and `certify_plan()` accept `test_media_dir`.
13. **The certify suite of a clone.** `tools/certify_platform.py` and `CERTIFY.md` stay until a
    freemocap build has run certify on Linux and on macOS.

## Reason

- The user decided each item in this session. The user's words on item 1: "Quick is to check
  unknown things are safe to use. Full is for benchmarking 1) unknown things and 2) this system in
  particular".
- Item 2 follows the rule that the user gave for MediaPipe: a new version is an unknown thing.
- Item 7: the media of the quick tests must be in the installed bundle. The footage is already
  public.
- Items 4, 5 and 8 are also rules of the format of `skellycertify` (skellycertify ADR-V1TR, ADR-M8J1).

## Consequences

- After a release with a new version set, each GPU model is unknown until a row for that set exists.
  A user then gets one quick run for an EP.
- The frames file is in the public git history and in each wheel: 6,215,661 bytes.
- One script of an old measurement in `decisions/scripts/` imports the image run. It does not run
  after item 9. It is a record.

## Open work

- Not measured: the first engine build of TensorRT RTX against the limit of item 5, and the start
  time of the MediaPipe pipeline.
- No row of the list `mediapipe` exists.
- The [certification build list](../open-work.md#certification-build-list) holds the runs.
