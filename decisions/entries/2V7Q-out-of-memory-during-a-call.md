# 2V7Q — An out-of-memory error during a call raises `VRAMExhaustionError` and closes the run

**Status:** absorbed into [`running.md#behaviour`](../../specs/pipeline/running.md#behaviour), [`session.py`](../../skellytracker/core/eps/session.py), [`run.py`](../../skellytracker/core/pipelines/run.py), 2026-11-16 (user, question K3 of 2026-11-16; PR: pending).

## Decision

1. An out-of-memory error of ONNX Runtime during a call of a session raises `VRAMExhaustionError`
   of `skellytracker/core/errors.py`. It is the class of an out-of-memory error at the build and
   at the warm-up run. The same text marks find the error.
2. The run does not do the call again. It does not change the batch.
3. The run is closed: each later call raises `RunClosedError`.
4. A generic detector of `create_detector` raises `VRAMExhaustionError` from a `detect` call. It
   has no run to close.
5. Each other error of a session passes through with no change.

This entry extends item 4 of [ADR-9NW0](9NW0-ep-keys-options-and-failures.md) to the calls. That
entry does not change.

## Reason

- An application then catches one error class for an out-of-memory error, at start and during a
  run. Before this entry, a call gave the raw error of ONNX Runtime.
- A retry at a smaller batch changes the batch of a run that is fixed at start
  ([Running](../../specs/pipeline/running.md#behaviour) item 4).
- After an out-of-memory error, the state of the sessions and of the nodes of the call is not
  known. A closed run is a state that the caller can act on.

## Consequences

- The caller starts a new run after the error, for example with fewer cameras or on an other EP.
- `report` of the error is None for a call: the function that runs the session has no
  `SessionReport`.
- The close writes `tap.json` of each `record` tap, as each `close()` does.

## Evidence

- `run_session` of `skellytracker/core/eps/session.py` maps the error. `run_batches` of
  `skellytracker/core/detectors/generic/inference.py` is the one place that runs a session for the
  generic detectors and for the `onnx_model` nodes. `PipelineRun._process` of
  `skellytracker/core/pipelines/run.py` closes the run.
- The tests are in `skellytracker/tests/test_eps_session.py`,
  `skellytracker/tests/detectors/test_generic_detectors.py` and
  `skellytracker/tests/pipelines/test_run.py`.

## Alternatives rejected

- **A retry at a smaller batch.** The batch is fixed at start, and a second failure is probable.
- **The run stays open.** The next call can fail again, and the node states are not known.
