# 4WR9 — The node catalog gives the JSON Schema of the params and the `any_from` inputs of each node type

**Status:** absorbed into [`core/pipelines/nodes.py`](../../skellytracker/core/pipelines/nodes.py), [`core/pipelines/cli.py`](../../skellytracker/core/pipelines/cli.py), 2026-11-23 (absorb pass of 2026-11-23; PR: pending). It was `accepted` from 2026-11-16 (user, question Q14 of the pipeline editor plan of freemocap).

## Decision

1. `NodeTypeInfo` of `list_node_types()` has the field `params_schema`. Its value is
   `Params.model_json_schema()` of the node type: the Pydantic JSON Schema of the params model.
2. `python -m skellytracker nodes --json` gives the field, because it writes each `NodeTypeInfo`
   with `dataclasses.asdict`. The text output does not change.
3. `NodeTypeInfo` has the field `any_from`: the input names of `NodeType.any_from`. These inputs
   give an `any` output its port type
   ([Graph](../../specs/pipeline/graph.md#behaviour) item 4).
4. The fields `params` and `params_schema` give the same params in the same order. `params` keeps
   the texts of the node tables. `params_schema` gives the types, the enums, the bounds and the
   defaults as data.

## Reason

The freemocap pipeline editor makes its param fields from the node catalog. It must not define the
node types again ([freemocap `AGENTS.md`](https://github.com/freemocap/freemocap): Tracker owns the
schemas). The field `type` of `NodeParam` is Python text, for example
`Literal['ema', 'one_euro']`. A TS editor cannot read it safely. The package JSON Schema of a
pipeline file has the params, but it has no port types and no port names. Without `any_from`, an
editor cannot find the port type of the output of a `gate` or a `first_of` node. A second request for the
schema would make the editor join two documents by the node type.

## Consequences

- The JSON output of `nodes` is larger. It is a catalog view, not a hot path.
- A change of a params model changes `params_schema` with no other edit.

## Evidence

- `skellytracker/core/pipelines/nodes.py`, `list_node_types`.
- `skellytracker/tests/pipelines/test_cli.py`,
  `test_nodes_lists_the_11_node_types_as_text_and_as_json`: the property names of each
  `params_schema` are the names of `params`, in the same order, the `smooth_roi` enum of
  `filter` is `["ema", "one_euro"]`, and only `gate` and `first_of` have `any_from`.

## Alternatives rejected

- freemocap calls `model_json_schema()` on the node classes. Then freemocap reads node internals of
  Tracker, not a public interface.
- The editor parses the text of `NodeParam.type`. The text is for people, and it can change.
- The editor reads `pipeline.schema.json` beside `list_node_types()`. It needs two documents and a
  join for one view.
