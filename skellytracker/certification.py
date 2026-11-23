"""`certify()` and `certify_plan()`: the certification functions of the whole package (ADR-P0JZ, ADR-21BK).

    import skellytracker
    plan = skellytracker.certify_plan("quick")          # show the plan, then get the consent of the user
    report = skellytracker.certify("quick", progress=show, cancel=event)

An application calls these two functions at its start on an OS with no reviewed pass (`details.os_known` is false).
It calls them again with one EP and one GPU (`execution_providers`, `device`) when the user selects an EP with
no reviewed pass on that GPU. This is the one certify path of an application (ADR-X7WD item 9).

The hand-in list (ADR-21BK item 5) holds each report of `certify()` on this host with a check that ran:

    for row in skellytracker.pending_reports():         # the reports that the user did not hand in
        report = skellytracker.read_report(row["report_id"])
    skellytracker.mark_reports(ids, "covered", reference=issue_url)   # or "opened", or "pending"

This package sends nothing and makes no report file for a person: the application builds the file from
the module reports, shows it, hands it in and then marks the reports. A report with a failed check is
always worth an offer (`has_failure`). A pass alone gives no prompt. A new report of a quick check deletes
each older report of a pass that it repeats, when the user did not hand that report in.

The two functions are `skellytracker.certify` and `skellytracker.certify_plan`. They obey the contract
`report-format.md` of the repository `skellycertify`, format `skellycertify.report/1.9.0`. An application that
runs its own check on the test frames reads them with `certify_frames()` of this module. The reason codes
of this package are in `skellytracker/REASON_CODES.md`. A plain `import skellytracker` imports this
module only: it imports `eps`, `pipelines` and ONNX Runtime in the function bodies.

The result is a plain `dict`, not a frozen record of `eps`, because the contract fixes a JSON object.
"""

import importlib.metadata
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path

SCHEMA = "skellycertify.report/1.9.0"
SUMMARY_NAMES = {"trt-rtx": "TensorRT RTX", "cuda": "CUDA", "directml": "DirectML", "coreml": "Core ML", "amdgpu": "AMD GPU",
                 "migraphx": "MIGraphX", "cpu": "CPU"}  # the short fixed name of each EP in `summary`; a name never changes
RAN = ("pass", "fail", "record-only")
SCHEMA_PREFIX = "skellycertify.report/1."  # a report of an older 1.x version on this host stays in the hand-in list
PACKAGE = "skellytracker"
LEVELS = ("quick", "full")
REPORT_STATES = ("pending", "opened", "covered")  # `opened`: the user saved the file and opened the issue form; `covered`: an issue holds it
REPORT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
# The time estimates below are not calibrated. One Windows host on `directml` (2026-11-20, ADR-R0EB) gave, with the start
# of the child and 3 frames in each mode: 4.2 s for the CPU reference, 1.1 to 1.4 s for a probe, and about 3 s for each of
# `<ep>:video` and `<ep>:live`. A run now has 30 frames in each mode, so the values are larger.
PROBE_SECONDS = 3  # not calibrated: one L3 probe
VIDEO_SECONDS = 6  # not calibrated: `<ep>:video` of an EP with no `certification.seconds` (the catalog gives `trt-rtx` and `cuda`, with the first engine build)
LIVE_SECONDS = 6  # not calibrated: `<ep>:live`: one more child and one more pipeline start on the EP
CPU_REFERENCE_SECONDS = 12  # not calibrated: the CPU reference: `cpu:video` and `cpu:live` in one child
QUICK_BUDGET_SECONDS = 65  # not calibrated: the hard time limit of the level `quick` (ADR-X7WD item 5, the number of ADR-Q9R6 item 1)
CPU_CHECKS = ("cpu:video", "cpu:live")  # the CPU reference of the run, at the two levels
MEDIAPIPE_CHECK = "mediapipe:smoke"  # the MediaPipe smoke run of the level `quick` (ADR-X7WD item 11); it is not an EP
MEDIAPIPE_MODULE = "MediaPipe"  # the `module` of `mediapipe:smoke` and the `name` of its `component` summary item
# not calibrated: one Windows system (MediaPipe 1.2.2, Python 3.13, CPU) measured about 3 s in one process for the import,
# the pipeline start and the 30 frames; the `spawn` child adds its start
MEDIAPIPE_SECONDS = 6
JPEG_SECONDS = 5  # not calibrated: the time estimate of the two JPEG checks; 1.0 to 1.3 s on one RTX 3070
JPEG_TIMEOUT_SECONDS = 120.0
JPEG_EPS = ("cuda", "trt-rtx")  # `GPU_FRAME_EPS` of `core/decode/certification.py`; a test checks that they agree
JPEG_CHECKS = ("jpeg-decode", "jpeg-preprocess")  # the names of `run_jpeg_quick_checks()`, in its order
CAMERA_COUNTS = (1, 3, 6)  # the camera counts of the pipeline timings of the level `full`
# the EPs with a JPEG certification: `GPU_FRAME_EPS` and `AMD_EPS` of `core/decode/certification.py`; a test checks that they agree
JPEG_FULL_EPS = ("cuda", "trt-rtx", "directml", "amdgpu", "migraphx")
PIPELINE_SECONDS = 10  # not calibrated: the estimate of the pipeline timing at one camera count; 4 to 12 s on one RTX 3070 host
JPEG_FULL_SECONDS = 20  # not calibrated: the estimate of the JPEG certification of one EP; 12 to 26 s on one RTX 3070 host
JPEG_FULL_TIMEOUT_SECONDS = 600.0
PROGRESS_INTERVAL = 0.1  # the contract allows at most 10 progress messages each second
RUNNABLE_STATES = ("builtin", "ready", "installed_unverified", "untested-ort", "not_ready", "field_test")
COMPARED_OUTPUTS = ("boxes", "wholebody")  # the outputs that `compare_results()` compares
CHILD_FAILURES = {"timed-out": "timed-out", "crashed": "crashed", "no-result": "crashed"}  # a child with no result
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
                    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
                    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
OS_NAMES = {"Darwin": "macOS"}
ARCHES = {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}
PATH_PATTERN = re.compile(r"(?:\b[A-Za-z]:[\\/]|\\\\[^\\\s]|/(?:home|Users|root)/|~[\\/])[^\s\"'|,;]*")
# the numbers of `compare_results()` that `<ep>:video` keeps: the values of frame 0
COMPARED_NUMBERS = ("people_cpu", "people_ep", "box_iou_min", "points_compared", "keypoint_px_max", "keypoint_box_fraction_max",
                    "keypoint_box_fraction_median", "keypoint_box_fraction_p99")
TIMING = re.compile(r"^(.+):(pipeline-\d+)$")  # the name of a pipeline timing of the level `full`: the label and the stage
FRAME_CHECK = re.compile(r":(?:video|live|pipeline-\d+)$|^mediapipe:smoke$")  # the checks that read the test frames file


def certify_frames(test_media_dir: str | os.PathLike | None = None) -> list[bytes]:
    """The 30 test frames of `certify()`, as the JPEG bytes of each frame in order. It decodes nothing and downloads nothing.

    `test_media_dir` is the test media folder of the format of `skellycertify` (section 2.8): the frames file there is
    `<sha256>.zip`, with the sha256 of the record. With None, or when the folder does not hold that file, the file is the
    file of the package. A file that is absent or has a wrong sha256 or a wrong count raises `FramesUnavailableError` of
    `core/eps/certification.py`.
    """
    from skellytracker.core.eps import certification

    return certification.frame_jpegs({"frames": certification.frames_record(test_media_dir)})


def certify_plan(level: str, *, execution_providers: Sequence[str] | None = None, device: str | Sequence[str] | None = None,
                 pipeline=None, test_media_dir: str | os.PathLike | None = None, setups: Sequence[str] | None = None) -> dict:
    """The plan of a `certify()` call with the same arguments. It loads no GPU library and downloads nothing.

    `downloads` is empty at the two levels: `certify()` downloads nothing. In the format `1.6.0`, each download
    of a plan has `source` and `sha256`. `details.checks` gives the
    name of each EP check, one for each EP and GPU. A pair with a reviewed pass is not in it at the level
    `quick`. No level installs an EP: `details.not_run` gives each of them that will not run, with its
    reason code, for example `ep-not-installed`. `system_changes`, `questions` and `risks` are empty.
    `pipeline` does not change the plan. `total` is the count of the checks that will run: the checks of
    each pair that can run, with its EP check, and the CPU reference (`cpu:video` and `cpu:live`) when a
    pair can run. The pairs give 0 when no pair can run. The level `full` always counts the checks of the CPU EP.
    At the level `quick`, it also counts `mediapipe:smoke` when that check will run: the default selection,
    MediaPipe installed and no reviewed row for it (see `certify()`). The plan does not look for the model file
    of MediaPipe, because that needs an import of `mediapipe`.
    `seconds_estimate` counts the same checks. At the level `quick` it is at most `QUICK_BUDGET_SECONDS` (65 s).
    `details.os_known` is true when `ep_evidence.yaml` has a reviewed pass for the OS key of this system
    (`os_key()` of `core/eps/evidence.py`), for any EP, GPU and version set. The OS key is the name and the
    release of the OS, for example `Windows 11`, `Ubuntu 24.04` or `macOS 15`. An update of the OS is not a new OS
    (ADR-X7WD item 8).
    `test_media_dir` does not change the plan: the test frames are never a download.
    `setups` is the list of the setups that the person accepted (format 1.8.0, section 2.6). This package has no
    setup check: the plan always has an empty `setups` list, and the option changes nothing.
    """
    _check_level(level)
    plan = {"package": PACKAGE, "kind": level, "seconds_estimate": 0, "total": 0, "risks": [], "downloads": [],
            "system_changes": [], "questions": [], "setups": []}
    from skellytracker.core.eps import evidence
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.system.host import probe_host

    catalog, host = load_catalog(), probe_host()
    settings = catalog.data["certification"]
    full = level == "full"
    selected = [item for item in _selection(catalog, host, execution_providers, device, skip_certified=not full)
                if item[4] != "reviewed"]
    if full:
        first, rest = _full_order(selected, host)
        selected = [*first, *rest]
    runnable = [item for item in selected if item[4] is None]
    smoke = _mediapipe_state(level, execution_providers, device, host) == "run"
    seconds = sum(_estimates(runnable, settings, full).values()) + (MEDIAPIPE_SECONDS if smoke else 0)
    plan["seconds_estimate"] = seconds if full else min(seconds, QUICK_BUDGET_SECONDS)
    plan["total"] = (len(_cpu_names(full)) if runnable or full else 0) + smoke + sum(
        len(_names(label, key, device_key, full)) for label, key, device_key, *_ in runnable)
    os_key = evidence.os_key(host.os_label)
    plan["details"] = {"execution_providers": list(dict.fromkeys(key for _, key, *_ in selected)),
                       "checks": [label for label, *_ in selected],
                       "not_run": {label: reason for label, _, _, _, reason in selected if reason},
                       "os_known": os_key is not None and any(
                           isinstance(row, dict) and row.get("result") == "pass" and isinstance(row.get("os_label"), str)
                           and evidence.os_key(row["os_label"]) == os_key for row in evidence.load_evidence())}
    return plan


def certify(level: str, progress: Callable[[dict], object] | None = None, cancel=None, *,
            execution_providers: Sequence[str] | None = None, device: str | Sequence[str] | None = None, pipeline=None,
            test_media_dir: str | os.PathLike | None = None, abandon=None, setups: Sequence[str] | None = None) -> dict:
    """Run the certification checks of this package at `level`, and return the module report.

    - `level`: `quick` or `full`. Each other value raises `ValueError`. The level `quick` checks that
      unknown things are safe to use. It never checks a known-good thing (ADR-X7WD item 1). The level `full`
      measures this system, and it can also check known-good things. It runs the checks of the level `quick`
      and more checks, in minutes (see "Level `full`").
    - `progress`: a callable that gets each progress message, a `dict` with the complete state, at most
      10 times a second. If it raises, it gets no other message, and the run continues.
    - `cancel`: an object with `is_set()`. A set cancel stops the running child process within about a
      second. Each check that did not end is `not-run` with `cancelled`.
    - `abandon`: an object with `is_set()`, as `cancel` (ADR-Q9R6 item 2). Use it when the caller of the run is gone,
      for example after a crash of the application. A set abandon stops the running child as a set cancel does, and
      the clean-up runs. Each check that did not end, and each check that a stop ended, is `not-run` with `abandoned`.
      From the time it is set, the run stores no local result. It writes no report file and deletes no older report.
      The returned report has an `id` with no file behind it, `evidence.valid` false and the reason `abandoned`
      (not `cancelled`, also when `cancel` is set).
    - `execution_providers`: the EP keys to check. The default is each GPU EP of this host: each usable
      plugin EP, and also `directml` and each EP of the Windows ML catalog (the `field-test` EPs with no
      pack), and `coreml` on a Mac. An unknown or reserved key raises `EpRequestError` (a `ValueError`).
    - `device`: one device key or a list of device keys, as in `run_devices()`: the GPUs to check on. The
      default is each GPU that the EP can use. A key that is not a GPU of this host raises
      `EpRequestError`. A named EP that cannot use a named GPU is `not-run` with `gpu-not-usable`.
    - A reviewed pair: an EP on a GPU with a reviewed pass, a row of `ep_evidence.yaml` for the EP, the GPU
      model, the OS and the version set of this release (`evidence.certified()`). The level `quick` never
      checks it, also when the caller names the EP or the GPU (ADR-X7WD items 2 and 3). It has no check.
      `details.skipped` gives it as `{<ep>: "reviewed"}`, and it has a summary item `skipped`. The level
      `full` checks it.
    - `pipeline`: the pipeline of the user, as a `PipelineConfig`, a key of the pipeline catalog or a
      path. The default is `certification.pipeline` of the EP catalog. A config that does not load
      raises, as `load_pipeline()` does.
    - `test_media_dir`: the test media folder of the format (section 2.8), or None. The frames file there is
      `<sha256>.zip`, with the sha256 of `frames_record()`. With None, or when the folder does not hold that file, the
      run uses the file of the package (format 1.6.0, section 2.8). A file in the folder with a wrong sha256 is never
      used: the session checks are then `not-run` with `test-media-missing`. The path is never in the report.
    - `setups`: the `id` of each setup that the person accepted, or None (format 1.8.0, section 2.6). This package
      has no setup check, so the option changes no check and no report.

    The quick check shows that a post-hoc session (the running mode `video`) and a realtime session (the
    running mode `live`) start and run. Each check below runs in its own `spawn` child. The frames are the
    30 test frames of the package (`frames_record()`, `FRAMES` of
    `core/eps/certification.py`), on one camera, in order.
    - First the CPU reference, one time for the run: the pipeline on the CPU EP on the frames in `video`,
      then in `live`. `cpu:video` passes when each frame has a person. `cpu:live` passes when its outputs
      are finite. It runs only when an EP check can run.
    - Then, for each EP on each GPU of the selection: the L3 probe (`verify()`), `<ep>:probe`.
    - `<ep>:video`: the pipeline on the EP on the frames in `video`. It compares frame 0 with frame 0 of
      the CPU reference with each threshold of `certification` of the EP catalog. Each later frame fails
      only on other people than the CPU EP (`people-differ`), an output that is not finite (`not-finite`) or
      a box IoU under `box_iou_min` (`box-differs`): its keypoint difference is a record only (ADR-R0EB
      item 3). The first frame that fails gives the reason. With no CPU reference, it is `not-run` with
      `cpu-reference-missing`. Its `numbers` hold the numbers of frame 0, `later_keypoint_box_fraction_max`
      (the worst keypoint difference of the later frames), `frames`, and `ep_ms`, `cpu_ms` and
      `speed_against_cpu` (`faster`, `slower` or `similar`): a rough figure, a record only that never
      changes the result.
    - `<ep>:live`: the pipeline on the EP on the frames in `live`, with a rising `timestamp_ms`. It
      passes when each frame has finite outputs and a person. It fails with the error of the run, with
      `not-finite` on an output that is not finite, and with `no-person` on a frame with no person. It
      compares nothing. It starts only after
      `<ep>:video` passed, else it is `not-run` with `video-not-passed`.
    It downloads nothing (ADR-X7WD item 6): the installer of the application brings the model files and the EP
    packs. With a model file that is not on this host, each of these checks
    is `not-run` with `models-missing`. With a test frames file that is absent or has a wrong sha256,
    `cpu:video`, `cpu:live` and each `<ep>:video` and `<ep>:live` are `not-run` with `test-media-missing`.
    Each EP on each GPU gives the checks `<ep>:probe`, `<ep>:video`, `<ep>:live`
    and `<ep>`. `<ep>` is `<key>@<device>`, for example `cuda@10de-2484-0`: the EP key and the device key of
    the GPU with no `gpu:` and with `-` for `:`. It is `<key>` alone for an EP with no GPU to run on, and
    for `coreml`: it runs on the chip of the Mac and selects no GPU. The key of its stored result is the chip
    name, and `details.eps.coreml.gpu` gives it, for example `chip:apple-m2-pro` (ADR-ER5X item 6).
    Thus the name of an EP check has no `:`. `details.eps.<ep>.device` gives the device key. The
    check `<ep>` is a roll-up check: it runs no test. It passes only when `<ep>:probe`, `<ep>:video` and
    `<ep>:live` pass. Else it has the result and the reason of the first of them that failed, or else of
    the first that did not run (ADR-X7WD item 4). On `cuda` and `trt-rtx`, an EP on
    a GPU also gives `<ep>:jpeg-decode` and `<ep>:jpeg-preprocess`: the two checks of
    `run_jpeg_quick_checks()` of the GPU frame path, in one more `spawn` child, after a check `<ep>:video` that
    passed. They never change `<ep>`: a JPEG check that fails stops only the GPU frame path
    (ADR-R53H item 5). An EP that cannot run, for
    example a pack that is not installed, gives `not-run` with `ep-<state code>`. Each EP runs, also
    when an other EP fails.

    The MediaPipe smoke run (ADR-X7WD item 11): the check `mediapipe:smoke`, with the `module` `MediaPipe`.
    - Only the level `quick` has it, and only with the default selection: the caller names no EP and no
      device. It is the last check of the run, after each EP check.
    - It runs only when no row of the list `mediapipe` of `ep_evidence.yaml` records a pass for the installed
      MediaPipe version, the Python version (`<major>.<minor>`, for example `3.13`) and the OS key of this
      system (`os_key()`, for example `Windows 11`). With such a row, the run has no check `mediapipe:smoke`,
      and `details.skipped` gives `{"mediapipe:smoke": "reviewed"}`.
    - It runs the pipeline `mediapipe-holistic-tasks@skellytracker` on the 30 test frames in the running
      mode `live`, with a rising `timestamp_ms`, in its own `spawn` child. It passes when each frame has a
      present row, and each point that MediaPipe found in that row has finite values. A missing point has
      NaN values: that is normal. It fails with `not-finite` on a value that is not finite, with `no-person`
      on a frame with no present row, and with the error of the run as `<ep>:live` does.
    - It is `not-run` with `models-missing` when MediaPipe is not installed, or when the model file of
      MediaPipe is not in its cache: it downloads nothing. It is `not-run` with `test-media-missing` when
      the test frames file is not valid.
    - It is not an EP check. It stores no local result, opts in nothing and never changes an EP check.
    - It has one summary item of the group `component`: `{"group": "component", "name": "MediaPipe", "device": None,
      "result": ...}`, with the result of the check when it is `pass` or `fail`. A check that is `not-run` has no item,
      as an EP that is `not-run`. With a reviewed row, the item has the result `skipped` and the reason `reviewed`.
      When MediaPipe is not installed, the check stays `not-run` with `models-missing`, and the item has the result
      `skipped` and the reason `not-installed` (format 1.6.0). A missing model file alone gives no item.

    The time budget of the level `quick` (ADR-X7WD item 5): `QUICK_BUDGET_SECONDS` (65, not calibrated) from the
    start of the call. The order is the CPU reference, then the pairs in the order of the selection, then `mediapipe:smoke`.
    Before each check that starts a child (the CPU reference, a probe, `<ep>:video`, `<ep>:live`, the two JPEG
    checks, `mediapipe:smoke`), a
    check whose time estimate is more than the time that is left does not start: it is `not-run` with
    `over-budget`. The time limit of each child is the smaller of its own limit and the time that is left,
    and a child that the end of the budget stops is also `not-run` with `over-budget`. A run that names
    one EP (`execution_providers` with one key) does not skip a check on its estimate: it stops only at the
    end of the budget. An EP check that is `not-run` stores no local result, so the budget never blocks an EP.
    The level `full` has no budget.

    Level `full` (ADR-75J6). The report has the layout of the level `quick`: a flat list of checks, the same
    `details.eps` and the same `details.versions`. It runs only checks that need no checkout: it installs
    nothing and builds no environment. `tools/certify_platform.py` keeps the checks that need a checkout.
    - The order (ADR-X7WD item 10): first the CPU reference (`cpu:video` and `cpu:live`). Then each pair with no
      reviewed pass on the GPU that the package recommends: the GPU with the most VRAM, on a tie the lowest PCI bus id
      (`_by_vram()` of `core/eps/recommendation.py`). Then the CPU timings: `cpu:pipeline-1`, `cpu:pipeline-3`
      and `cpu:pipeline-6`, then `cpu:jpeg`. Then the pairs with no reviewed pass on the other GPUs, then the
      reviewed pairs. The checks of the report have this order. The CPU EP has no EP check.
    - The checks of each EP on each GPU: `<ep>:probe`, `<ep>:video` and `<ep>:live` as in the level `quick`, then
      `<ep>:pipeline-1`, `<ep>:pipeline-3` and `<ep>:pipeline-6`, then `<ep>:jpeg`, then `<ep>`. It does
      not write `<ep>:jpeg-decode` and `<ep>:jpeg-preprocess`.
    - `<ep>:pipeline-<n>` is the timing of the pipeline on `<n>` cameras in the running mode `video`, in a
      `spawn` child (`time_run()` of `core/eps/certification.py`). It is `record-only`, and its `numbers`
      hold the times and the VRAM of the child, and `against_cpu` and `speed_against_cpu` from the medians, which the
      run adds after the CPU timings.
      A run that raises, for example with no VRAM left, is `not-run` with the exception class. It starts
      only after a check `<ep>:video` that passed, else it is `not-run` with `video-not-passed`.
    - `<ep>:jpeg` is the outcome of `run_jpeg_certification()` of `core/decode/certification.py` on the EP,
      in one `spawn` child, for each EP of `JPEG_FULL_EPS` on a GPU: `fail` when a check failed, else `pass`
      when a check passed. Each check of that run follows it as `<ep>:jpeg:<name>`, with its result, its
      reason code and its numbers. It starts only after a probe that passed.
    - A timing and a JPEG check never change `<ep>`. `<ep>` is the roll-up check of the level `quick`.
      The run stores the same local result as a quick check. For `cuda` and `trt-rtx`, the stored `jpeg`
      holds the results of the two checks of `QUICK_CHECKS` from the JPEG certification.
    - With no EP to check, the level `full` still runs the checks of the CPU EP.
    - The timings use frame 0 of the test frames.

    The report: `id` is a version 4 UUID. It is also the name of the report file and the id of the hand-in
    list. The package writes it after the scrub of private words. `details.eps.<ep>.pack_version` holds the
    version of the pack of the EP in the catalog, the package version of its Windows ML record, or `builtin`.
    For an EP with a pack, `details.eps.<ep>` also holds two facts of the installed pack, from its manifest in the
    EP store: `installed_pack_version`, and `wheels_match_lock`, true when the sha256 values of the wheels that
    the install recorded are those of the lock of the catalog. A report of
    the schema `1.0.0` on this host, with a time in its file name and no `id`, stays in the hand-in list
    with its old id. The package never deletes a report of the level `full`. `test_media` lists the test frames file
    when a check that reads it ran (`FRAME_CHECK`): `{"name": "quick_frames.zip", "sha256", "bytes", "source"}`, with the
    `source` `shared` for the file of `test_media_dir` and `bundled` for the file of the package. It is an empty list
    when no such check ran or when the file is not valid. A run with no check has no `test_media`.

    Each check has `module`: the name of `SUMMARY_NAMES` of its EP, for example `CUDA`, and `CPU` for each check
    `cpu:*`. A JPEG check and an `exit` check have the module of their EP. The `name` of the summary item of the EP
    is the same text. `mediapipe:smoke` and its `exit` check have the module `MediaPipe`.

    `summary` is the list of the summary items of the report for a person, from the format `1.6.0`. An item has
    `group`, `name`, `device` and `result`. Each EP that ran on a GPU has one item of the group `ep`, with the
    result of its check: an EP that is `not-run` has no item. `name` is the short fixed name of the EP, for
    example `TensorRT RTX`, `CUDA`, `DirectML` or `CPU`. `device` is the `id` of the GPU in `host.gpus`, or None.
    A `gpu-jpeg` item follows the `ep` item when a check of the GPU JPEG decode ran on that EP and that GPU.
    Each reviewed pair that the level `quick` skipped has an `ep` item with the result `skipped` and the reason
    `reviewed`, after the items of the pairs that ran. The CPU EP has the next item when one of its checks ran:
    `fail` when one failed, else `record-only`. The `component` item of `mediapipe:smoke` follows it. The level `full` then adds one item of the group `benchmark` for each
    timing `<ep>:pipeline-<n>` with a median, in the order of the checks: `name` and `device` as for the `ep` item,
    `stage` (`pipeline-<n>`), `ms_per_frame` (the median time of one call, which holds one frame of each of the `<n>`
    cameras) and `fps` (the calls in each second, from the median). A `benchmark` item has no `result`.

    Evidence: the item of the quick level is one EP on one GPU of this host. Thus a run of a part of the EPs is
    complete for each EP that it checks, and is not `partial-run`. A run with no EP to check and no
    `mediapipe:smoke` has no check and is not valid as evidence (`no-check`), also when each pair is
    reviewed: that is a correct quick run. A `quick` report never gives a reviewed row of `rows`. A person
    can write a row of the list `mediapipe` after a review of a report with a `mediapipe:smoke` that passed.

    The package cannot see the pipelines of an application, so it never refuses a run with `gpu-busy`:
    the application must not call it while a pipeline holds the GPU.

    It writes in the EP store of the user: the report in the folder `reports`, the verdict of the
    probe and, in `quick-checks.json`, the result of each check `<ep>` that is `pass` or `fail` as the local result of
    the EP. A `field-test`
    EP gets the opt-in during its check. The opt-in stays only when the check passes on a GPU (ADR-21BK item 2). The stored result is for the GPU model: two GPUs of one
    model share it, and the last check wins. The row of `quick-checks.json` of `cuda` and `trt-rtx` also holds
    `jpeg`: the result of each of the two JPEG checks.
    """
    _check_level(level)
    started = time.monotonic()
    created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    from skellytracker.core.eps import evidence
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.system.host import probe_host

    catalog, host = load_catalog(), probe_host()
    report, reasons = _base_report(level, created, host)
    sender = _Progress(progress, level)
    full = level == "full"
    if not full:
        sender.deadline = started + QUICK_BUDGET_SECONDS
        sender.whole = execution_providers is not None and len(set(execution_providers)) == 1
    selected = _selection(catalog, host, execution_providers, device, skip_certified=not full)
    skipped = [item for item in selected if item[4] == "reviewed"]  # the level `quick` never checks a reviewed pair
    selected = [item for item in selected if item[4] != "reviewed"]
    cpu = full or any(reason is None for *_, reason in selected)  # the CPU reference runs only for an EP that can run
    first, rest = _full_order(selected, host) if full else (selected, [])
    selected = [*first, *rest]

    def pair_names(items):
        return [name for label, key, device_key, *_ in items for name in _names(label, key, device_key, full)]

    smoke = _mediapipe_state(level, execution_providers, device, host)
    names = [*(CPU_CHECKS if cpu else ()), *pair_names(first), *(_cpu_names()[len(CPU_CHECKS):] if full else ()), *pair_names(rest),
             *((MEDIAPIPE_CHECK,) if smoke in ("run", "models-missing") else ())]  # the last check of the run
    report["checks"] = [{"name": name, "result": None, "reason": None} for name in names]
    if smoke == "models-missing":
        report["checks"][-1].update(result="not-run", reason="models-missing")
    sender.estimates = {**_estimates(selected, catalog.data["certification"], full), **({MEDIAPIPE_CHECK: MEDIAPIPE_SECONDS} if smoke == "run" else {})}
    resolved = _pipeline(catalog, pipeline) if names else None  # a config that does not load raises before the start
    stop = cancel if abandon is None else _Stop(cancel, abandon)  # the checks and the children read one object
    sender.send("starting", None, report["checks"], None)
    if names:
        _quick(report, selected, catalog, host, sender, stop, resolved, full, len(first), test_media_dir, abandon)
    else:
        reasons.append("no-check")
    abandoned = abandon is not None and abandon.is_set()
    if stop is not None and stop.is_set():
        code = "abandoned" if abandoned else "cancelled"
        for row in report["checks"]:
            if row["result"] is None or (abandoned and row["reason"] == "cancelled"):
                row.update(result="not-run", reason=code)
        reasons.append(code)
    sender.send("cleaning-up", None, report["checks"], None)
    for row in report["checks"]:  # after the run: the JPEG checks of the level `full` and the `exit` checks join during it
        row["module"] = _module(row["name"])
    report["details"]["skipped"] = {label: "reviewed" for label, *_ in skipped} | ({MEDIAPIPE_CHECK: "reviewed"} if smoke == "reviewed" else {})
    report["evidence"] = {"valid": not reasons, "reasons": reasons}
    report["summary"] = _summary(report, [{"group": "ep", "name": _module(key), "device": evidence.gpu_id(gpu),
                                           "result": "skipped", "reason": "reviewed"} for _, key, _, gpu, _ in skipped],
                                 mediapipe_installed=smoke != "models-missing")
    report = _scrub(report)
    report = {"schema": SCHEMA, "id": str(uuid.uuid4()), **report}  # after the scrub: a private word must not change the id
    if report["checks"] and not abandoned:
        from skellytracker.core.eps import certification

        path = certification.reports_dir() / f"{report['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        _prune_reports()
    sender.send("done", None, report["checks"], None)
    return report


def pending_reports(include_handed_in: bool = False) -> list[dict]:
    """The reports of `certify()` on this host that the user did not hand in, the oldest first.

    Each row is `{"report_id", "kind", "created_utc", "has_failure", "evidence_valid", "state", "reference"}`.
    `state` is `pending`, `opened` or `covered`, and `reference` is the text of `mark_reports()`, for example
    the address of the issue, or None. With `include_handed_in`, the list holds each report in each state.
    A report is in the list when a check of it ended `pass` or `fail`. It reads the EP store only.
    """
    from skellytracker.core.eps import certification, store

    marks = store.read_json(_marks_path(store)) or {}
    rows = []
    for path in sorted(certification.reports_dir().glob("*.json")):
        report = store.read_json(path)
        if not isinstance(report, dict) or not str(report.get("schema")).startswith(SCHEMA_PREFIX) or not REPORT_ID.match(path.stem):
            continue
        results = {check.get("result") for check in report.get("checks", ()) if isinstance(check, dict)}
        if not results & {"pass", "fail"}:
            continue
        mark = marks.get(path.stem) if isinstance(marks.get(path.stem), dict) else {}
        state = mark.get("state") if mark.get("state") in REPORT_STATES else "pending"
        if state == "pending" or include_handed_in:
            rows.append({"report_id": path.stem, "kind": report.get("kind"), "created_utc": report.get("created_utc"),
                         "has_failure": "fail" in results, "evidence_valid": bool((report.get("evidence") or {}).get("valid")),
                         "state": state, "reference": mark.get("reference") if state != "pending" else None})
    return sorted(rows, key=lambda row: (row["created_utc"] or "", row["report_id"]))


def read_report(report_id: str) -> dict:
    """The module report of a row of `pending_reports()`, unchanged. An id that is not in the list raises `ValueError`."""
    from skellytracker.core.eps import certification, store

    report = store.read_json(certification.reports_dir() / f"{report_id}.json") if REPORT_ID.match(str(report_id)) else None
    if not isinstance(report, dict) or not str(report.get("schema")).startswith(SCHEMA_PREFIX):
        raise ValueError(f"{report_id!r} is not a report of this host")
    return report


def mark_reports(report_ids: Sequence[str], state: str, *, reference: str | None = None) -> None:
    """Set the hand-in state of reports: `covered` (an issue holds them), `opened` (the user saved the file and
    opened the issue form) or `pending` (not sent: back in the list).

    `reference` is one text that this package stores and gives back unchanged, for example the address of the
    issue. It applies to each report of the call. `pending` removes a stored reference. An unknown state,
    an id that is not a report of this host, or a `reference` with `pending` raises `ValueError`, and the
    call then changes nothing.
    """
    from skellytracker.core.eps import store

    if isinstance(report_ids, str):
        raise ValueError("report_ids is a list of report ids")
    if state not in REPORT_STATES:
        raise ValueError(f"the state must be one of {', '.join(REPORT_STATES)}, not {state!r}")
    if state == "pending" and reference is not None:
        raise ValueError("a pending report has no reference")
    ids = list(dict.fromkeys(report_ids))
    for report_id in ids:
        read_report(report_id)
    with store.store_lock():
        marks = store.read_json(_marks_path(store)) or {}
        for report_id in ids:
            if state == "pending":
                marks.pop(report_id, None)
            else:
                marks[report_id] = {"state": state, "reference": reference}
        store.write_json(_marks_path(store), marks)


def _prune_reports() -> None:
    """Delete each older report of a pass that a newer report repeats (ADR-ER5X item 7).

    A report stays when it has a failed check, when the user handed it in (`opened` or `covered`), and when
    it is the newest pass of an EP on a GPU or of `mediapipe:smoke`. A report with no check that passed is not a report of a pass:
    it stays. A file that this function cannot delete stays.
    """
    from skellytracker.core.eps import certification, store

    with store.store_lock():
        marks = store.read_json(_marks_path(store)) or {}
        found = []
        for path in certification.reports_dir().glob("*.json"):
            report = store.read_json(path)
            if not isinstance(report, dict) or not str(report.get("schema")).startswith(SCHEMA_PREFIX) or path.stem in marks:
                continue
            if report.get("kind") != "quick":  # a report of the level `full` always stays
                continue
            checks = [check for check in report.get("checks", ()) if isinstance(check, dict)]
            passed = {check.get("name") for check in checks if check.get("result") == "pass"
                      and (":" not in str(check.get("name")) or check.get("name") == MEDIAPIPE_CHECK)}
            if passed and not any(check.get("result") == "fail" for check in checks):
                found.append((str(report.get("created_utc") or ""), path.stem, path, passed))
        newer: set = set()
        for _, _, path, passed in sorted(found, key=lambda item: item[:2], reverse=True):
            if passed <= newer:
                try:
                    path.unlink()
                except OSError:
                    pass
            newer |= passed


def note_exit_requested() -> None:
    """The exit notice of an application (ADR-ER5X item 5): the user asked it to close, and it can now end this
    process in any way. Call it in the process that runs the pipelines, before the process ends.

    Without the notice, an end of a process that held a session on a GPU EP, with no clean exit of the
    interpreter, counts as one unclean exit of that EP on that GPU. Two in a row mark the EP as failed on
    this PC, until a quick check passes.
    """
    from skellytracker.core.eps import exits

    exits.note_exit_requested()


def _marks_path(store) -> Path:
    return store.store_root() / "hand-in.json"


class _Stop:
    """Set when the cancel or the abandon of `certify()` is set: the one stop object of the checks and the children."""

    def __init__(self, cancel, abandon):
        self.events = [event for event in (cancel, abandon) if event is not None]

    def is_set(self) -> bool:
        return any(event.is_set() for event in self.events)


def _check_level(level) -> None:
    if level not in LEVELS:
        raise ValueError(f"the level must be 'quick' or 'full', not {level!r}")


class _Progress:
    """The sender of the progress messages: each message is the complete state, at most 10 each second.

    It also holds the time budget of the run, because each check gets it: `deadline` is the end of the budget of the
    level `quick` (`time.monotonic()`), or None. With `whole`, a check does not skip on its estimate, only at the end.
    """

    def __init__(self, callback, kind: str):
        self.callback, self.kind, self.last, self.estimates = callback, kind, 0.0, {}
        self.deadline, self.whole = None, False

    def send(self, state: str, step: str | None, checks: list[dict], total: int | None = None) -> None:
        if self.callback is None:
            return
        time.sleep(max(0.0, self.last + PROGRESS_INTERVAL - time.monotonic()))
        self.last = time.monotonic()
        message = {"package": PACKAGE, "kind": self.kind, "state": state, "step": None if step is None else {"name": step},
                   "checks": [{"name": row["name"], "result": row["result"]} for row in checks],
                   "done": sum(row["result"] is not None for row in checks), "total": len(checks) if total is None else total,
                   "seconds_left": sum(self.estimates.get(row["name"], 0) for row in checks if row["result"] is None)}
        try:
            self.callback(message)
        except Exception:  # noqa: BLE001 - the contract: stop calling it, and continue the run
            self.callback = None


def _over_budget(sender: _Progress, name: str) -> bool:
    """True when the check `name` must not start: the time that is left of the budget is shorter than its estimate.

    A run that names one EP stops only at the end of the budget (ADR-X7WD item 5). The level `full` has no budget.
    """
    left = None if sender.deadline is None else sender.deadline - time.monotonic()
    return left is not None and (left <= 0 or (not sender.whole and sender.estimates.get(name, 0) > left))


def _timeout(sender: _Progress, limit: float) -> float:
    """The time limit of a child: `limit`, or the time that is left of the budget when that is shorter."""
    return limit if sender.deadline is None else max(0.0, min(limit, sender.deadline - time.monotonic()))


def _cut(problem: str | None, timeout: float, limit: float) -> str | None:
    """`over-budget` for a child that the end of the budget stopped, else `problem` unchanged."""
    return "over-budget" if problem == "timed-out" and timeout < limit else problem


def check_label(execution_provider: str, device_key: str | None) -> str:
    """The name of the check of an EP on a GPU in a report of `certify()`, for example `cuda@10de-2484-0` for the
    device key `gpu:10de:2484:0`. It is the EP key alone with no device key. It has no `:`, so each check name with
    `:` is a part of it."""
    if device_key is None:
        return execution_provider
    return f"{execution_provider}@{device_key.removeprefix('gpu:').replace(':', '-')}"


_label = check_label  # the old private name; the code of this module uses it


def record_failed_pair(execution_provider: str, device_key: str) -> None:
    """Store the result `failed` in `quick-checks.json` for the EP on the GPU of `device_key` on this system.

    An application calls it when its process ended during the quick check of that pair, for example from a crash
    record. It writes the row that a failed check of `certify()` writes, and keeps each other pair. It can never
    store a pass. An unknown or reserved EP key, and a device key that is not a GPU of this host that the EP can
    use, raise `EpRequestError` (a `ValueError`).
    """
    from skellytracker.core import errors
    from skellytracker.core.eps import certification, evidence, store
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.eps.recommendation import ep_gpus
    from skellytracker.core.system.host import probe_host

    catalog, host = load_catalog(), probe_host()
    catalog.ep(execution_provider)  # an unknown or reserved key raises `EpRequestError`
    gpu = dict(ep_gpus(catalog, execution_provider, host)).get(device_key)
    if gpu is None:
        raise errors.EpRequestError(f"{device_key!r} is not the device key of a GPU of this host that {execution_provider!r} can use")
    _record(certification, store, evidence, catalog, host, execution_provider, gpu, "fail", "", (),
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), {})


def _summary(report: dict, skipped: Sequence[dict] = (), mediapipe_installed: bool = True) -> list[dict]:
    """The summary items of section 3.7 of the contract, from the checks of the report: the EPs that ran, in the order of the run.

    An `ep` item has the result of the row of the pair. The CPU EP has no such row: its item is `fail` when one of its
    rows failed, else `record-only`, because the CPU EP is the reference of each comparison. A `gpu-jpeg` item is
    there only when a GPU JPEG decode check ran for the pair: the check `jpeg-decode` of the level `quick`, or the
    checks `jpeg:gpu_decode.*` of the level `full`, where one `fail` gives `fail`. `device` is the id of the GPU in
    `host.gpus`, or None. The items of `skipped` (a pair with a reviewed pass) follow the pairs that ran, before the CPU EP.
    The `component` item of `mediapipe:smoke` follows the CPU EP: the result of the check when it ran, or `skipped` with
    `reviewed` when `details.skipped` gives the check as `reviewed`, or `skipped` with `not-installed` when the check is
    in the report and `mediapipe_installed` is false. A `benchmark` item follows for each timing of the level `full` with a median, in the order of the checks.
    """
    rows = {row["name"]: row["result"] for row in report["checks"]}
    eps = report["details"].get("eps", {})
    items = []
    for label, facts in eps.items():
        if rows.get(label) not in RAN:
            continue
        pair = {"name": _module(label), "device": facts.get("gpu")}
        items.append({"group": "ep", **pair, "result": rows[label]})
        decode = rows.get(f"{label}:jpeg-decode")
        if decode not in RAN:
            found = {result for name, result in rows.items() if name.startswith(f"{label}:jpeg:gpu_decode.")} & {"pass", "fail"}
            decode = "fail" if "fail" in found else "pass" if found else None
        if decode:
            items.append({"group": "gpu-jpeg", **pair, "result": decode})
    items += skipped
    cpu = {result for name, result in rows.items() if name.startswith("cpu:")} & set(RAN)
    if cpu:
        items.append({"group": "ep", "name": SUMMARY_NAMES["cpu"], "device": None, "result": "fail" if "fail" in cpu else "record-only"})
    smoke = {"group": "component", "name": MEDIAPIPE_MODULE, "device": None}
    if rows.get(MEDIAPIPE_CHECK) in RAN:  # as an EP: a check that is `not-run` has no item
        items.append({**smoke, "result": rows[MEDIAPIPE_CHECK]})
    elif report["details"].get("skipped", {}).get(MEDIAPIPE_CHECK) == "reviewed":
        items.append({**smoke, "result": "skipped", "reason": "reviewed"})
    elif MEDIAPIPE_CHECK in rows and not mediapipe_installed:  # only a `component` item can have `not-installed`
        items.append({**smoke, "result": "skipped", "reason": "not-installed"})
    for row in report["checks"]:
        timing, median = TIMING.match(row["name"]), (row.get("numbers") or {}).get("median_ms")
        if timing and row["result"] == "record-only" and median:
            label, stage = timing.groups()
            items.append({"group": "benchmark", "name": _module(label), "device": eps.get(label, {}).get("gpu"), "stage": stage,
                          "ms_per_frame": median, "fps": round(1000 / median, 1)})
    return items


def _module(name: str) -> str:
    """The `module` of a check: the name of `SUMMARY_NAMES` of the EP key at the start of the check name or label, or
    `MEDIAPIPE_MODULE` for `mediapipe:smoke` and its `exit` check."""
    key = name.split("@")[0].split(":")[0]
    return MEDIAPIPE_MODULE if key == "mediapipe" else SUMMARY_NAMES.get(key, key)


def _full_order(selected: list[tuple], host) -> tuple[list[tuple], list[tuple]]:
    """The pairs of the level `full` in the order of ADR-X7WD item 10: the pairs that run before the CPU timings, and the rest.

    First: each pair with no reviewed pass on the GPU that the package recommends (the GPU with the most VRAM, as
    `recommend()` picks it). The rest: the pairs with no reviewed pass on the other GPUs, then the reviewed pairs.
    """
    from skellytracker.core.eps import evidence, gate
    from skellytracker.core.eps.recommendation import _by_vram
    from skellytracker.core.system.host import gpu_device_keys

    recommended = next(iter(_by_vram(gpu_device_keys(host))), (None, None))[0]  # None on a Mac: `coreml` has no device key
    os_name = gate.OS_LABELS.get(host.os_name, host.os_name)
    reviewed = [gpu is not None and evidence.certified(key, gpu, os_name) for _, key, _, gpu, _ in selected]
    first = [item for item, done in zip(selected, reviewed, strict=True) if not done and item[2] == recommended]
    rest = [item for item, done in zip(selected, reviewed, strict=True) if not done and item[2] != recommended]
    return first, rest + [item for item, done in zip(selected, reviewed, strict=True) if done]


def _names(label: str, key: str, device_key: str | None, full: bool = False) -> tuple[str, ...]:
    """The check names of an EP on a GPU at the start of the run, in the order of the report. The last name is the EP check."""
    if key == "cpu":  # `_cpu_names()` has the checks of the CPU EP; a named `cpu` is `not-run` with `not-gpu-ep`
        return (f"{label}:probe", label)
    if full:
        more = (*(f"{label}:pipeline-{cameras}" for cameras in CAMERA_COUNTS),
                *((f"{label}:jpeg",) if key in JPEG_FULL_EPS and device_key is not None else ()))
    else:
        more = tuple(f"{label}:{name}" for name in JPEG_CHECKS) if key in JPEG_EPS and device_key is not None else ()
    return (f"{label}:probe", f"{label}:video", f"{label}:live", *more, label)


def _cpu_names(full: bool = True) -> tuple[str, ...]:
    """The check names of the CPU EP: the CPU reference, and in the level `full` the timings and `cpu:jpeg`. Each name has a `:`."""
    return (*CPU_CHECKS, *((*(f"cpu:pipeline-{cameras}" for cameras in CAMERA_COUNTS), "cpu:jpeg") if full else ()))


def _estimates(selected: list[tuple], settings: dict, full: bool) -> dict[str, int]:
    """The time estimate in seconds of each check that takes time, by its name. No value is calibrated."""
    found = {}
    for label, key, device_key, *_, reason in selected:
        if reason is not None:  # it does not run
            continue
        names = _names(label, key, device_key, full)
        found |= {names[0]: PROBE_SECONDS, names[1]: settings["seconds"].get(key, VIDEO_SECONDS), names[2]: LIVE_SECONDS}
        if full:
            found |= {name: JPEG_FULL_SECONDS if name.endswith(":jpeg") else PIPELINE_SECONDS for name in names[3:-1]}
        elif names[3:-1]:
            found[names[3]] = JPEG_SECONDS  # the two JPEG checks run in one child
    if found or full:
        found[CPU_CHECKS[0]] = CPU_REFERENCE_SECONDS  # the two checks of the CPU reference run in one child
    if full:
        found |= {name: JPEG_FULL_SECONDS if name.endswith(":jpeg") else PIPELINE_SECONDS for name in _cpu_names()[len(CPU_CHECKS):]}
    return found


def _mediapipe_state(level: str, execution_providers, device, host) -> str | None:
    """The state of `mediapipe:smoke` (ADR-X7WD item 11): None when the run has no such check, else `reviewed`, `models-missing` or `run`.

    Only the level `quick` with the default selection (no EP and no device from the caller) has the check. `reviewed`:
    a row of the list `mediapipe` of `ep_evidence.yaml` records a pass for the MediaPipe version, the Python version and
    the OS key of this system. `models-missing`: MediaPipe is not installed.
    """
    if level != "quick" or execution_providers is not None or device is not None:
        return None
    from skellytracker.core.eps import evidence

    try:
        version = importlib.metadata.version("mediapipe")
    except importlib.metadata.PackageNotFoundError:
        version = None
    if evidence.mediapipe_reviewed(version, f"{sys.version_info.major}.{sys.version_info.minor}", evidence.os_key(host.os_label)):
        return "reviewed"
    return "models-missing" if version is None else "run"


def _selection(catalog, host, execution_providers, device=None, *, skip_certified: bool = True) -> list[tuple]:
    """`(label, key, device_key, gpu, reason)` for each EP and GPU to check; `reason` is the code of one that cannot run.

    With `skip_certified` (the level `quick`), an EP on a GPU with a reviewed pass has the reason `reviewed`, also when the
    caller names the EP or the GPU: the caller runs no check for it (ADR-X7WD item 3).
    """
    from skellytracker.core import errors
    from skellytracker.core.eps import evidence, gate, store
    from skellytracker.core.eps.recommendation import ep_gpus
    from skellytracker.core.eps.records import USABLE_STATES
    from skellytracker.core.system.host import gpu_device_keys

    if isinstance(execution_providers, str):
        raise ValueError("execution_providers is a list of EP keys, for example ['cuda']")
    wanted = None if device is None else [device] if isinstance(device, str) else list(device)
    for item in wanted or ():
        if item not in dict(gpu_device_keys(host)):
            raise errors.EpRequestError(f"{item!r} is not the device key of a GPU of this host")
    default = execution_providers is None
    keys = ([key for key in catalog.keys() if catalog.device_row(key) is not None or gate.chip_of(catalog, key, host)] if default
            else list(dict.fromkeys(execution_providers)))
    found = []
    for key in keys:
        catalog.ep(key)  # an unknown or reserved key raises `EpRequestError`
        chip = gate.chip_of(catalog, key, host)
        if chip is not None:  # `coreml`: one check on the chip of the host, with no device key and the name `<key>`
            certified = skip_certified and evidence.certified(key, chip, gate.OS_LABELS.get(host.os_name, host.os_name))
            if not (default and wanted is not None):
                found.append((key, key, None, chip, "gpu-not-usable" if wanted is not None else "reviewed" if certified else
                              _setup_reason(store.pack_state(catalog, key, None, None, host.os_build))))
            continue
        if catalog.device_row(key) is None:
            found.append((key, key, None, None, "not-gpu-ep"))
            continue
        usable = ep_gpus(catalog, key, host)
        pairs = [(device_key, gpu) for device_key, gpu in usable if wanted is None or device_key in wanted]
        for device_key, gpu in pairs:
            state = store.pack_state(catalog, key, gpu, device_key, host.os_build)
            # the default: a plugin EP must be usable; `directml` and a Windows ML EP are always in it
            if default and catalog.pack(key) is not None and state[0] not in USABLE_STATES:
                continue
            reviewed = skip_certified and evidence.certified(key, gpu, host.os_name)
            found.append((_label(key, device_key), key, device_key, gpu, "reviewed" if reviewed else _setup_reason(state)))
        if not pairs and not default:
            reason = "gpu-not-usable" if usable else _setup_reason(store.pack_state(catalog, key, None, None, host.os_build))
            found.append((key, key, None, None, reason))
    return found


def _setup_reason(state: tuple) -> str | None:
    return None if state[0] in RUNNABLE_STATES else "ep-" + (state[1] or state[0]).replace("_", "-")


def _pipeline(catalog, pipeline) -> tuple[dict, str, str | None]:
    """The mapping of the pipeline for the child, its key, and the reason code when the pipeline checks cannot run."""
    from skellytracker.core import pipelines

    config = pipeline if isinstance(pipeline, pipelines.PipelineConfig) else pipelines.load_pipeline(
        catalog.data["certification"]["pipeline"] if pipeline is None else pipeline)
    check = pipelines.check_pipeline(config)
    reason = ("models-missing" if any(warning.code == "missing_dependency" for warning in check.warnings)
              else None if set(COMPARED_OUTPUTS) <= set(check.output_schema) else "outputs-not-comparable")
    return pipelines.export_pipeline(config), f"{config.pipeline_id}@{config.source.name}", reason


def _quick(report: dict, selected: list[tuple], catalog, host, sender: _Progress, cancel, resolved: tuple,
           full: bool = False, first: int = 0, test_media_dir: str | os.PathLike | None = None, abandon=None) -> None:
    """Run the CPU reference, then the checks of each EP of `selected`, and more checks for each EP with `full`.

    With `full`, the CPU timings run after the first `first` pairs of `selected` (`_full_order()`). After a set
    `abandon`, it stores no local result.
    """
    from skellytracker.core.eps import certification, evidence, gate, store
    from skellytracker.core.system.runtime import probe_runtime

    rows = {row["name"]: row for row in report["checks"]}
    mapping, pipeline_key, image_reason = resolved
    settings = {**catalog.data["certification"], "frames": certification.frames_record(test_media_dir), "pipeline": mapping}
    try:
        certification.frames_file(settings)
        media = None
    except certification.FramesUnavailableError:
        media = "test-media-missing"  # `certify()` downloads nothing (ADR-X7WD item 6)
    image_reason = media or image_reason
    details = {"pipeline": pipeline_key, "eps": {}}
    reference = _cpu_reference(report, settings, image_reason, sender, cancel) if CPU_CHECKS[0] in rows else None
    if full:
        details["full"] = {"camera_counts": list(CAMERA_COUNTS), "warmup_calls": certification.WARMUP_CALLS,
                           "timed_calls": certification.TIMED_CALLS, "running_mode": "video"}
    for item in [*selected[:first], None, *selected[first:]] if full else selected:
        if cancel is not None and cancel.is_set():
            break
        if item is None:  # the CPU timings of the level `full`
            _timings(report, "cpu", "cpu", None, settings, image_reason, sender, cancel)
            _jpeg_full(report, "cpu", None, None, None, sender, cancel)
            continue
        label, key, device_key, gpu, setup = item
        names = _names(label, key, device_key, full)
        details["eps"][label] = {"gpu": None if gpu is None else evidence.gpu_id(gpu), "device": device_key,
                                 "pack_version": gate.pack_version(catalog, key), **store.installed_pack_facts(catalog, key)}
        if setup is not None:
            for name in names:
                rows[name].update(result="not-run", reason=setup)
            sender.send("running", None, report["checks"])
            continue
        jpeg, stored, kept = () if full else names[3:-1], {}, False
        temporary = catalog.ep_status(key) == "field-test" and key not in store.field_test_opt_ins()
        if temporary:
            store.opt_in_field_test(key)
        try:
            setup = _setup_reason(store.pack_state(catalog, key, gpu, device_key, host.os_build)) if temporary else None
            if setup is None:
                _probe(report, label, key, device_key, sender, cancel)
                _video(report, label, key, device_key, settings, image_reason, sender, cancel, details["eps"][label], reference)
                _live(report, label, key, device_key, settings, media, sender, cancel)
                if full:
                    _timings(report, label, key, device_key, settings,
                             None if rows[names[1]]["result"] == "pass" else "video-not-passed", sender, cancel)
                    if f"{label}:jpeg" in rows:
                        stored = _jpeg_full(report, label, key, device_key,
                                            None if rows[names[0]]["result"] == "pass" else "probe-not-passed", sender, cancel)
                elif jpeg:
                    _jpeg(report, label, key, device_key, sender, cancel)
            else:
                for name in names[:-1]:
                    rows[name].update(result="not-run", reason=setup)
            parts = [rows[name] for name in names[:3]]  # the roll-up check `<label>`: the probe, `video` and `live`
            failed = next((row for row in parts if row["result"] == "fail"), None)
            not_run = next((row for row in parts if row["result"] == "not-run"), None)
            if failed is None and not_run is None:
                rows[label].update(result="pass", reason=None)
            else:
                rows[label].update(result="fail" if failed else "not-run", reason=(failed or not_run)["reason"])
            # a set abandon stores nothing: a crash record can have stored the failure of this pair (ADR-Q9R6 item 2)
            if rows[label]["result"] in ("pass", "fail") and not (abandon is not None and abandon.is_set()):
                _record(certification, store, evidence, catalog, host, key, gpu, rows[label]["result"], pipeline_key,
                        details["eps"][label].get("models", ()), report["created_utc"],
                        stored if full else {name.rsplit(":", 1)[1]: rows[name]["result"] for name in jpeg})
                kept = rows[label]["result"] == "pass"
            sender.send("running", None, report["checks"])
        finally:
            if temporary and not kept:  # the opt-in stays only with a stored pass
                _cleanup(report, "field-test-opt-in", lambda key=key: store.drop_field_test_opt_in(key))
    if rows.get(MEDIAPIPE_CHECK, {}).get("result", "") is None:  # after each EP check
        _mediapipe(report, settings, media, sender, cancel)
    _against_cpu(report)
    runtime = probe_runtime()  # imports onnxruntime in this process; the children load the EPs
    ort = dict(zip(runtime.ort_packages, runtime.ort_package_versions, strict=True))
    ort_name = "onnxruntime-windowsml" if "onnxruntime-windowsml" in ort else next(iter(ort), None)
    details["versions"] = {"ort_distribution": ort_name, "ort_version": ort.get(ort_name), "windowsml": runtime.windowsml_version,
                           "catalog_revision": catalog.revision, "set_hash": evidence.set_hash(catalog)}
    frames = settings["frames"]  # section 3.9 of the format: the test media file that a check used, never its path
    used = media is None and any(row["result"] in RAN and FRAME_CHECK.search(row["name"]) for row in report["checks"])
    report["test_media"] = [{"name": Path(frames["path"]).name, "sha256": frames["sha256"], "bytes": frames["bytes"],
                             "source": "bundled" if frames["dir"] is None else "shared"}] if used else []
    report["details"] = details


def _probe(report: dict, label: str, key: str, device_key: str | None, sender: _Progress, cancel) -> None:
    from skellytracker.core.eps import verification

    row = next(row for row in report["checks"] if row["name"] == f"{label}:probe")
    if _over_budget(sender, row["name"]):
        row.update(result="not-run", reason="over-budget")
        return
    sender.send("running", row["name"], report["checks"])
    started, timeout = time.monotonic(), _timeout(sender, verification.TIMEOUT_SECONDS)
    try:
        (verdict,) = verification.verify([key], device_key=device_key, force=True, cancel=cancel, timeout=timeout)
    except Exception as error:  # noqa: BLE001 - a setup failure: the EP did not run
        row.update(result="not-run", reason=type(error).__name__)
        return
    numbers = {"seconds": round(time.monotonic() - started, 1), "max_abs_diff": verdict.max_abs_diff}
    code = _cut(verdict.reason_code, timeout, verification.TIMEOUT_SECONDS)
    if verdict.ok:
        row.update(result="pass", reason=None)
    elif code in ("cancelled", "over-budget"):
        row.update(result="not-run", reason=code)
    elif verdict.reason_code in CHILD_FAILURES:
        row.update(result="fail", reason=CHILD_FAILURES[verdict.reason_code])
        numbers["exit_code"] = verdict.exit_code
    else:
        row.update(result="fail", reason=f"probe-{verdict.level.lower()}-failed")
    row["numbers"] = numbers
    if verdict.exit_reason_code:
        _add_exit(report, row["name"], verdict.exit_reason_code)


def _row(report: dict, name: str) -> dict:
    return next(row for row in report["checks"] if row["name"] == name)


def _session_result(rows: list[dict], mode: str, found: dict | None, problem: str | None, exit_code: int | None) -> dict | None:
    """The result of `mode` of a child of `session_run()`. A child with no result sets each row of `rows`, and gives None.

    An error in the mode stays in the result as `{"error": <exception class name>}`: the caller gives `fail`.
    """
    if found is not None and "error" not in found:
        return found.get(mode) or {"error": "no-result"}
    code = found["error"] if found else problem
    for row in rows:
        if code == "cancelled":
            row.update(result="not-run", reason="cancelled")
        elif code in CHILD_FAILURES:
            row.update(result="fail", reason=CHILD_FAILURES[code], numbers={"exit_code": exit_code})
        else:  # `over-budget`, or a setup failure before the first mode, for example a test frames file that is not valid
            row.update(result="not-run", reason=code)
    return None


def _finite(frame: dict) -> bool:
    """No NaN or infinity in a box of a present row, and a finite position for each point with a finite score."""
    import numpy as np

    boxes, body = frame["boxes"], frame["wholebody"]
    score, xy = body.score[body.present], body.xy[body.present]
    return bool(np.isfinite(boxes.xyxy[boxes.present]).all() and np.isfinite(xy[np.isfinite(score)]).all())


def _cpu_reference(report: dict, settings: dict, image_reason: str | None, sender: _Progress, cancel) -> dict | None:
    """The CPU reference of the run: `cpu:video` and `cpu:live`, in one `spawn` child on the CPU EP.

    `cpu:video` passes when each frame has a person, and `cpu:live` passes when its outputs are finite. It gives the
    frames of `video` and `cpu_ms`, or None when `cpu:video` did not pass.
    """
    from skellytracker.core.eps import certification

    video, live = (_row(report, name) for name in CPU_CHECKS)
    if image_reason is not None or (cancel is not None and cancel.is_set()) or _over_budget(sender, video["name"]):
        for row in (video, live):
            row.update(result="not-run", reason=image_reason or ("cancelled" if cancel is not None and cancel.is_set() else "over-budget"))
        return None
    sender.send("running", video["name"], report["checks"])
    started, timeout = time.monotonic(), _timeout(sender, certification.WIDE_TIMEOUT_SECONDS)
    found, problem, exit_code = certification.session_run(
        "cpu", settings, ("video", "live"), cancel=cancel, timeout=timeout,
        progress=lambda mode: sender.send("running", live["name"], report["checks"]) if mode == "live" else None)
    problem = _cut(problem, timeout, certification.WIDE_TIMEOUT_SECONDS)
    run = _session_result([video, live], "video", found, problem, exit_code)
    if run is None:
        return None
    seconds = round(time.monotonic() - started, 1)
    if "error" in run:
        video.update(result="fail", reason=run["error"])
    elif not all(frame["boxes"].present.any() for frame in run["frames"]):
        video.update(result="fail", reason="no-person-on-cpu")
    else:
        video.update(result="pass", reason=None, numbers={"frames": len(run["frames"]), "cpu_ms": run["ms"], "seconds": seconds})
    other = found.get("live") or {"error": "no-result"}
    if "error" in other:
        live.update(result="fail", reason=other["error"])
    else:
        reason = None if all(_finite(frame) for frame in other["frames"]) else "not-finite"
        live.update(result="fail" if reason else "pass", reason=reason, numbers={"frames": len(other["frames"])})
    if problem:
        _add_exit(report, live["name"], problem)
    return {"frames": run["frames"], "cpu_ms": run["ms"]} if video["result"] == "pass" else None


def _video(report: dict, label: str, key: str, device_key: str | None, settings: dict, image_reason: str | None,
           sender: _Progress, cancel, details: dict, reference: dict | None) -> None:
    """The check `<label>:video`: the pipeline on the test frames in the running mode `video` on the EP, in a `spawn` child.

    It compares frame 0 with frame 0 of the CPU reference with each threshold of the catalog. Each later frame has the
    lighter rule of `compare_results()` with `keypoints` false: the people, the finite outputs and the box IoU (ADR-R0EB
    item 3). The first frame that fails gives the reason. `numbers` holds the numbers of `compare_results()` of frame 0,
    and `later_keypoint_box_fraction_max`: the worst keypoint difference of the later frames, a record only.
    """
    from skellytracker.core.eps import certification

    row, probe = _row(report, f"{label}:video"), _row(report, f"{label}:probe")
    if probe["result"] != "pass" or (cancel is not None and cancel.is_set()):
        row.update(result="not-run", reason="probe-not-passed" if probe["result"] != "pass" and probe["reason"] != "cancelled"
                   else "cancelled")
        return
    if image_reason is not None or reference is None:
        row.update(result="not-run", reason=image_reason or "cpu-reference-missing")
        return
    if _over_budget(sender, row["name"]):
        row.update(result="not-run", reason="over-budget")
        return
    sender.send("running", row["name"], report["checks"])
    started, timeout = time.monotonic(), _timeout(sender, certification.WIDE_TIMEOUT_SECONDS)
    found, problem, exit_code = certification.session_run(key, settings, ("video",), device_key, cancel=cancel, timeout=timeout)
    problem = _cut(problem, timeout, certification.WIDE_TIMEOUT_SECONDS)
    run = _session_result([row], "video", found, problem, exit_code)
    if run is None:
        return
    if "error" in run:
        row.update(result="fail", reason=run["error"])
    else:
        compared = [certification.compare_results(cpu, ep, settings["thresholds"], keypoints=index == 0)
                    for index, (cpu, ep) in enumerate(zip(reference["frames"], run["frames"], strict=True))]
        failed = next((item for item in compared if not item["ok"]), None)
        reason = failed["reason_code"] if failed else "partial-placement" if certification.PARTIAL_PLACEMENT in run["warnings"] else None
        row.update(result="fail" if reason else "pass", reason=reason)
        later = [item["keypoint_box_fraction_max"] for item in compared[1:] if item["keypoint_box_fraction_max"] is not None]
        numbers = {name: compared[0][name] for name in COMPARED_NUMBERS if compared[0][name] is not None}
        row["numbers"] = {**numbers, "later_keypoint_box_fraction_max": max(later, default=None), "frames": len(compared),
                          "seconds": round(time.monotonic() - started, 1), "ep_ms": run["ms"],
                          "cpu_ms": reference["cpu_ms"], "speed_against_cpu": certification.speed_against_cpu(run["ms"], reference["cpu_ms"])}
        details.update(models=run["models"], warnings=run["warnings"])
    if problem:
        _add_exit(report, row["name"], problem)


def _live(report: dict, label: str, key: str, device_key: str | None, settings: dict, media: str | None, sender: _Progress,
          cancel) -> None:
    """The check `<label>:live`: a smoke run of the test frames in the running mode `live` on the EP, in a `spawn` child.

    It passes when each frame has finite outputs and a person. It compares nothing. `media` is the reason code of test
    frames that are not valid.
    """
    from skellytracker.core.eps import certification

    row, video = _row(report, f"{label}:live"), _row(report, f"{label}:video")
    if media is not None:
        row.update(result="not-run", reason=media)
        return
    if video["result"] != "pass" or (cancel is not None and cancel.is_set()):
        row.update(result="not-run", reason="cancelled" if video["result"] == "pass" or video["reason"] == "cancelled" else "video-not-passed")
        return
    if _over_budget(sender, row["name"]):
        row.update(result="not-run", reason="over-budget")
        return
    sender.send("running", row["name"], report["checks"])
    timeout = _timeout(sender, certification.WIDE_TIMEOUT_SECONDS)
    found, problem, exit_code = certification.session_run(key, settings, ("live",), device_key, cancel=cancel, timeout=timeout)
    problem = _cut(problem, timeout, certification.WIDE_TIMEOUT_SECONDS)
    run = _session_result([row], "live", found, problem, exit_code)
    if run is None:
        return
    if "error" in run:
        row.update(result="fail", reason=run["error"])
    else:
        frames = run["frames"]
        reason = ("not-finite" if not all(_finite(frame) for frame in frames)
                  else "no-person" if not all(frame["boxes"].present.any() for frame in frames) else None)
        row.update(result="fail" if reason else "pass", reason=reason, numbers={"frames": len(frames), "ep_ms": run["ms"]})
    if problem:
        _add_exit(report, row["name"], problem)


def _holistic_finite(frame) -> bool:
    """Finite values for each point that MediaPipe found in a present row, and a finite score for each point.

    A missing point has NaN coordinates and the score 0 (`HolisticKeypoints`): it is normal. A point with a value that
    is not NaN is a found point: each of its coordinates must be finite.
    """
    import numpy as np

    xy, score = frame.xy[frame.present], frame.score[frame.present]
    return bool(np.isfinite(xy[~np.isnan(xy).all(axis=-1)]).all() and np.isfinite(score).all())


def _mediapipe(report: dict, settings: dict, media: str | None, sender: _Progress, cancel) -> None:
    """The check `mediapipe:smoke` (ADR-X7WD item 11): the pipeline `mediapipe-holistic-tasks` on the test frames in the
    running mode `live`, in a `spawn` child. It is not an EP check: it stores nothing and never changes an EP check.

    It passes when each frame has a present row with finite values (`_holistic_finite()`). It fails with `not-finite`,
    with `no-person` on a frame with no present row, and with the error of the run as `<ep>:live` does.
    """
    from skellytracker.core.eps import certification

    row = _row(report, MEDIAPIPE_CHECK)
    if cancel is not None and cancel.is_set():
        return  # `certify()` gives each check that did not end `cancelled`
    if media is not None:
        row.update(result="not-run", reason=media)
        return
    if _over_budget(sender, row["name"]):
        row.update(result="not-run", reason="over-budget")
        return
    sender.send("running", row["name"], report["checks"])
    started, timeout = time.monotonic(), _timeout(sender, certification.WIDE_TIMEOUT_SECONDS)
    found, problem, exit_code = certification.mediapipe_run(settings, cancel=cancel, timeout=timeout)
    problem = _cut(problem, timeout, certification.WIDE_TIMEOUT_SECONDS)
    run = _session_result([row], "live", found, problem, exit_code)
    if run is None:
        return
    if "error" in run:
        row.update(result="fail", reason=run["error"])
    else:
        frames = run["frames"]
        reason = ("not-finite" if not all(_holistic_finite(frame) for frame in frames)
                  else "no-person" if not all(frame.present.any() for frame in frames) else None)
        row.update(result="fail" if reason else "pass", reason=reason,
                   numbers={"frames": len(frames), "seconds": round(time.monotonic() - started, 1)})
    if problem:
        _add_exit(report, row["name"], problem)


def _jpeg_child(key: str, device_key: str | None, connection) -> None:
    """The child of `_jpeg()`: it sends the two checks of the GPU frame path, or `{"error": <exception class name>}`."""
    try:
        from skellytracker.core.decode.certification import run_jpeg_quick_checks

        result = {"checks": run_jpeg_quick_checks(key, device_key=device_key)}  # it switches the check rule off itself
    except Exception as error:  # noqa: BLE001 - a fixed code: an error text can hold a path
        result = {"error": type(error).__name__}
    connection.send(result)
    connection.close()


def _jpeg_spawn(key: str, device_key: str, cancel, timeout: float = JPEG_TIMEOUT_SECONDS) -> tuple[dict | None, str | None, int | None]:
    from skellytracker.core.eps import verification

    return verification.spawn_child(_jpeg_child, (key, device_key), timeout=timeout, cancel=cancel)


def _jpeg(report: dict, label: str, key: str, device_key: str, sender: _Progress, cancel) -> None:
    """The two JPEG checks of the GPU frame path, in one `spawn` child. They keep the reason codes of
    `core/decode/certification.py`, with no `detail` text. They never change the EP check."""
    rows = [next(row for row in report["checks"] if row["name"] == f"{label}:{name}") for name in JPEG_CHECKS]
    video = _row(report, f"{label}:video")
    if video["result"] != "pass" or (cancel is not None and cancel.is_set()):
        for row in rows:
            row.update(result="not-run", reason="cancelled" if video["result"] == "pass" or video["reason"] == "cancelled"
                       else "video-not-passed")
        return
    if _over_budget(sender, rows[0]["name"]):
        for row in rows:
            row.update(result="not-run", reason="over-budget")
        return
    sender.send("running", rows[0]["name"], report["checks"])
    timeout = _timeout(sender, JPEG_TIMEOUT_SECONDS)
    found, problem, exit_code = _jpeg_spawn(key, device_key, cancel, timeout)
    problem = _cut(problem, timeout, JPEG_TIMEOUT_SECONDS)
    if found is None or "error" in found:
        code = found["error"] if found else problem
        for row in rows:
            if code in ("cancelled", "over-budget"):
                row.update(result="not-run", reason=code)
            else:
                row.update(result="fail", reason=CHILD_FAILURES.get(code, code))
                if code in CHILD_FAILURES:
                    row["numbers"] = {"exit_code": exit_code}
        return
    by_name = {item["name"]: item for item in found.get("checks", ())}
    for row, name in zip(rows, JPEG_CHECKS, strict=True):
        item = by_name.get(name)
        if item is None:
            row.update(result="fail", reason="no-result")
            continue
        row.update(result=item["result"], reason=None if item["result"] == "pass" else item["reason"])
        numbers = {field: value for field, value in (item.get("numbers") or {}).items()
                   if value is None or isinstance(value, bool | int | float)}
        if numbers:
            row["numbers"] = numbers
    if problem:
        _add_exit(report, rows[-1]["name"], problem)


def _numbers(values: dict) -> dict:
    """The values that a check can hold in `numbers`: a number, a boolean, None, or a short fixed word."""
    return {name: value for name, value in values.items()
            if value is None or isinstance(value, bool | int | float) or (isinstance(value, str) and value in ("faster", "slower", "similar"))}


def _timings(report: dict, label: str, key: str, device_key: str | None, settings: dict, reason: str | None,
             sender: _Progress, cancel) -> None:
    """The pipeline timing at each camera count of `CAMERA_COUNTS`, each in a `spawn` child: the checks `<label>:pipeline-<n>`.

    A timing is `record-only`: it never changes the EP check. `reason` is the code of a timing that cannot
    start. A run that raises, for example with no VRAM left at 6 cameras, is `not-run` with the exception class.
    """
    from skellytracker.core.eps import certification

    for cameras in CAMERA_COUNTS:
        row = next(row for row in report["checks"] if row["name"] == f"{label}:pipeline-{cameras}")
        if cancel is not None and cancel.is_set():
            reason = "cancelled"
        if reason is not None:
            row.update(result="not-run", reason=reason)
            continue
        sender.send("running", row["name"], report["checks"])
        found, problem, exit_code = certification.timing_run(key, settings, cameras, device_key, cancel=cancel)
        if found is None or "error" in found:
            code = found["error"] if found else problem
            if code in CHILD_FAILURES:
                row.update(result="fail", reason=CHILD_FAILURES[code], numbers={"exit_code": exit_code})
            else:
                row.update(result="not-run", reason=code)
            continue
        row.update(result="record-only", reason=None, numbers=_numbers(found))
        if problem:
            _add_exit(report, row["name"], problem)


def _against_cpu(report: dict) -> None:
    """Add `against_cpu` and `speed_against_cpu` to each timing of a pair with a median, from the median of the CPU EP.

    It runs after each timing, because the level `full` times some pairs before the CPU EP (ADR-X7WD item 10).
    """
    from skellytracker.core.eps import certification

    medians = {match.group(2): (row.get("numbers") or {}).get("median_ms") for row in report["checks"]
               if (match := TIMING.match(row["name"])) and match.group(1) == "cpu"}
    for row in report["checks"]:
        match = TIMING.match(row["name"])
        median, cpu = (row.get("numbers") or {}).get("median_ms"), match and medians.get(match.group(2))
        if match and match.group(1) != "cpu" and median and cpu:
            row["numbers"].update(against_cpu=round(median / cpu, 2), speed_against_cpu=certification.speed_against_cpu(median, cpu))


def _jpeg_full_child(key: str | None, device_key: str | None, connection) -> None:
    """The child of `_jpeg_full()`: it sends the checks of the JPEG certification, or `{"error": <exception class name>}`."""
    try:
        from skellytracker.core.decode import certification

        found = certification.run_jpeg_certification(key, device_key=device_key)  # it switches the check rule off itself
        result = {"checks": found["checks"], "quick": certification.QUICK_CHECKS}
    except Exception as error:  # noqa: BLE001 - a fixed code: an error text can hold a path
        result = {"error": type(error).__name__}
    connection.send(result)
    connection.close()


def _jpeg_full_spawn(key: str | None, device_key: str | None, cancel) -> tuple[dict | None, str | None, int | None]:
    from skellytracker.core.eps import verification

    return verification.spawn_child(_jpeg_full_child, (key, device_key), timeout=JPEG_FULL_TIMEOUT_SECONDS, cancel=cancel)


def _jpeg_full(report: dict, label: str, key: str | None, device_key: str | None, reason: str | None,
               sender: _Progress, cancel) -> dict:
    """The JPEG certification of `core/decode/certification.py` on one EP, or on the CPU paths with no `key`, in a `spawn` child.

    The check `<label>:jpeg` is the outcome: `fail` when a check failed, else `pass` when a check passed. Each
    check of the certification follows it as `<label>:jpeg:<name>`, with its result, its reason code and its
    numbers, and with no `detail` text. They never change the EP check. `reason` is the code of a run that
    cannot start. It returns the stored result of the two checks of the quick level, for `cuda` and `trt-rtx`.
    """
    row = next(row for row in report["checks"] if row["name"] == f"{label}:jpeg")

    def stored(results: dict, names: dict, fallback: str) -> dict:
        return {name: results.get(source, fallback) for source, name in names.items()} if key in JPEG_EPS else {}

    not_run = {name: name for name in JPEG_CHECKS}
    if cancel is not None and cancel.is_set():
        reason = "cancelled"
    if reason is not None:
        row.update(result="not-run", reason=reason)
        return stored({}, not_run, "not-run")
    sender.send("running", row["name"], report["checks"])
    found, problem, exit_code = _jpeg_full_spawn(key, device_key, cancel)
    if found is None or "error" in found:
        code = found["error"] if found else problem
        if code == "cancelled":
            row.update(result="not-run", reason="cancelled")
            return stored({}, not_run, "not-run")
        row.update(result="fail", reason=CHILD_FAILURES.get(code, code))
        if code in CHILD_FAILURES:
            row["numbers"] = {"exit_code": exit_code}
        return stored({}, not_run, "fail")
    new = []
    for item in found.get("checks", ()):
        check = {"name": f"{label}:jpeg:{item['name']}", "result": item["result"],
                 "reason": None if item["result"] == "pass" else item.get("reason")}
        numbers = _numbers(item.get("numbers") or {})
        if numbers:
            check["numbers"] = numbers
        new.append(check)
    index = report["checks"].index(row)
    report["checks"][index + 1:index + 1] = new
    failed = next((check for check in new if check["result"] == "fail"), None)
    if failed is not None:
        row.update(result="fail", reason=failed["reason"])
    elif any(check["result"] == "pass" for check in new):
        row.update(result="pass", reason=None)
    else:
        row.update(result="not-run", reason="no-check")
    if problem:
        _add_exit(report, row["name"], problem)
    return stored({item["name"]: item["result"] for item in found.get("checks", ())}, found.get("quick") or {}, "not-run")


def _add_exit(report: dict, name: str, code: str) -> None:
    """The check `exit` of the contract for a child that gave its result and then did not exit cleanly."""
    index = next(i for i, row in enumerate(report["checks"]) if row["name"] == name)
    report["checks"].insert(index + 1, {"name": f"{name}:exit", "result": "record-only", "reason": code})


def _record(certification, store, evidence, catalog, host, key, gpu, result: str, pipeline_key: str, models, created: str,
            jpeg: dict) -> None:
    """Store the local result of the quick check of the pair (ADR-21BK item 2)."""
    from skellytracker.core.eps import exits

    pair = certification.pair_key(catalog, key, gpu, host.os_name)
    with store.store_lock():
        if result == "pass":
            exits.forget(pair)  # a passed quick check removes the count of unclean exits (ADR-ER5X item 5)
        path = store.store_root() / "quick-checks.json"
        store.write_json(path, {**(store.read_json(path) or {}), pair: {
            "result": "passed" if result == "pass" else "failed", "set_hash": evidence.set_hash(catalog), "pipeline": pipeline_key,
            "precisions": {model["key"]: model["precision"] for model in models}, "created_utc": created,
            **({"jpeg": jpeg} if jpeg else {})}})


def _cleanup(report: dict, name: str, step: Callable[[], object]) -> None:
    try:
        step()
    except Exception as error:  # noqa: BLE001 - a failed cleanup step is a row of `cleanup`, and the report still returns
        report["cleanup"].append({"name": name, "result": "fail", "reason": type(error).__name__})


def _base_report(level: str, created: str, host) -> tuple[dict, list[str]]:
    """The module report of `level` with no check yet, and the evidence reasons of its block `package`.

    `certify()` starts from it. `tools/certify_platform.py` uses it when its section 4 gave no report.
    """
    package, reasons = _package()
    return {"schema": SCHEMA, "package": package, "kind": level, "created_utc": created, "host": _host(host),
            "checks": [], "cleanup": [], "details": {}}, reasons


def _package() -> tuple[dict, list[str]]:
    """The block `package` and its evidence reasons: `no-version`, `no-commit` and `modified-tree`."""
    try:
        version = importlib.metadata.version("skellytracker")
    except importlib.metadata.PackageNotFoundError:
        version = None
    commit, modified = _commit()
    reasons = [code for code, bad in (("no-version", not (version and SEMVER.match(version))),
                                      ("no-commit", not (commit and COMMIT.match(commit))),
                                      ("modified-tree", modified is not False)) if bad]
    return {"name": PACKAGE, "version": version, "commit": commit, "tree_modified": modified}, reasons


def _commit() -> tuple[str | None, bool | None]:
    """The commit of the source and whether the tree had a change: from `skellytracker/_build_info.py`, which a build
    writes (`COMMIT`, `TREE_MODIFIED`); else from the PEP 610 record of an install from a git URL; else from `git` in a
    checkout; else `(None, None)`."""
    try:
        from skellytracker import _build_info  # absent in the repository: a build writes it

        return _build_info.COMMIT, _build_info.TREE_MODIFIED
    except ImportError:
        pass
    try:
        text = importlib.metadata.distribution("skellytracker").read_text("direct_url.json")
        commit = (json.loads(text or "{}").get("vcs_info") or {}).get("commit_id")
        if commit:
            return commit, False  # pip builds a git URL from a clean clone of that commit
    except (importlib.metadata.PackageNotFoundError, ValueError):
        pass
    root = Path(__file__).resolve().parents[1]
    if getattr(sys, "frozen", False) or not (root / ".git").exists() or shutil.which("git") is None:
        return None, None
    try:
        head, status = (subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30,  # noqa: S603, S607
                                       stdin=subprocess.DEVNULL, check=True).stdout
                        for args in (("rev-parse", "HEAD"), ("status", "--porcelain", "--untracked-files=normal")))
    except (OSError, subprocess.SubprocessError):
        return None, None
    return head.strip(), bool(status.strip())


def _host(host) -> dict:
    from skellytracker.core.eps import evidence

    return {"os": {"name": OS_NAMES.get(host.os_name, host.os_name), "release": host.os_release, "version": host.os_version,
                   "build": host.os_build, "label": host.os_label, "arch": ARCHES.get(host.arch.lower(), host.arch.lower())},
            "cpu": {"name": host.cpu_name}, "memory_bytes": host.memory_total_bytes,
            "gpus": [{"vendor": gpu.vendor, "name": gpu.name, "id": evidence.gpu_id(gpu), "driver_version": gpu.driver_version,
                      "vram_bytes": gpu.vram_total_bytes, "shared_memory_bytes": gpu.shared_memory_bytes} for gpu in host.gpus]}


def _private_words() -> list[str]:
    words = {os.environ.get("USERNAME"), os.environ.get("USER"), Path.home().name, socket.gethostname(), platform.node()}
    words |= {word[: -len(".local")] for word in words if word and word.lower().endswith(".local")}  # the short macOS host name
    return sorted((word for word in words if word), key=len, reverse=True)


def _scrub(report: dict) -> dict:
    """Remove the user name, the host name, the home folder and each absolute path from each key and each value.

    A name that is also a word of a public fact (the host block, the check names, the reason codes) stays, and
    `details.scrub.exempted_terms` gives the count of such names (rules 12 and 13 of section 6 of the contract).
    """
    public = "\n".join([json.dumps(report["host"]), *(f"{row['name']} {row['reason']}" for row in report["checks"])])
    words = _private_words()
    kept = [word for word in words if not re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", public, re.IGNORECASE)]
    paths = sorted(filter(None, {str(Path.home()), sys.prefix}), key=len, reverse=True)

    def clean(value):
        if isinstance(value, dict):
            return {clean(name): clean(item) for name, item in value.items()}
        if isinstance(value, list | tuple):
            return [clean(item) for item in value]
        if not isinstance(value, str):
            return value
        for path in paths:
            for form in {path, path.replace("\\", "/"), path.replace("/", "\\")}:
                value = re.sub(re.escape(form), "<path>", value, flags=re.IGNORECASE)
        for word in kept:
            value = re.sub(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", "<private>", value, flags=re.IGNORECASE)
        return PATH_PATTERN.sub("<path>", value)

    report = clean(report)
    report["details"]["scrub"] = {"exempted_terms": len(words) - len(kept)}
    return report
