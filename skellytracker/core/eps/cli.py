"""The CLI `skellytracker-eps`. `python -m skellytracker.core.eps` runs the same commands.

    skellytracker-eps status [--json | --format ini] [--out FILE]
    skellytracker-eps recommend [--form performance|accuracy] [--json]
    skellytracker-eps install [KEY ...] [--cuda] [--trt-rtx] [--recommended | --all-compatible | --cpu-only]
                              [--from-dir DIR] [--dry-run] [--yes] [--progress jsonl] [--cancel-file PATH]
    skellytracker-eps verify [KEY ... | --all] [--level L2|L3] [--force]
    skellytracker-eps remove PACK_ID | --all | --consumer KIND
    skellytracker-eps gc [--force] [--cache]
    skellytracker-eps download KEY ... --platform TAG --dest DIR
    skellytracker-eps selftest [--json] [--index-url URL]
    skellytracker-eps doctor [--full]

`status` and `recommend` import no `onnxruntime` and use no network. `status --json` has the schema
`skellytracker.eps.status/1`. `status --format ini` is UTF-16LE with a BOM, for an installer that has
no JSON parser. No environment variable selects the EP or the device.

Exit codes, the same as the pipeline CLI: 0 ok; 1 failure; 2 usage error, no confirmation, a
reserved or unknown EP key, or a refused option; 3 an EP is not available; 4 a session was not
created; 5 the GPU memory is exhausted; 6 cancelled. Each error prints one line on stderr.
"""

import argparse
import dataclasses
import json
import os
import sys
import threading
import urllib.request
from pathlib import Path

from skellytracker.core import errors
from skellytracker.core.eps import _download, installer, self_test, state, store, verification
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.recommendation import recommend
from skellytracker.core.eps.records import EpRecommendation, EpStatus, InstallPlan
from skellytracker.core.system.host import gpu_device_keys

STATUS_SCHEMA = "skellytracker.eps.status/1"
MB = 1024 * 1024


def megabytes(count: int) -> int:
    return -(-count // MB)


def recommendation_json(result: EpRecommendation) -> dict:
    return {
        "key": result.chosen.ep_key, "pack_id": result.chosen.pack_id, "device_key": result.chosen.device_key,
        "status": result.chosen.status, "options": dict(result.options), "precision": result.precision,
        "skipped": [{"key": c.ep_key, "status": c.status, "reason": c.reason} for c in result.skipped],
        "driver_update": any(offer.kind == "update-driver" for offer in result.offers),
        "offers": [dataclasses.asdict(offer) for offer in result.offers],
        "source": {"kind": result.source.kind, "catalog_revision": result.source.catalog_revision,
                   "row": result.source.row_id, "ranking_evidence": result.source.ranking_evidence},
    }


def recommendation_block(performance: EpRecommendation, accuracy: EpRecommendation) -> str:
    chosen = performance.chosen
    lines = [f"Performance EP: {chosen.ep_key} ({chosen.status})" + (f", pack {chosen.pack_id}" if chosen.pack_id else "")
             + (f", device {chosen.device_key}" if chosen.device_key else "") + f", precision {performance.precision}"
             + (f", options {dict(performance.options)}" if performance.options else ""),
             f"Accuracy EP: {accuracy.chosen.ep_key}, precision {accuracy.precision}"]
    lines += [f"  Skipped: {c.ep_key} ({c.status}): {c.reason}" for c in performance.skipped]
    lines += [f"  Offer: {offer.kind}" + (f" {offer.ep_key}" if offer.ep_key else "") + f": {offer.note}" for offer in performance.offers]
    source = performance.source
    lines.append(f"Source: hardware table, row {source.row_id}, catalog {source.catalog_revision[:12]}, "
                 f"ranking evidence: {source.ranking_evidence or 'none: order not measured'}")
    return "\n".join(lines)


def status_json(status: EpStatus) -> dict:
    host = status.host
    gpus = [{"rank": rank, "device_key": key, "vendor": gpu.vendor, "name": gpu.name, "vendor_id": gpu.pci_vendor_id,
             "device_id": gpu.pci_device_id, "driver": gpu.driver_version,
             "vram_mb": None if gpu.vram_total_bytes is None else gpu.vram_total_bytes // MB}
            for rank, (key, gpu) in enumerate(gpu_device_keys(host))]
    return {
        "schema": STATUS_SCHEMA,
        "core": {"ort_version": status.ort_version, "catalog_revision": status.catalog_revision, "core_matches_pin": status.core_matches_pin},
        "host": {"os": host.os_name, "os_build": host.os_build, "arch": host.arch, "platform_tag": status.platform_tag, "gpus": gpus,
                 "store_root": status.store_root, "store_free_bytes": status.store_free_bytes},
        "recommended": {"performance": recommendation_json(status.performance), "accuracy": recommendation_json(status.accuracy)},
        "eps": [dict(dataclasses.asdict(row), licences=[{"name": name, "url": url} for name, url in row.licences]) for row in status.eps],
        "warnings": list(status.warnings),
    }


def _ini(name: str, value) -> str:
    return f"{name}={' '.join(str(value).split())[:1023]}"


def status_ini(status: EpStatus) -> bytes:
    """The status as an INI file in UTF-16LE with a BOM: one line for each value, each value under 1024 characters."""
    performance = status.performance
    best = next(iter(performance.skipped), performance.chosen)  # the first candidate of the hardware class
    rows = {row.key: row for row in status.eps}
    best_row = rows.get(best.ep_key)
    values = [("schema", STATUS_SCHEMA), ("ok", 1), ("recommended", best.ep_key), ("recommended_pack", best.pack_id or ""),
              ("recommended_label", best_row.label if best_row else best.ep_key),
              ("recommended_download_mb", megabytes(best_row.download_bytes) if best_row else 0),
              ("recommended_source", best_row.source if best_row else "builtin"), ("catalog_revision", status.catalog_revision),
              ("recommended_row", performance.source.row_id), ("ranking_evidence", performance.source.ranking_evidence or "none"),
              ("driver_update", int(any(offer.kind == "update-driver" for offer in performance.offers))), ("count", len(status.eps))]
    lines = ["[status]", *(_ini(name, value) for name, value in values)]
    for number, row in enumerate(status.eps):
        fields = [("key", row.key), ("label", row.label), ("supported", int(row.state != "unsupported")),
                  ("builtin", int(row.state == "builtin")), ("recommended", int(row.key == best.ep_key)), ("state", row.state),
                  ("reason", row.reason or ""), ("download_mb", megabytes(row.download_bytes)), ("licence_count", len(row.licences))]
        for index, (name, url) in enumerate(row.licences):
            fields += [(f"licence.{index}.name", name), (f"licence.{index}.url", url)]
        lines += [f"[ep.{number}]", *(_ini(name, value) for name, value in fields)]
    return b"\xff\xfe" + ("\r\n".join(lines) + "\r\n").encode("utf-16-le")


def _write(data: bytes | str, out: str | None) -> None:
    if out:
        Path(out).write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    elif isinstance(data, bytes):
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    else:
        print(data)


def cmd_status(args) -> int:
    status = state.status()
    if args.format == "ini":
        _write(status_ini(status), args.out)
    elif args.json:
        _write(json.dumps(status_json(status), indent=1), args.out)
    else:
        lines = [recommendation_block(status.performance, status.accuracy), ""]
        lines += [f"{row.key}: {row.state}" + (f" ({row.reason})" if row.reason else "") for row in status.eps]
        lines += [f"Warning: {text}" for text in status.warnings]
        _write("\n".join(lines), args.out)
    return errors.EXIT_OK


def cmd_recommend(args) -> int:
    if args.json:
        print(json.dumps(recommendation_json(recommend(args.form)), indent=1))
    else:
        print(recommendation_block(recommend("performance"), recommend("accuracy")))
    return errors.EXIT_OK


def plan_text(plan: InstallPlan) -> str:
    lines = [f"Pack {pack.pack_id} {pack.version} for the EP {pack.ep_key}: download {megabytes(pack.download_bytes)} MB, "
             f"disk {megabytes(pack.disk_bytes)} MB. Licence: {pack.licence_name} {pack.licence_url}" for pack in plan.packs]
    lines += [f"Warning: {text}" for text in plan.warnings]
    lines.append(f"Total: download {megabytes(plan.download_bytes)} MB, disk {megabytes(plan.disk_bytes)} MB, to {store.store_root()}"
                 if plan.packs else "No pack to install.")
    return "\n".join(lines)


def cmd_install(args) -> int:
    keys = [*args.keys, *(["cuda"] if args.cuda else []), *(["trt-rtx"] if args.trt_rtx else [])]
    selection = "cpu-only" if args.cpu_only else "recommended" if args.recommended else keys or "all-compatible"
    plan = installer.plan_install(selection)
    jsonl = args.progress == "jsonl"
    if jsonl and not (args.yes or args.dry_run):
        print("--progress jsonl needs --yes.", file=sys.stderr)
        return errors.EXIT_USAGE
    text = sys.stderr if jsonl else sys.stdout
    print(recommendation_block(recommend("performance"), recommend("accuracy")), file=text)
    print(plan_text(plan), file=text)
    if jsonl:
        print(json.dumps({"event": "plan", "keys": [p.ep_key for p in plan.packs], "download_bytes": plan.download_bytes,
                          "disk_bytes": plan.disk_bytes, "warnings": list(plan.warnings)}), flush=True)
    if args.dry_run or not plan.packs:
        return errors.EXIT_OK
    if not args.yes:
        if not sys.stdin.isatty():
            print("The install needs a confirmation: use --yes.", file=sys.stderr)
            return errors.EXIT_USAGE
        if input(f"Download {megabytes(plan.download_bytes)} MB? [y/N] ").strip().lower() not in ("y", "yes"):  # noqa: S322
            return errors.EXIT_USAGE
    cancel = threading.Event()
    done = threading.Event()
    if args.cancel_file:
        def watch() -> None:
            while not done.wait(0.2):  # at least each 250 ms
                if os.path.exists(args.cancel_file):
                    cancel.set()

        threading.Thread(target=watch, daemon=True).start()

    def progress(event) -> None:
        if jsonl:
            fraction = event.bytes_done / event.bytes_total if event.bytes_total else None
            print(json.dumps({"event": "progress", "key": event.key, "phase": event.phase, "bytes_done": event.bytes_done,
                              "bytes_total": event.bytes_total, "fraction": fraction}), flush=True)

    try:
        result = installer.install(plan, progress=progress, cancel=cancel, from_dir=Path(args.from_dir) if args.from_dir else None)
    finally:
        done.set()
    outcomes = [(key, "ok", None, "") for key in result.ok] + [(key, "failed", code, message) for key, code, message in result.failed]
    outcomes += [(key, "cancelled", None, "") for key in result.cancelled]
    for key, outcome, code, message in outcomes:
        if jsonl:
            print(json.dumps({"event": "done", "key": key, "result": outcome, "error_code": code, "message": message}), flush=True)
        print(f"{key}: {outcome}" + (f" ({code}): {message}" if code else ""), file=text)
    if jsonl:
        print(json.dumps({"event": "summary", "ok": list(result.ok), "failed": [key for key, _, _ in result.failed],
                          "cancelled": list(result.cancelled), "needs_worker_restart": result.needs_worker_restart}), flush=True)
    return errors.EXIT_CANCELLED if result.cancelled else errors.EXIT_FAILURE if result.failed else errors.EXIT_OK


def cmd_verify(args) -> int:
    verdicts = verification.verify(args.keys or None, level=args.level, force=args.force)
    for verdict in verdicts:
        detail = "" if verdict.ok else f": {verdict.reason}"
        print(f"{verdict.ep_key}: {verdict.level} {'pass' if verdict.ok else 'fail'}{detail}")
    return errors.EXIT_OK if all(verdict.ok for verdict in verdicts) else errors.EXIT_FAILURE


def cmd_remove(args) -> int:
    if not (args.pack_id or args.all or args.consumer):
        print("remove needs a pack id, --all or --consumer KIND.", file=sys.stderr)
        return errors.EXIT_USAGE
    installer.remove("all" if args.all else args.pack_id, consumer=args.consumer)
    return errors.EXIT_OK


def cmd_gc(args) -> int:
    result = installer.gc(force=args.force, cache=args.cache)
    print(f"Removed packs: {', '.join(result.removed_packs) or 'none'}. Removed refs: {len(result.removed_refs)}. "
          f"Removed partial downloads: {result.removed_partials}. Deferred: {', '.join(result.deferred) or 'none'}.")
    return errors.EXIT_OK


def cmd_download(args) -> int:
    print(installer.download(args.keys, args.platform, Path(args.dest)))
    return errors.EXIT_OK


def cmd_selftest(args) -> int:
    result = self_test.selftest(args.index_url)
    if args.json:
        print(json.dumps(dataclasses.asdict(result), indent=1))
    else:
        for name, ok, detail in result.steps:
            print(f"{'pass' if ok else 'FAIL'}: {name}" + (f": {detail}" if detail else ""))
    return errors.EXIT_OK if result.ok else errors.EXIT_FAILURE


def cmd_doctor(args) -> int:
    catalog = load_catalog()
    kind, path = _download.trust_store_source()
    print(f"Trust store: {kind}" + (f" ({path})" if path else ""))
    print(f"Proxy: {urllib.request.getproxies() or 'none'}")
    print(f"EP store: {store.store_root()}")
    for text in state.status().warnings:
        print(f"Warning: {text}")
    ok = True
    for name, url in catalog.data["indexes"].items():
        page = url + catalog.pack("trt-rtx" if name == "pypi" else "cuda")["package"] + "/"
        try:
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_download.ssl_context()))
            with opener.open(page, timeout=20) as response:
                print(f"Index {name}: reachable (HTTP {response.status})")
        except OSError as error:
            ok = False
            print(f"Index {name}: not reachable: {error}")
    if args.full:
        for key in catalog.keys():
            pack = catalog.pack(key)
            manifest = None if pack is None else store.read_manifest(pack["id"], pack["version"])
            if manifest is not None:
                folder = store.pack_dir(pack["id"], pack["version"])
                bad = [name for name, _, sha in manifest["files"] if not (folder / name).is_file() or _download.sha256_of(folder / name) != sha]
                ok = ok and not bad
                print(f"Pack {pack['id']}: {len(manifest['files'])} files, {len(bad)} with a wrong sha256")
    return errors.EXIT_OK if ok else errors.EXIT_FAILURE


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="skellytracker-eps", description="Install, verify and select ONNX Runtime execution providers.")
    commands = root.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status", help="the EP state of this host; no network")
    status.add_argument("--json", action="store_true")
    status.add_argument("--format", choices=["ini"])
    status.add_argument("--out")
    status.set_defaults(run=cmd_status)
    recommended = commands.add_parser("recommend", help="the recommended EP of this host")
    recommended.add_argument("--form", choices=["performance", "accuracy"], default="performance")
    recommended.add_argument("--json", action="store_true")
    recommended.set_defaults(run=cmd_recommend)
    install = commands.add_parser("install", help="download and install EP packs")
    install.add_argument("keys", nargs="*", metavar="KEY")
    install.add_argument("--cuda", action="store_true")
    install.add_argument("--trt-rtx", action="store_true")
    selection = install.add_mutually_exclusive_group()
    selection.add_argument("--recommended", action="store_true")
    selection.add_argument("--all-compatible", action="store_true")
    selection.add_argument("--cpu-only", action="store_true")
    install.add_argument("--from-dir")
    install.add_argument("--dry-run", action="store_true")
    install.add_argument("--yes", action="store_true")
    install.add_argument("--progress", choices=["jsonl"])
    install.add_argument("--cancel-file")
    install.set_defaults(run=cmd_install)
    verify = commands.add_parser("verify", help="verify EPs in a child process")
    verify.add_argument("keys", nargs="*", metavar="KEY")
    verify.add_argument("--all", action="store_true")
    verify.add_argument("--level", choices=["L2", "L3"], default="L3")
    verify.add_argument("--force", action="store_true")
    verify.set_defaults(run=cmd_verify)
    remove = commands.add_parser("remove", help="remove packs or consumer refs from the store")
    remove.add_argument("pack_id", nargs="?")
    remove.add_argument("--all", action="store_true")
    remove.add_argument("--consumer", metavar="KIND")
    remove.set_defaults(run=cmd_remove)
    collect = commands.add_parser("gc", help="delete the packs that no consumer needs")
    collect.add_argument("--force", action="store_true")
    collect.add_argument("--cache", action="store_true")
    collect.set_defaults(run=cmd_gc)
    download = commands.add_parser("download", help="download the wheels of packs for an install from a folder")
    download.add_argument("keys", nargs="+", metavar="KEY")
    download.add_argument("--platform", required=True)
    download.add_argument("--dest", required=True)
    download.set_defaults(run=cmd_download)
    selftest = commands.add_parser("selftest", help="the EP pack test of CI")
    selftest.add_argument("--json", action="store_true")
    selftest.add_argument("--index-url")
    selftest.set_defaults(run=cmd_selftest)
    doctor = commands.add_parser("doctor", help="check the network, the trust store and the store files")
    doctor.add_argument("--full", action="store_true")
    doctor.set_defaults(run=cmd_doctor)
    return root


def main(argv: list[str] | None = None) -> int:
    """Run one command. It returns the exit code and prints one line on stderr for an error."""
    try:
        args = parser().parse_args(argv)
        return args.run(args)
    except SystemExit as stop:  # argparse: a usage error is 2, --help is 0
        return stop.code if isinstance(stop.code, int) else errors.EXIT_USAGE
    except KeyboardInterrupt:
        return errors.EXIT_CANCELLED
    except Exception as error:  # noqa: BLE001 - the exit-code table maps each error class
        print(f"{type(error).__name__}: {' '.join(str(error).split())}", file=sys.stderr)
        return errors.exit_code_of(error)
