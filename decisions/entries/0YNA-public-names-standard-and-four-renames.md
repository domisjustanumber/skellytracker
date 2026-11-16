# 0YNA — The standard for public names, and four renames

**Status:** absorbed into [`skellytracker/AGENTS.md#code-conventions`](../../skellytracker/AGENTS.md#code-conventions), [`skellytracker/AGENTS.md#layout`](../../skellytracker/AGENTS.md#layout), [`running.md#behaviour`](../../specs/pipeline/running.md#behaviour), [`pipelines/__init__.py`](../../skellytracker/core/pipelines/__init__.py), 2026-11-16 (user, question N1 of 2026-11-16; PR: pending).

## Decision

1. **The standard.** The public surface is the entry points `detectors`, `pipelines` and `eps`,
   with their records and their errors. Its names follow these rules:
   1. The case of PEP 8: `snake_case` for a function, a method and a field, `CapWords` for a class,
      `UPPER_CASE` for a constant.
   2. The name of each exception class ends in `Error`.
   3. An exception name is `<Subject><State>Error`. Its base is the built-in class that a caller
      catches: `KeyError` for not found, `ValueError` for a refused input, `RuntimeError` for a
      state.
   4. A module function is `verb_subject`. A bare verb is allowed only when the namespace names the
      object (`eps.install`) or the first argument is the object (`annotate(image, ...)`).
   5. One verb for one act in each entry point: `list_` (all entries), `get_` (one entry by key or
      pin; it raises `<Subject>NotFoundError`), `describe_` (the details of one entry), `load_`
      (parse into a config or a model), `check_` (run the rules and return the result), `create_`
      (make an object), `start_` (make an object that holds resources and has `close()`), `export_`
      and `to_` (write or convert).
   6. A catalog row is `<Subject>Entry`, with `key`, `version`, `available`, `unavailable_reason`
      and `superseded`.
   7. A function result in an entry point is `<Subject><Act-noun>` (`DetectorDescription`,
      `PipelineCheck`). In `eps`, where the act has no subject, it is `<Act>Result`.
   8. A boolean is an adjective or a participle with no prefix (`available`, `downloaded`). Use
      `is_<noun>` only when the bare word is a noun. Use `needs_<noun>` or `uses_<noun>` for a
      relation.
   9. A collection has a plural name, and one item has a singular name. An array with one value for
      each element keeps the name of the spec.
   10. One concept has one field name in each type (`point_names`).
   11. For an EP: a public parameter that takes the EP key is `execution_provider`. A compound name
       takes the prefix `ep_`. A CLI flag can be shorter (`--ep`).
   12. To rename a name that a spec or an entry fixes, write an entry and change the spec text in
       the same commit. Add no alias.
2. **The renames.** No old name has an alias, because 2.0.0 is not released.
   - `CallRefused` is now `CallRefusedError`.
   - `SetParamsRefused` is now `SetParamsRefusedError`.
   - `find_pipeline` is now `get_pipeline`.
   - `CanonicalKeypoints.names` is now `CanonicalKeypoints.point_names`.
3. **The names that stay.** `RunClosedError`, `Frame`, `PipelineRun.models`, `check_pipeline`,
   `needs_execution_provider`, `annotate` and `PipelineCheck` stay as they are.

This entry refines the name `SetParamsRefused` in item 3 of
[ADR-N5BM](N5BM-set-during-run-and-set-params.md). That entry does not change.

## Reason

- The pipeline API had names that no text fixed. Each had a comment that said so, and the plan
  asked the user to confirm them.
- A caller catches errors by the built-in base and by the `Error` suffix. Two errors had no suffix.
- `get_detector` gives one entry by key. `find_pipeline` did the same act with an other verb.
- A `keypoints` value has `point_names`. The canonical form of that value had `names` for the same
  concept.

## Consequences

- An application that used an old name must change it. freemocap uses the pipeline API.
- Row 13 of the pipeline changelog and the body of ADR-N5BM keep the old name `SetParamsRefused`.
- `uses_gpu` of `PackStatus` is a relation, as `needs_execution_provider` is. Rule 8 names the
  prefix `uses_` for it.

## Alternatives rejected

- **An alias for each old name.** No release has the old names.
- **`find_` for a pipeline.** It makes two verbs for one act.
