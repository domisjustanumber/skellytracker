"""The CLI commands `run`, `validate` and `nodes` of `python -m skellytracker`, and the webcam demo of a pipeline.

    python -m skellytracker run --pipeline <key or file> --coco <annotations.json> --images <dir> --out <dir or file.jsonl>
                                [--ep <key>] [--ep-option <name>=<value> ...] [--device <key> ...]
                                [--timing on|off] [--taps <dir>] [--user-root <dir>]
    python -m skellytracker validate <key or file> [--user-root <dir>]
    python -m skellytracker nodes [--json]
    python -m skellytracker --pipeline <key or file> [--camera <index>] [--rotate <degrees>]
                            [--ep <key>] [--ep-option <name>=<value> ...] [--device <key> ...]

`run` is the COCO input form (pipeline.timing, Behaviour item 6): one camera with the id 0, the
running mode `image`, and the images in ascending `image_id` order. `--out` gets the timing file: a
path that ends in `.jsonl` is the file, and each other path is a folder that gets `timing.jsonl`.
`run` writes no other file there. `--taps` gives the tap folder.

With no `--ep`, `run` and the demo use `eps.recommend("performance")` and print the chosen EP and
its options. They do this only when the run must give an EP (`V-pipeline.running-8`).

Exit codes, the table of `core/errors.py`: 0 ok; 1 failure, also an extra or an ONNX file that is
absent; 2 a usage error, a pipeline that is not valid, a key that the catalog does not have, or an
EP key or an EP option that the EP catalog refuses; 3 an EP is not available; 4 a session was not
created; 5 the GPU memory is exhausted; 6 cancelled. Each error prints one line on stderr.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from skellytracker.core import eps, errors
from skellytracker.core.pipelines._runtime.resolve import ResolvedPipeline, resolve
from skellytracker.core.pipelines.annotate import annotate
from skellytracker.core.pipelines.loading import check_pipeline, load_pipeline
from skellytracker.core.pipelines.nodes import list_node_types
from skellytracker.core.pipelines.run import Frame, _start, start_pipeline

COMMANDS = ("run", "validate", "nodes")
TIMING_FILE = "timing.jsonl"  # choice: no text gives the name of the timing file
WINDOW_TITLE = "skellytracker pipeline demo"
_QUIT_KEYS = (ord("q"), 27)
_ROTATIONS = {90: 0, 180: 1, 270: 2}  # degrees clockwise -> the cv2 rotate code


def parse_ep_options(items: Sequence[str] | None) -> dict[str, str]:
    """Return the mapping of the `--ep-option <name>=<value>` items. Raise `EpRequestError` for an item with no name or no `=`."""
    options: dict[str, str] = {}
    for item in items or ():
        name, found, value = item.partition("=")
        if not found or not name:
            raise errors.EpRequestError(f"--ep-option must be <name>=<value>, not {item!r}")
        options[name] = value
    return options


def run_ep(resolved: ResolvedPipeline, execution_provider: str | None, ep_options: Mapping[str, str]) -> tuple[str | None, dict[str, str]]:
    """Return the EP key and the EP options of a run. With no key, a pipeline that needs an EP gets the recommended EP (ADR-ZYS9 item 8)."""
    options = dict(ep_options)
    if execution_provider is None and resolved.needs_execution_provider:
        recommended = eps.recommend("performance")
        execution_provider = recommended.chosen.ep_key
        options = {**dict(recommended.options), **options}
        print(f"Execution provider: {execution_provider} (recommended for performance), options: {options}", flush=True)
    return execution_provider, options


def read_coco_images(annotations: Path, image_dir: Path) -> list[tuple[int, Path]]:
    """Return `(image_id, path)` of each image of a COCO annotations file, in ascending `image_id` order."""
    try:
        records = json.loads(annotations.read_text(encoding="utf-8"))["images"]
        found = sorted((int(record["id"]), image_dir / record["file_name"]) for record in records)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"cannot read the images of the COCO file {annotations.name}: {type(exc).__name__}: {exc}") from exc
    ids = [image_id for image_id, _ in found]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError(f"the COCO file {annotations.name} must give one or more images with unique ids")
    return found


def cmd_run(options: argparse.Namespace) -> int:
    import cv2

    resolved = resolve(load_pipeline(options.pipeline, user_root=options.user_root), options.user_root)
    images = read_coco_images(Path(options.coco), Path(options.images))
    execution_provider, ep_options = run_ep(resolved, options.ep, parse_ep_options(options.ep_option))
    sink = None
    if options.timing == "on":
        out = Path(options.out)
        sink = out if out.suffix.lower() == ".jsonl" else out / TIMING_FILE
        sink.parent.mkdir(parents=True, exist_ok=True)
    run = _start(
        resolved, image_ids=[image_id for image_id, _ in images], camera_ids=[0], running_mode="image",
        execution_provider=execution_provider, ep_options=ep_options, device=options.device, timing_sink=sink, timing=options.timing,
        tap_dir=options.taps,
    )
    with run:
        for frame_index, (_, path) in enumerate(images):
            image = cv2.imread(str(path))
            if image is None:
                raise ValueError(f"cannot read the image {path.name}")
            run.process(Frame(image, frame_index))
    return errors.EXIT_OK


def cmd_validate(options: argparse.Namespace) -> int:
    config = load_pipeline(options.source, user_root=options.user_root)
    for warning in check_pipeline(config, user_root=options.user_root).warnings:
        print(f"warning: {warning.code}: {warning.message}")
    print(f"{config.pipeline_id}@{config.source.name}: valid")
    return errors.EXIT_OK


def cmd_nodes(options: argparse.Namespace) -> int:
    nodes = list_node_types()
    if options.json:
        print(json.dumps([dataclasses.asdict(node) for node in nodes], indent=2))
        return errors.EXIT_OK
    for node in nodes:
        inputs = ", ".join(f"{port.name}: {port.port_type}" + ("" if port.required else " (optional)") for port in node.inputs)
        outputs = ", ".join(f"{port.name}: {port.port_type}" for port in node.outputs)
        print(f"{node.type}  ({inputs}) -> ({outputs})  spans: {', '.join(node.timing_spans)}")
        for param in node.params:
            default = "required" if param.required else f"default {json.dumps(param.default)}"
            print(f"  param {param.name}: {param.type}, {default}" + (", set during run" if param.set_during_run else ""))
    return errors.EXIT_OK


def add_ep_arguments(parser: argparse.ArgumentParser) -> None:
    """Add `--ep`, `--ep-option` and `--device`: the same flags for `run` and for the demo."""
    parser.add_argument("--ep", default=None, help="a key of the EP catalog, for example cpu (default: the recommended EP, when the pipeline needs one)")
    parser.add_argument("--ep-option", action="append", metavar="NAME=VALUE", help="one EP option; repeatable")
    parser.add_argument("--device", action="append", metavar="KEY", help="one GPU key; repeatable (default: each GPU that the EP can use)")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="skellytracker")
    commands = root.add_subparsers(dest="command", required=True)
    user_root = {"default": None, "help": "the user root (default: SKELLYTRACKER_USER_ROOT, else the user data folder)"}
    run = commands.add_parser("run", help="run a pipeline on the images of a COCO file and write the timing file")
    run.add_argument("--pipeline", required=True, help="<pipeline_id>@<source.name>, with an optional pin ==<version>, or a pipeline file")
    run.add_argument("--coco", required=True, help="the COCO annotations file")
    run.add_argument("--images", required=True, help="the image folder")
    run.add_argument("--out", required=True, help=f"the timing file (.jsonl), or a folder that gets {TIMING_FILE}")
    add_ep_arguments(run)
    run.add_argument("--timing", choices=["on", "off"], default="on")
    run.add_argument("--taps", default=None, metavar="DIR", help="the tap folder")
    run.add_argument("--user-root", **user_root)
    run.set_defaults(run=cmd_run)
    validate = commands.add_parser("validate", help="run the load checks of a pipeline and print the warnings")
    validate.add_argument("source", help="a pipeline file, or a key of the pipeline catalog")
    validate.add_argument("--user-root", **user_root)
    validate.set_defaults(run=cmd_validate)
    nodes = commands.add_parser("nodes", help="list the node types")
    nodes.add_argument("--json", action="store_true", help="print JSON")
    nodes.set_defaults(run=cmd_nodes)
    return root


def _guarded(call: Any) -> int:
    """Run `call` and return the exit code. Print one line on stderr for an error."""
    try:
        return call()
    except SystemExit as stop:  # argparse: a usage error is 2, --help is 0
        return stop.code if isinstance(stop.code, int) else errors.EXIT_USAGE
    except KeyboardInterrupt:
        return errors.EXIT_CANCELLED
    except Exception as error:  # noqa: BLE001 - the exit-code table maps each error class
        text = error.args[0] if isinstance(error, KeyError) and error.args else error
        print(f"{type(error).__name__}: {' '.join(str(text).split())}", file=sys.stderr)
        # A config, a parameter or a key that is not valid is a usage error. No such error class has its own code.
        usage = isinstance(error, (ValueError, LookupError)) and not hasattr(error, "exit_code")
        return errors.EXIT_USAGE if usage else errors.exit_code_of(error)


def main(arguments: list[str]) -> int:
    """Run `run`, `validate` or `nodes`. Return the exit code."""

    def call() -> int:
        options = parser().parse_args(arguments)
        return options.run(options)

    return _guarded(call)


def run_demo(
    pipeline: str | Path, *, camera: int = 0, rotation: int = 0, execution_provider: str | None = None,
    ep_options: Mapping[str, str] | None = None, device: Sequence[str] | None = None,
) -> None:
    """Run a pipeline on a webcam in the running mode `live` and show each output, until the key q or Esc.

    `frame_index` is the count of the frames that the camera gave. `timestamp_ms` is the time of a
    monotonic clock in milliseconds. The function closes the run and the camera at the end, also
    after an error.
    """
    import cv2

    config = load_pipeline(pipeline)
    execution_provider, options = run_ep(resolve(config), execution_provider, ep_options or {})
    run, capture = None, None
    try:
        run = start_pipeline(config, camera_ids=[camera], running_mode="live", execution_provider=execution_provider, ep_options=options, device=device)
        capture = cv2.VideoCapture(camera)
        if not capture.isOpened():
            raise RuntimeError(f"Could not open camera at index {camera}.")
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        frame_index = 0
        while True:
            # shortcut: a failed read ends the demo, and a slow pipeline shows old frames; add a capture thread if that hurts
            ok, image = capture.read()
            if not ok or image is None:
                break
            if rotation in _ROTATIONS:
                image = cv2.rotate(image, _ROTATIONS[rotation])
            result = run.process(Frame(image, frame_index, time.perf_counter_ns() / 1e6))
            frame_index += 1
            cv2.imshow(WINDOW_TITLE, annotate(image, result, run.output_schema))
            if cv2.waitKey(1) & 0xFF in _QUIT_KEYS:
                break
    finally:
        if run is not None:
            run.close()
        if capture is not None:
            capture.release()
        cv2.destroyAllWindows()


def demo_main(pipeline: str, *, camera: int, rotation: int, ep: str | None, ep_option: Sequence[str] | None, device: Sequence[str] | None) -> int:
    """Run the webcam demo of a pipeline from the demo CLI. Return the exit code."""

    def call() -> int:
        run_demo(pipeline, camera=camera, rotation=rotation, execution_provider=ep, ep_options=parse_ep_options(ep_option), device=device)
        return errors.EXIT_OK

    return _guarded(call)
