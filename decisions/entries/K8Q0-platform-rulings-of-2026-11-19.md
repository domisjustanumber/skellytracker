# K8Q0 — Platform rulings of 2026-11-19: host facts, ONNX Runtime through this package, the EP page

**Status:** absorbed into [Package: Layout](../../skellytracker/AGENTS.md#layout), [Package: ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime), [Package: Freeze rules](../../skellytracker/AGENTS.md#freeze-rules), [`core/system/__init__.py`](../../skellytracker/core/system/__init__.py), [`core/eps/__init__.py`](../../skellytracker/core/eps/__init__.py), [`core/eps/cli.py`](../../skellytracker/core/eps/cli.py), 2026-11-23 (absorb pass of 2026-11-23; PR: pending). It was `accepted` from 2026-11-19 (user).

## Decision

1. **Host facts.** Hardware facts and live metrics have one home: `core/system` and `core/metrics`
   of this package. freemocap removes its own gathering. It takes the facts for its anonymous ping
   from `probe_host()` and `probe_environment()`. This package sends no ping. skellycam is not asked
   to depend on this package. Built today: `LiveSample.load_average_1m`.
2. **ONNX Runtime through this package.** When freemocap uses the entry points `detectors`,
   `pipelines`, `eps`, `system` and `metrics`, it declares neither `onnx` nor `onnxruntime`. They
   come only through this package. This package then owns the PyInstaller collection of ONNX
   Runtime: a hook in `skellytracker/_pyinstaller/`. It is not built. This changes the
   [Freeze rules](../../skellytracker/AGENTS.md#freeze-rules) of `skellytracker/AGENTS.md`:
   - "Do not add a hook for an other package to `_pyinstaller/`." becomes\
     -> "Do not add a hook for an other package to `_pyinstaller/`. The one exception is the hook
     of ONNX Runtime ([ADR-K8Q0](K8Q0-platform-rulings-of-2026-11-19.md) item 2)."
3. **Pin.** freemocap pins this package to an exact commit of the working branch only until the
   SemVer scheme of the user exists.
4. **EP page of freemocap.** The first EP page of freemocap shows the EPs with their state, a pick,
   the install with progress and cancel, the reason text, the EPs of the Windows ML catalog with as
   much information as possible, and the remove and certify buttons. This package gives each fact
   through `status()`. freemocap holds no EP fact of its own: the row `core/eps/` of
   [Layout](../../skellytracker/AGENTS.md#layout)
   ([ADR-1GGP](1GGP-ep-api-gives-an-application-each-ep-fact.md)). Not built here:
   - progress and cancel for an install from the Windows ML catalog;
   - a remove call and a command of `skellytracker-eps` for a catalog package that this package
     installed. The freemocap remove button uses the same call. It never removes a package that was
     on the PC before. Today only the certify suite calls `remove_installed()`
     ([ADR-XSE7](XSE7-amd-eps-in-the-field-test.md) item 8);
   - flags of `PackStatus` for not certified, passed on this PC and failed on this PC
     ([ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) items 2 and 3).

GPU JPEG decode is for NVIDIA only: item 7 of
[ADR-BZ7X](BZ7X-onnx-runtime-telemetry-switch-and-scan.md) states it.

## Reason

- Two readers of one host fact can give two values. One home gives one value to each application.
- `ort_core` of the EP catalog must equal the `onnxruntime` pin
  ([ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime)). A second declaration in freemocap
  can resolve a different build.
- A pin to a commit is the only exact pin before the version scheme exists.

## Consequences

- The `_pyinstaller/` row of the layout table names only the data-only hook. Change it when the
  hook of ONNX Runtime is built.

## Open work

See [open-work.md](../open-work.md).
