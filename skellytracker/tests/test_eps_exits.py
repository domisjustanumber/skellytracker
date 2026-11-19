"""The unclean exits of a process that held a session on a GPU EP (ADR-ER5X item 5)."""

import subprocess
import sys
import textwrap

import pytest

from skellytracker.core import eps
from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps import evidence, exits, gate, store
from skellytracker.tests.hw_fakes import fake_pack, gpu

RTX = gpu()


@pytest.fixture(autouse=True)
def ep_store(tmp_path, monkeypatch):
    monkeypatch.setenv(store.STORE_VARIABLE, str(tmp_path / "eps"))
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "win_amd64")
    monkeypatch.setattr(evidence, "load_evidence", lambda: ())
    for name, value in {"_handle": None, "_path": None, "_pairs": set(), "_exit_requested": False}.items():
        monkeypatch.setattr(exits, name, value)
    monkeypatch.setattr(exits.atexit, "register", lambda function: None)  # the test ends the "process" itself
    fake_pack("cuda")
    yield tmp_path / "eps"
    if exits._handle is not None:
        exits._handle.close()


def dead_process(*pairs: str) -> None:
    """Leave the marker of a process that is gone: a marker file with no lock."""
    folder = exits._sessions_dir()
    folder.mkdir(parents=True, exist_ok=True)
    name = f"999-{len(list(folder.glob('*.marker')))}"
    (folder / f"{name}.marker").write_bytes(b" ")
    store.write_json(folder / f"{name}.json", {"pairs": list(pairs)})


def test_two_unclean_exits_in_a_row_mark_the_ep_as_failed_and_a_clean_exit_resets_the_count():
    catalog = eps.load_catalog()
    pair = gate.pair_key(catalog, "cuda", RTX, "Windows")
    checks = store.store_root() / "quick-checks.json"
    store.write_json(checks, {pair: {"result": "passed"}})
    dead_process(pair)
    assert exits.collect() == [] and gate.local_result(catalog, "cuda", RTX, "Windows") == "passed"  # one is a record only
    assert store.read_json(exits._counts_path()) == {pair: 1} and not list(exits._sessions_dir().glob("*"))
    exits.note_session(catalog, "cuda", RTX, "Windows")  # this process opens a session and ends cleanly
    assert len(list(exits._sessions_dir().glob("*.marker"))) == 1
    exits._clean_exit()
    assert store.read_json(exits._counts_path()) == {} and not list(exits._sessions_dir().glob("*"))
    dead_process(pair)
    assert exits.collect() == []  # the count started again at 1
    dead_process(pair)
    assert exits.collect() == [pair]
    row = store.read_json(checks)[pair]
    assert (row["result"], row["cause"], row["unclean_exits"]) == ("failed", "unclean-exits", 2)
    assert gate.check_reason(catalog, "cuda", RTX, "Windows") == gate.FAILED_CHECK
    assert gate.local_cause(catalog, "cuda", RTX, "Windows") == "unclean-exits"
    with store.store_lock():  # a quick check that passed: the caller writes the row and removes the count
        store.write_json(checks, {pair: {"result": "passed"}})
        exits.forget(pair)
    assert store.read_json(exits._counts_path()) == {} and gate.check_reason(catalog, "cuda", RTX, "Windows") is None


def test_a_live_process_the_exit_notice_and_the_certification_code_give_no_unclean_exit():
    catalog = eps.load_catalog()
    pair = gate.pair_key(catalog, "cuda", RTX, "Windows")
    with gate.certification_run():
        exits.note_session(catalog, "cuda", RTX, "Windows")
    assert exits._handle is None and not exits._sessions_dir().exists()  # the certification code writes no marker
    exits.note_session(catalog, "cuda", RTX, "Windows")
    exits.note_session(catalog, "cuda", RTX, "Windows")
    (marker,) = exits._sessions_dir().glob("*.marker")
    assert store.read_json(marker.with_suffix(".json")) == {"pairs": [pair]}
    code = textwrap.dedent("""
        import sys
        from skellytracker.core.eps import exits
        print(exits.collect(), len(list(exits._sessions_dir().glob("*.marker"))))
    """)
    other = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, timeout=120, check=True)  # noqa: S603
    assert other.stdout.split() == ["[]", "1"]  # an other process sees the lock: the marker stays, and nothing counts
    assert store.read_json(exits._counts_path()) is None
    exits.note_exit_requested()
    assert not list(exits._sessions_dir().glob("*")) and exits._handle is None
    exits.note_session(catalog, "cuda", RTX, "Windows")  # after the notice, the process writes no marker
    assert not list(exits._sessions_dir().glob("*"))


def test_a_killed_process_leaves_a_marker_that_the_next_process_counts(tmp_path):
    code = textwrap.dedent("""
        import os
        from skellytracker.core import eps
        from skellytracker.core.eps import catalog as catalog_module, exits
        from skellytracker.tests.hw_fakes import gpu
        catalog_module.platform_tag = lambda: "win_amd64"
        exits.note_session(eps.load_catalog(), "cuda", gpu(), "Windows")
        os._exit(7)  # no clean exit of the interpreter
    """)
    for expected in ([], None):
        done = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, timeout=120, check=False)  # noqa: S603
        assert done.returncode == 7, done.stderr
        if expected is not None:
            assert exits.collect() == expected
    catalog = eps.load_catalog()
    assert exits.collect() == [gate.pair_key(catalog, "cuda", RTX, "Windows")]  # the second in a row
