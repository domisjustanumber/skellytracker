"""The record rules of `core.system` and `core.metrics`, and the sanitizer."""

import dataclasses
import json
import pickle

import pytest

from skellytracker.core._hardware import sanitize
from skellytracker.core.metrics import records as metrics_records
from skellytracker.core.system import records as system_records


def record_classes(module) -> list[type]:
    return [c for c in vars(module).values() if dataclasses.is_dataclass(c) and c.__module__ == module.__name__]


def example(cls: type):
    """An instance with a value for each required field and a record for each section field."""
    values = {}
    for field in dataclasses.fields(cls):
        if field.default is dataclasses.MISSING:
            values[field.name] = example(field.type) if dataclasses.is_dataclass(field.type) else {"int": 1}.get(getattr(field.type, "__name__", ""), "nvidia")
    return cls(**values)


ALL = record_classes(system_records) + record_classes(metrics_records)


@pytest.mark.parametrize("cls", ALL, ids=lambda c: c.__name__)
def test_record_form(cls):
    assert cls.__dataclass_params__.frozen
    record = example(cls)
    assert pickle.loads(pickle.dumps(record)) == record  # noqa: S301
    hash(record)
    json.dumps(dataclasses.asdict(record))
    fields = dataclasses.fields(cls)
    assert not any("dict" in str(f.type) for f in fields)
    assert "hostname" not in {f.name for f in fields}
    if "nvidia" in {f.name for f in fields}:
        assert fields[-1].name == "nvidia" and fields[-1].default is None
    for field in fields:
        if "utilization" in field.name:
            assert field.name.endswith("utilization") and "float" in str(field.type)
        if field.name.endswith("_bytes") or field.name.endswith("_ns"):
            assert "int" in str(field.type) and "float" not in str(field.type)


def test_sanitize_text_windows_and_posix():
    win = sanitize.sanitize_text(
        r"no file D:\people\ann\app\.venv\Lib\x.dll and d:/people/ann/data",
        prefix=r"D:\people\ann\app\.venv", home=r"D:\people\ann",
    )
    assert win == r"no file <prefix>\Lib\x.dll and ~/data"
    posix = sanitize.sanitize_text("no /data/ann/app/.venv/lib/x.so in /data/ann/d", prefix="/data/ann/app/.venv", home="/data/ann")
    assert posix == "no <prefix>/lib/x.so in ~/d"


def test_reduce_token():
    assert sanitize.reduce_token(r"D:\people\ann\run.py") == "run.py"
    assert sanitize.reduce_token("/data/ann/run.py") == "run.py"
    assert sanitize.reduce_token("file:///data/ann/pkg-1.0.whl") == "pkg-1.0.whl"
    assert sanitize.reduce_token("--out=/data/ann/out.json") == "--out=out.json"
    assert sanitize.reduce_token("-m") == "-m" and sanitize.reduce_token("status") == "status"
