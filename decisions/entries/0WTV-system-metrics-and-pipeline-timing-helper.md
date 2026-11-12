# 0WTV — `core/metrics/` holds only system metrics; the pipeline timing helper is `core/pipelines/timing.py`

**Status:** accepted, 2026-11-12 (user).

## Decision

1. `core/metrics/` holds only system-level live metrics: CPU load, GPU load, VRAM and process
   samples. It holds no pipeline metric.
2. The helper that aggregates the timing events to the skellybench timing record is the public
   module `core/pipelines/timing.py`. The CLI run with timing on calls it. A caller can also run it
   on a timing JSONL file. Its rule does not change: `stages_ms_per_image` is the sum of the model
   point times divided by the sum of `batch_size`. The model points are the points of each detector
   node and the `run` point of each `mediapipe_tasks` node. The `run` time of a glue node goes to
   `excluded_ms_per_image`.
3. This entry supersedes [ADR-Q59W](Q59W-pipeline-timing-and-taps.md). The other rules of Q59W stay.
   These headings state them: the [Fields](../../specs/pipeline/timing.md#fields),
   [Behaviour](../../specs/pipeline/timing.md#behaviour),
   [Implementer guidance](../../specs/pipeline/timing.md#implementer-guidance) and
   [Authoring guidance](../../specs/pipeline/timing.md#authoring-guidance) of Timing, and the
   [Fields](../../specs/pipeline/taps.md#fields) and
   [Behaviour](../../specs/pipeline/taps.md#behaviour) of Taps.
4. No heading of the spec states item 7 of Q59W, so this entry restates it. The pipeline spec of
   skellytracker owns the glue node definitions and their reference implementations. The skellybench
   templates are a separate concern of skellybench.

## Reason

- The user, in words: "core.metrics is just system-level stuff (gpu load, cpu load, etc). Any
  pipeline-specific metrics stay in the pipeline."
- The pipeline spec defines the timing events. One package then owns the event form and its
  aggregation.
- The user selected a public module. freemocap or a notebook can then aggregate a timing file
  without the CLI.

## Consequences

- The Implementer guidance of [Timing](../../specs/pipeline/timing.md#implementer-guidance) names
  `core/pipelines/timing.py` in place of `core/metrics/`.
- Stage P of [`specs/sidecar-implementation-plan.md`](../../specs/sidecar-implementation-plan.md)
  names `core/metrics/` for the helper. The next edit of that stage changes it to
  `core/pipelines/timing.py`.
- The hardware and EP track gives `core/metrics/`
  ([ADR-AQR4](AQR4-detectors-and-pipelines-entry-points.md) item 3). Its scope is item 1.

## Alternatives rejected

- **A helper in `core/metrics/`.** The user keeps that package for system metrics.
- **A private helper in `core/pipelines/_runtime/`.** Only the CLI could use it.
- **skellybench aggregates the raw events.** skellybench takes aggregates, not raw events
  ([ADR-Q59W](Q59W-pipeline-timing-and-taps.md), Reason).
