"""The node catalog: the fixed facts of each node type (ADR-V7GZ item 9).

    list_node_types()   # one `NodeTypeInfo` for each class of `config.NODE_TYPES`

The texts of a param are the texts of the node tables of the pipeline spec
(`specs/pipeline/nodes/<type>.md`). A doc test compares them with the committed tables.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_core import to_jsonable_python

from skellytracker.core.pipelines.config import NODE_TYPES, VARIADIC

# The constraint attributes of the metadata of a field, and their text in the column "Range".
_BOUNDS = (
    ("ge", ">="),
    ("gt", ">"),
    ("le", "<="),
    ("lt", "<"),
    ("min_length", "length >="),
    ("max_length", "length <="),
    ("multiple_of", "multiple of"),
)


@dataclass(frozen=True)
class NodePort:
    """One port of a node type. The input `*` is the list of a variadic node. `required` is false for an output.

    `port_types` are the port types that an input accepts, or that an output can give. An output
    with two or more port types takes the type of the inputs that `any_from` of its node type names.
    """

    name: str
    direction: str
    port_types: tuple[str, ...]
    required: bool


@dataclass(frozen=True)
class NodeParam:
    """One param of a node type.

    `type` and `range` are the texts of the columns "Type" and "Range" of the node table.
    `default` is the default as plain JSON data. It is None for a required param: read `required`.
    """

    name: str
    type: str
    range: str
    default: Any
    required: bool
    set_during_run: bool
    description: str
    source: str


@dataclass(frozen=True)
class NodeTypeInfo:
    """One node type: its section ID, its ports (the inputs, then the outputs), its timing spans and its params.

    `any_from` names the inputs that give an output with two or more port types its type
    (pipeline.graph, Behaviour item 4). `params_schema` is the JSON Schema of the params model of the node type. An editor makes
    its param fields from it (ADR-4WR9).
    """

    type: str
    section: str
    inputs: tuple[NodePort, ...]
    outputs: tuple[NodePort, ...]
    any_from: tuple[str, ...]
    timing_spans: tuple[str, ...]
    params: tuple[NodeParam, ...]
    params_schema: dict[str, Any]


def _type_text(annotation: Any, module: str) -> str:
    """Return the Python text of a type, without the prefixes `typing.` and `<module>.`."""
    if isinstance(annotation, type) and not getattr(annotation, "__args__", None):
        return annotation.__name__
    return str(annotation).replace("typing.", "").replace(f"{module}.", "")


def _param(name: str, field: Any, module: str) -> NodeParam:
    extra = field.json_schema_extra if isinstance(field.json_schema_extra, dict) else {}
    bounds = [
        f"{text} {getattr(item, attr)}" for item in field.metadata for attr, text in _BOUNDS if getattr(item, attr, None) is not None
    ]
    required = field.is_required()
    return NodeParam(
        name=name,
        type=_type_text(field.annotation, module),
        range=", ".join(bounds),
        default=None if required else to_jsonable_python(field.get_default(call_default_factory=True)),
        required=required,
        set_during_run=bool(extra.get("set_during_run")),
        description=field.description or "",
        source=str(extra.get("source", "")),
    )


def list_node_types() -> list[NodeTypeInfo]:
    """Return the facts of each node type, in the order of the pipeline spec."""
    return [
        NodeTypeInfo(
            type=node.type,
            section=node.section,
            inputs=tuple(
                NodePort(name, "input", kind, name == VARIADIC or name in node.required_inputs) for name, kind in node.inputs.items()
            ),
            outputs=tuple(NodePort(name, "output", kind, False) for name, kind in node.outputs.items()),
            any_from=tuple(node.any_from),
            timing_spans=tuple(node.timing_spans),
            params=tuple(_param(name, field, node.__module__) for name, field in node.Params.model_fields.items()),
            params_schema=node.Params.model_json_schema(),
        )
        for node in NODE_TYPES
    ]


__all__ = ["NodeParam", "NodePort", "NodeTypeInfo", "list_node_types"]
