"""Write the JSON Schema and the node tables of the pipeline spec from its reference model.

The Pydantic reference model is `specs/pipeline/reference/pipeline_config.py` (ADR-3SF2 item 3).
The tool loads it by its path, with `make_vectors.load_reference`. The model must export:

- `PipelineConfig`, a Pydantic model. `PipelineConfig.model_json_schema()` is the schema.
- `NODE_TYPES`, a tuple of classes. Each class has the class attributes `type` (for example
  `roi_from_points`), `section` (`node.<type>`), `Params` (a Pydantic model), `inputs` and
  `outputs` (port name -> port type).

Each field of `Params` has a `description`, and a `json_schema_extra` with `live` (a bool) and
`source` (a string). A field with no default is required.

The tool writes these files:

- `specs/pipeline/pipeline.schema.json`: `json.dumps(schema, indent=2, sort_keys=True)` and a
  line feed, with LF line ends.
- For each class of `NODE_TYPES`, two tables in `specs/pipeline/nodes/<type>.md`. The params table
  replaces the text between `<!-- node-table:params -->` and `<!-- /node-table:params -->`. Its
  columns are Param, Type, Range, Default, Live, Description and Source. A required param shows
  `required` as its default. The ports table replaces the text between `<!-- node-table:ports -->`
  and `<!-- /node-table:ports -->`. Its columns are Port, Direction and Type. The inputs come
  first, then the outputs.

A node file that does not exist, or that does not have the two marker pairs, is an error that
names the file. The tool then writes nothing. With `--check`, the tool writes nothing and exits 1
when a file is not current, and names each such file. When the reference model does not exist,
the tool prints one line and exits 0, because the draft spec is not written yet.

Usage:
    python tools/make_pipeline_schema.py            # write the files
    python tools/make_pipeline_schema.py --check    # exit 1 when a file is not current
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from pydantic_core import to_jsonable_python

import make_vectors

REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = REPO_ROOT / "specs" / "pipeline"
MODEL = PIPELINE_DIR / "reference" / "pipeline_config.py"
# The constraint attributes of the `annotated_types` metadata of a field, and their text.
BOUNDS = (
    ("ge", ">="),
    ("gt", ">"),
    ("le", "<="),
    ("lt", "<"),
    ("min_length", "length >="),
    ("max_length", "length <="),
    ("multiple_of", "multiple of"),
)


def load_model(path: Path = MODEL) -> ModuleType:
    """Load the reference model by its path. Its module name is its stem, in `sys.modules`."""
    return make_vectors.load_reference(path.stem, path.parent)


def schema_text(model: ModuleType) -> str:
    """Return the text of the JSON Schema of `model.PipelineConfig`."""
    return json.dumps(model.PipelineConfig.model_json_schema(), indent=2, sort_keys=True) + "\n"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _type_text(annotation: Any, module: str) -> str:
    """Return the Python text of a type, without the prefixes `typing.` and `<module>.`."""
    if isinstance(annotation, type) and not getattr(annotation, "__args__", None):
        return annotation.__name__
    return str(annotation).replace("typing.", "").replace(f"{module}.", "")


def params_table(node: type) -> str:
    """Return the params table of a node class."""
    fields = node.Params.model_fields
    if not fields:
        return "This node has no parameters."
    lines = [
        "| Param | Type | Range | Default | Live | Description | Source |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, field in fields.items():
        extra = field.json_schema_extra if isinstance(field.json_schema_extra, dict) else {}
        bounds = [
            f"{text} {getattr(item, attr)}"
            for item in field.metadata
            for attr, text in BOUNDS
            if getattr(item, attr, None) is not None
        ]
        if field.is_required():
            default = "required"
        else:
            value = to_jsonable_python(field.get_default(call_default_factory=True))
            default = f"`{json.dumps(value)}`"
        live = {True: "yes", False: "no"}.get(extra.get("live"), "")
        cells = [
            f"`{name}`",
            f"`{_type_text(field.annotation, node.__module__)}`",
            ", ".join(bounds),
            default,
            live,
            field.description or "",
            str(extra.get("source", "")),
        ]
        lines.append("| " + " | ".join(_cell(cell) for cell in cells) + " |")
    return "\n".join(lines)


def ports_table(node: type) -> str:
    """Return the ports table of a node class: the inputs, then the outputs."""
    lines = ["| Port | Direction | Type |", "|---|---|---|"]
    for direction, ports in (("input", node.inputs), ("output", node.outputs)):
        lines += [f"| `{port}` | {direction} | `{kind}` |" for port, kind in ports.items()]
    return "\n".join(lines)


def replace_tables(text: str, node: type, where: str) -> str:
    """Return `text` with the params table and the ports table of `node` between their markers.

    Raise `ValueError` that names `where` when a marker pair is missing.
    """
    for name, table in {"params": params_table(node), "ports": ports_table(node)}.items():
        start, end = f"<!-- node-table:{name} -->", f"<!-- /node-table:{name} -->"
        pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.DOTALL)
        found = pattern.findall(text)
        if len(found) != 1:
            raise ValueError(f"{where}: needs one pair of the markers {start} and {end}")
        new = f"{start}\n{table}\n{end}"
        text = text.replace(found[0], new)
    return text


def expected(model: ModuleType, base: Path = PIPELINE_DIR) -> dict[Path, str]:
    """Return the expected text of the schema file and of each node file.

    Raise `ValueError` that names a node file that does not exist or that has no markers.
    """
    texts = {base / "pipeline.schema.json": schema_text(model)}
    for node in model.NODE_TYPES:
        path = base / "nodes" / f"{node.type}.md"
        where = path.relative_to(base).as_posix()
        if not path.is_file():
            raise ValueError(f"{where}: the node file of the node type {node.type} does not exist")
        texts[path] = replace_tables(path.read_text(encoding="utf-8"), node, where)
    return texts


def run(model_path: Path = MODEL, base: Path = PIPELINE_DIR, check: bool = False) -> int:
    """Write or check the files. Return the exit status."""
    if not model_path.is_file():
        print(f"{model_path.name} does not exist yet: nothing to make")
        return 0
    try:
        texts = expected(load_model(model_path), base)
    except ValueError as error:
        print(error)
        return 1
    stale = [
        path
        for path, text in texts.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != text
    ]
    if check:
        names = [f"differs: {path.relative_to(base).as_posix()}" for path in stale]
        print("\n".join(names) or "the pipeline schema and the node tables are current")
        return 1 if stale else 0
    for path in stale:
        path.write_text(texts[path], encoding="utf-8", newline="\n")
    print(f"wrote {len(stale)} files")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when a file is not current")
    return run(check=parser.parse_args(argv[1:]).check)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
