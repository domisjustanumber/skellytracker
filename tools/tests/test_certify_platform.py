"""Tests of the frame of `tools/certify_platform.py` and of its section 1, with fake sections and no GPU.

The private test strings are built from parts, so that `tools/check_private_data.py` does not see a real user path.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import certify_platform as cp
import pytest

PY = sys.executable


@pytest.fixture(autouse=True)
def no_windows_ml_catalog(monkeypatch):
    monkeypatch.setattr(cp, "windows_ml_offer", list)  # the consent text calls no hardware probe and no catalog


def emit(data: dict) -> list[str]:
    return [PY, "-c", f"import json; print('noise line'); print(json.dumps({data!r}))"]


PASSING = {"result": "pass", "summary": "ok", "checks": [{"name": "a", "result": "pass", "reason_code": None}],
           "details": {"count": 1}, "questions": [{"id": "q1", "text": "Did the camera light turn on?"}]}


def sections(timeout: int = 60) -> tuple[cp.Section, ...]:
    return tuple(cp.Section(n, f"fake {n}", 1, timeout, cp.not_built) for n in (1, 2, 3, 4))


def run(tmp_path: Path, commands: dict, selected=None, timeout: int = 60, **options):
    out, work = tmp_path / "report.md", tmp_path / "work"
    fakes = sections(timeout)
    options = {"yes": True, "interactive": False, **options}
    code = cp.run_suite(fakes, selected or {s.number for s in fakes}, out, work=work,
                        command=lambda section, _work: commands[section.number], **options)
    return code, out, work


def test_each_child_failure_is_a_finding_and_the_report_is_still_written(tmp_path):
    marker = tmp_path / "grandchild-ran"
    grandchild = f"import time, pathlib; time.sleep(3); pathlib.Path({str(marker)!r}).write_text('x')"
    hang = [PY, "-c", f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {grandchild!r}]); time.sleep(60)"]
    commands = {1: emit(PASSING), 2: [PY, "-c", "import sys; sys.exit(3)"], 3: hang, 4: [PY, "-c", "print('garbage')"]}
    started = time.monotonic()
    code, out, work = run(tmp_path, commands, timeout=2)
    assert code == cp.EXIT_OK and time.monotonic() - started < 30
    data = cp.report_data(out.read_text(encoding="utf-8"))
    found = {r["number"]: (r["result"], r["reason_code"], r["exit_code"]) for r in data["sections"]}
    assert found == {1: ("pass", None, 0), 2: ("fail", "crashed", 3), 3: ("fail", "timed-out", None), 4: ("fail", "bad-output", 0)}
    assert data["sections"][0]["details"] == {"count": 1} and data["sections"][2]["seconds"] >= 2
    time.sleep(3)
    assert not marker.exists(), "the timeout must kill the whole process tree"
    assert not work.exists()


def test_the_markdown_ends_with_a_json_block_equal_to_the_data(tmp_path):
    _, out, _ = run(tmp_path, {n: emit(PASSING) for n in (1, 2, 3, 4)})
    text = out.read_text(encoding="utf-8")
    data = cp.report_data(text)
    assert text.rstrip().endswith("```")
    assert data["schema"] == cp.REPORT_SCHEMA and data["suite_version"] == cp.SUITE_VERSION
    assert cp.render(data) == text
    assert "| 1. fake 1 | pass | ok |" in text and "**Not valid as evidence:**" in text


def test_a_backtick_run_in_the_data_does_not_break_the_json_fence():
    data = {"schema": "s", "suite_version": 1, "created_utc": "t", "evidence": {"valid": False, "reasons": ["x"], "tag": None},
            "sections": [], "answers": [], "notes": "a ```` note"}
    assert cp.report_data(cp.render(data)) == data


def test_only_runs_the_selected_sections(tmp_path):
    def never(section, _work):
        raise AssertionError("section 2 must not run")

    out, work = tmp_path / "r.md", tmp_path / "w"
    commands = {1: emit(PASSING), 3: emit(PASSING), 4: emit(PASSING)}
    cp.run_suite(sections(), {1}, out, yes=True, work=work, interactive=False,
                 command=lambda s, w: commands[s.number] if s.number == 1 else never(s, w))
    data = cp.report_data(out.read_text(encoding="utf-8"))
    assert [r["reason_code"] for r in data["sections"]] == [None, "not-selected", "not-selected", "not-selected"]
    assert data["selected"] == [1] and "partial-run" in data["evidence"]["reasons"]


def test_only_refuses_an_unknown_section():
    with pytest.raises(SystemExit):
        cp.main(["--only", "9"])


@pytest.mark.parametrize(("interactive", "answers"), [(True, ["n"]), (False, [])])
def test_no_consent_runs_nothing(tmp_path, interactive, answers):
    def never(section, work):
        raise AssertionError("nothing may run")

    out, work = tmp_path / "r.md", tmp_path / "w"
    code = cp.run_suite(sections(), {1, 2}, out, yes=False, work=work, command=never, interactive=interactive,
                        ask=lambda _: answers.pop(0))
    assert code == cp.EXIT_NO_CONSENT and not out.exists() and not work.exists()


def test_the_end_questions_and_the_note_are_recorded_and_scrubbed(tmp_path):
    user = "zz" + "testuser"
    answers = ["y", "y", f"camera ok, ask {user}"]
    code, out, _ = run(tmp_path, {1: emit(PASSING), 2: emit(PASSING), 3: emit(PASSING), 4: emit(PASSING)}, selected={1},
                       yes=False, interactive=True, ask=lambda _: answers.pop(0))
    data = cp.report_data(out.read_text(encoding="utf-8"))
    assert code == cp.EXIT_OK and data["answers"] == [{"section": 1, "id": "q1", "text": "Did the camera light turn on?", "answer": "yes"}]
    assert data["notes"] == f"camera ok, ask {user}"  # not a private term of this host


def test_ctrl_c_stops_the_run_writes_the_report_and_deletes_the_work_folder(tmp_path):
    def interrupt(section, work):
        (work / "download.bin").write_bytes(b"x")
        raise KeyboardInterrupt

    out, work = tmp_path / "r.md", tmp_path / "w"
    code = cp.run_suite(sections(), {1, 2, 3, 4}, out, yes=True, work=work, interactive=False,
                        command=lambda s, w: emit(PASSING) if s.number == 1 else interrupt(s, w))
    data = cp.report_data(out.read_text(encoding="utf-8"))
    assert code == cp.EXIT_CANCELLED and not work.exists()
    assert [r["reason_code"] for r in data["sections"]] == [None, "interrupted", "interrupted", "interrupted"]


def test_the_scrub_removes_the_user_name_the_home_folder_and_the_hostname():
    user, host = "zz" + "planted", "BOX-" + "4711"
    home = "C:" + "\\Users\\" + user
    data = {"a": home + "\\GitHub\\repo\\x.py", "b": [f"made on {host.lower()} by {user.upper()}"], "c": 5,
            "d": "/ho" + "me/" + "someone/x", "e": "gpu:10de:2484:0", "f": f"{user}x stays"}
    clean = cp.scrub(data, [home], [user, host])
    text = json.dumps({**clean, "f": None})
    assert user not in text.lower() and host.lower() not in text.lower() and "Users" not in text and "someone" not in text
    assert clean["e"] == "gpu:10de:2484:0" and clean["c"] == 5 and clean["f"] == f"{user}x stays"


def test_a_cleanup_error_is_a_row_and_the_work_folder_and_the_report_still_go(tmp_path, monkeypatch):
    """An error of one cleanup step must not skip the next step or the report."""
    root, outside = tmp_path / "zoo", tmp_path / "keep.bin"
    (root / "a-directory").mkdir(parents=True)  # unlink of a directory raises
    (root / "model.onnx").write_bytes(b"m")
    outside.write_bytes(b"k")
    monkeypatch.setattr(cp, "MODEL_ROOT", root)
    listed = json.dumps([str(root / "a-directory"), str(root / "model.onnx"), str(outside), str(root / ".." / "keep.bin")])
    writer = ("import pathlib, sys; pathlib.Path(sys.argv[1], 'remove-at-end.json').write_text(sys.argv[2]); "
              "print('{\"result\": \"pass\"}')")

    def broken(work):
        raise RuntimeError("no catalog")

    monkeypatch.setattr(cp, "remove_windows_packages", broken)
    out, work = tmp_path / "r.md", tmp_path / "w"
    code = cp.run_suite(sections()[:1], {1}, out, yes=True, work=work, interactive=False,
                        command=lambda s, w: [PY, "-c", writer, str(w), listed])
    text = out.read_text(encoding="utf-8")
    data = cp.report_data(text)
    assert code == cp.EXIT_OK and not work.exists() and not (root / "model.onnx").exists() and outside.exists()
    reasons = [(c["name"], c["reason_code"]) for c in data["cleanup"]]
    assert ("remove-windows-packages", "RuntimeError") in reasons and reasons.count(("remove-listed-file", "outside-model-root")) == 2
    assert len([r for r in reasons if r[0] == "remove-listed-file" and r[1] != "outside-model-root"]) == 1  # the directory
    assert "| remove-windows-packages | fail | RuntimeError |" in text


def test_a_child_with_a_complete_result_and_a_bad_exit_keeps_its_result(tmp_path):
    result = json.dumps(PASSING)
    commands = {1: [PY, "-c", f"import sys; print({result!r}, flush=True); sys.exit(3)"],
                2: [PY, "-c", f"import time; print({result!r}, flush=True); time.sleep(60)"],
                3: [PY, "-c", "import sys; print('half a line', flush=True); sys.exit(3)"], 4: emit(PASSING)}
    _, out, _ = run(tmp_path, commands, timeout=3)
    found = {r["number"]: r for r in cp.report_data(out.read_text(encoding="utf-8"))["sections"]}
    assert (found[1]["result"], found[1]["exit_code"], found[1]["details"]) == ("pass", 3, {"count": 1})
    assert found[1]["checks"][-1] == {"name": "exit", "result": "record-only", "reason_code": "crashed", "exit_code": 3}
    assert (found[2]["result"], found[2]["checks"][-1]["reason_code"], found[2]["exit_code"]) == ("pass", "timed-out", None)
    assert (found[3]["result"], found[3]["reason_code"]) == ("fail", "crashed") and found[3]["checks"] == []


def one_section(command, timeout=60):
    return cp.run_section(cp.Section(1, "fake", 1, timeout, cp.not_built), command)


def test_a_child_that_hangs_at_exit_is_killed_after_the_grace_time_and_keeps_its_result(monkeypatch):
    monkeypatch.setattr(cp, "EXIT_GRACE_SECONDS", 1)
    result = json.dumps(PASSING)
    started = time.monotonic()
    found = one_section([PY, "-c", f"import time; print({result!r}, flush=True); time.sleep(300)"], timeout=120)
    took = time.monotonic() - started
    print(f"hung-child return time: {took:.2f} s")
    assert took < 15 and found["result"] == "pass" and found["details"] == {"count": 1}
    assert found["checks"][-1] == {"name": "exit", "result": "record-only", "reason_code": "hung-at-exit", "exit_code": None,
                                   "grace_seconds": 1}


def test_a_child_that_exits_normally_after_its_result_has_no_exit_check(monkeypatch):
    monkeypatch.setattr(cp, "EXIT_GRACE_SECONDS", 1)
    found = one_section(emit(PASSING))
    assert found["result"] == "pass" and all(c["name"] != "exit" for c in found["checks"]) and found["exit_code"] == 0


def test_a_child_with_no_result_that_hangs_is_timed_out(monkeypatch):
    monkeypatch.setattr(cp, "EXIT_GRACE_SECONDS", 1)
    found = one_section([PY, "-c", "import time; print('noise', flush=True); time.sleep(300)"], timeout=2)
    assert (found["result"], found["reason_code"]) == ("fail", "timed-out")


def test_a_result_bigger_than_a_pipe_buffer_is_parsed_whole(monkeypatch):
    monkeypatch.setattr(cp, "EXIT_GRACE_SECONDS", 1)
    script = f"import json; print(json.dumps({{**{PASSING!r}, 'details': {{'blob': 'x' * 200_000}}}}))"  # not a long command line
    found = one_section([PY, "-c", script])
    assert found["result"] == "pass" and len(found["details"]["blob"]) == 200_000


def test_a_section_child_ends_with_os_exit_after_its_result(tmp_path):
    """A teardown that crashes after the result (here an atexit hook with exit code 7) must not change the exit code."""
    script = Path(cp.__file__).resolve()
    code = (f"import atexit, os, runpy, sys; atexit.register(os._exit, 7); "
            f"sys.argv = [{str(script)!r}, '--section', '6', '--work', {str(tmp_path)!r}]; "
            f"sys.path.insert(0, {str(script.parent)!r}); runpy.run_path({str(script)!r}, run_name='__main__')")
    done = subprocess.run([PY, "-B", "-c", code], capture_output=True, text=True, timeout=120, check=False)  # noqa: S603
    assert done.returncode == 0 and json.loads(done.stdout.splitlines()[-1])["reason_code"] == "not-built"


def test_a_stale_work_folder_that_cannot_be_deleted_stops_the_run_before_any_section(tmp_path, monkeypatch, capsys):
    def never(section, work):
        raise AssertionError("nothing may run")

    out, work = tmp_path / "r.md", tmp_path / "w"
    work.mkdir()
    monkeypatch.setattr(cp.shutil, "rmtree", lambda path, ignore_errors=False: None)  # for example a file that a program holds open
    code = cp.run_suite(sections(), {1}, out, yes=True, work=work, command=never, interactive=False)
    assert code == cp.EXIT_FAILURE and not out.exists() and "Delete it by hand" in capsys.readouterr().err


def test_a_stale_remove_list_is_acted_on_at_the_start_only_inside_the_model_root(tmp_path, monkeypatch):
    root = tmp_path / "zoo"
    root.mkdir()
    (root / "left.onnx").write_bytes(b"m")
    (tmp_path / "mine.txt").write_bytes(b"k")
    monkeypatch.setattr(cp, "MODEL_ROOT", root)
    work = tmp_path / "w"
    work.mkdir()
    (work / "remove-at-end.json").write_text(json.dumps([str(root / "left.onnx"), str(tmp_path / "mine.txt")]))
    out = tmp_path / "r.md"
    cp.run_suite(sections()[:1], {1}, out, yes=True, work=work, interactive=False, command=lambda s, w: emit(PASSING))
    assert not (root / "left.onnx").exists() and (tmp_path / "mine.txt").exists()
    assert [c["reason_code"] for c in cp.report_data(out.read_text(encoding="utf-8"))["cleanup"]] == ["outside-model-root"]


def test_sigterm_sighup_and_sigbreak_take_the_path_of_ctrl_c():
    import signal

    names = [name for name in ("SIGTERM", "SIGHUP", "SIGBREAK") if hasattr(signal, name)]
    before = {name: signal.getsignal(getattr(signal, name)) for name in names}
    try:
        cp.stop_on_signals()
        for name in names:
            with pytest.raises(KeyboardInterrupt):
                signal.getsignal(getattr(signal, name))(getattr(signal, name), None)
    finally:
        for name, handler in before.items():
            signal.signal(getattr(signal, name), handler)


def test_section_1_python_or_package_differences_make_the_report_not_evidence():
    facts = {"tag": "certify-1", "commit": "c" * 40, "clean": True}
    first = {"number": 1, "reason_code": None, "details": {"checkout": facts},
             "checks": [cp.check("python", "fail", "python-mismatch"), cp.check("packages", "fail", "packages-differ")]}
    result = cp.evidence_state([first], {1}, sections()[:1])
    assert result["valid"] is False and result["reasons"] == ["python-differs", "packages-differ"]
    first["checks"] = [cp.check("python", "pass"), cp.check("packages", "pass")]
    assert cp.evidence_state([first], {1}, sections()[:1])["valid"] is True


def test_a_common_host_or_user_name_does_not_delete_public_facts_but_the_notes_are_always_scrubbed(tmp_path, monkeypatch):
    data = {"sections": [{"name": "Hardware probe", "result": "pass", "summary": "Ubuntu 24.04.1 LTS, field-test pass",
                          "details": {"host": {"os_label": "Ubuntu 24.04.1 LTS", "cpu_name": "AMD Ryzen 9"},
                                      "eps": [{"key": "migraphx", "catalog_status": "field-test"}],
                                      "os": {"version": "#45-Ubuntu SMP PREEMPT_DYNAMIC", "label": "Windows 11 Home 26H2"}},
                          "checks": [{"name": "os_label", "result": "pass", "reason_code": None}]}]}
    words = ["ubuntu", "test", "home", "zz" + "planted"]
    kept = cp.report_words(words, data, ["Windows 11 Home"])
    assert kept == ["zz" + "planted"]
    clean = cp.scrub(data, [], kept)
    assert clean["sections"][0]["summary"] == "Ubuntu 24.04.1 LTS, field-test pass"
    assert clean["sections"][0]["details"]["os"]["label"] == "Windows 11 Home 26H2"
    assert cp.scrub("ubuntu at home, test", [], words) == "<private> at <private>, <private>"  # the notes: each word
    monkeypatch.setattr(cp, "private_terms", lambda: ([], ["ubuntu", "zz" + "planted"]))
    monkeypatch.setattr(cp, "host_facts_text", lambda: ["Ubuntu 24.04.1 LTS"])
    answers = ["y", "ubuntu box of zz" + "planted"]
    _, out, _ = run(tmp_path, {1: emit(PASSING)}, selected={1}, yes=True, interactive=True, ask=lambda _: answers.pop(0))
    report = cp.report_data(out.read_text(encoding="utf-8"))
    assert report["scrub"] == {"exempted_terms": 1} and report["notes"] == "<private> box of <private>"


def test_the_short_macos_host_name_is_scrubbed_with_and_without_local(monkeypatch):
    host = "Doms" + "-MacBook-Pro"
    monkeypatch.setattr(cp.socket, "gethostname", lambda: host + ".local")
    monkeypatch.setattr(cp.platform, "node", lambda: host + ".local")
    _, words = cp.private_terms()
    assert host in words and host + ".local" in words
    assert cp.scrub([f"{host}.local", host, f"made on {host}"], [], words) == ["<private>", "<private>", "made on <private>"]


def test_a_placeholder_child_prints_not_built(capsys):
    assert cp.main(["--section", "6"]) == 0
    assert json.loads(capsys.readouterr().out)["reason_code"] == "not-built"


# --------------------------------------------------------------------------------------------
# Section 1
# --------------------------------------------------------------------------------------------


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args], cwd=root, check=True,  # noqa: S603, S607
                   capture_output=True)


def test_section_1_reads_the_tag_and_the_state_of_the_tree(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("1")
    git(tmp_path, "add", "a.txt")
    git(tmp_path, "commit", "-q", "-m", "one")
    (tmp_path / cp.WORK_DIR.name).mkdir()
    (tmp_path / cp.WORK_DIR.name / "x").write_text("ignored")
    untagged, facts = cp.checkout_check(tmp_path)
    assert (untagged["result"], untagged["reason_code"], facts["clean"], facts["tag"]) == ("record-only", "no-tag", True, None)
    git(tmp_path, "tag", "certify-1")
    tagged, facts = cp.checkout_check(tmp_path)
    assert (tagged["result"], facts["tag"], len(facts["commit"])) == ("pass", "certify-1", 40)
    (tmp_path / "a.txt").write_text("2")
    dirty, facts = cp.checkout_check(tmp_path)
    assert (dirty["result"], dirty["reasons"], facts["changed_files"]) == ("record-only", ["modified-tree"], 1)
    result = cp.evidence_state([{"number": 1, "reason_code": None, "details": {"checkout": facts}}], {1}, sections()[:1])
    assert result["valid"] is False and result["reasons"] == ["modified-tree"]


def test_section_1_without_git_history_is_not_evidence(tmp_path):
    check, facts = cp.checkout_check(tmp_path)
    assert check["reason_code"] == "no-git" and facts["commit"] is None


LOCK = {"package": [
    {"name": "proj", "source": {"editable": "."},
     "dependencies": [{"name": "a"}, {"name": "w", "marker": "sys_platform == 'no-such-os'"}, {"name": "f", "extra": ["with-x"]}],
     "optional-dependencies": {"media": [{"name": "d"}, {"name": "a"}]},
     "dev-dependencies": {"dev": [{"name": "c"}]}},
    {"name": "a", "version": "1.0", "dependencies": [{"name": "e"}]},
    {"name": "c", "version": "2.0"}, {"name": "d", "version": "3.0"}, {"name": "e", "version": "4.0rc1"},
    {"name": "f", "version": "5.0", "optional-dependencies": {"with-x": [{"name": "g"}]}},
    {"name": "g", "version": "6.0"}, {"name": "w", "version": "7.0"}]}


def test_the_lock_walk_follows_markers_extras_and_groups():
    required, extras = cp.lock_packages(LOCK)
    assert required == {"a": "1.0", "e": "4.0rc1", "c": "2.0", "f": "5.0", "g": "6.0"}
    assert extras == {"d": "3.0"}


def test_the_package_comparison_lists_mismatches_and_missing_packages():
    installed = {"a": "1.0", "e": "4.0rc1", "c": "2.1", "f": "5.0"}
    found = cp.compare_packages(*cp.lock_packages(LOCK), installed.get)
    assert found["mismatched"] == [{"name": "c", "locked": "2.0", "installed": "2.1"}]
    assert found["missing"] == ["g"] and found["extras_not_installed"] == ["d"]


def test_the_plan_prints_decimal_megabytes_with_one_decimal_under_10():
    downloads = lambda options: (("cuda.whl", 1_009_139_129), ("image.jpg", 212_902), ("small.whl", 9_940_000))  # noqa: E731
    text = cp.plan_text((cp.Section(3, "s", 1, 60, cp.not_built, downloads),), {3}, Path("r.md"))
    assert "cuda.whl (1009 MB), image.jpg (0.2 MB), small.whl (9.9 MB)." in text


def test_main_stops_bytecode_before_any_import_of_the_checkout(monkeypatch):
    """A run without `-B` must leave no `__pycache__` in the clone: the flag goes on first, and the module imports only the
    standard library at its top level."""
    import ast

    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    with pytest.raises(SystemExit):
        cp.main(["--only", "99"])
    assert sys.dont_write_bytecode is True
    tree = ast.parse(Path(cp.__file__).read_text(encoding="utf-8"))
    roots = {(node.module if isinstance(node, ast.ImportFrom) else alias.name).split(".")[0]
             for node in tree.body if isinstance(node, ast.Import | ast.ImportFrom) for alias in node.names}
    assert roots - {"__future__"} <= sys.stdlib_module_names


def test_the_report_file_name_and_created_utc_are_the_start_of_the_run(tmp_path, monkeypatch):
    _, out, _ = run(tmp_path, {1: emit(PASSING)}, selected={1}, started=time.gmtime(0))
    assert cp.report_data(out.read_text(encoding="utf-8"))["created_utc"] == "1970-01-01T00:00:00Z"
    captured = {}
    monkeypatch.setattr(cp, "stop_on_signals", lambda: None)
    monkeypatch.setattr(cp, "run_suite", lambda sections, selected, out, **options: captured.update(out=out, **options) or 0)
    monkeypatch.chdir(tmp_path)
    assert cp.main(["--only", "1", "--yes"]) == 0
    assert captured["out"].name == time.strftime("certify-report-%Y%m%dT%H%M%SZ.md", captured["started"])


def test_section_1_records_no_package_version():
    """The tag and the commit identify the code; `skellytracker.__version__` is the same in each checkout."""
    assert "skellytracker" not in cp.onnx_stack_facts()


def test_section_1_records_the_telemetry_switch(monkeypatch, tmp_path):
    """Section 1 records the value of ORT_DISABLE_TELEMETRY; a value that is not 1 or true is `record-only` (ADR-BZ7X)."""
    for value, expected in (("1", ("pass", None)), (" TRUE ", ("pass", None)), ("0", ("record-only", "telemetry-on")),
                            (None, ("record-only", "telemetry-on"))):
        monkeypatch.setattr(cp, "onnx_stack_facts", lambda value=value: {"ort_disable_telemetry": value})
        found = {c["name"]: (c["result"], c["reason_code"]) for c in cp.section_checkout(tmp_path, root=tmp_path)["checks"]}
        assert found["telemetry-switch"] == expected


def test_the_report_records_the_telemetry_folder_before_and_after_as_booleans(tmp_path, monkeypatch):
    states = iter([False, True])
    monkeypatch.setattr(cp, "telemetry_database", lambda: next(states))
    _, out, _ = run(tmp_path, {1: emit(PASSING)}, selected={1})
    text = out.read_text(encoding="utf-8")
    assert cp.report_data(text)["telemetry_database"] == {"before": False, "after": True}
    assert "Telemetry folder of ONNX Runtime: before no, after yes." in text


def test_the_suite_and_the_package_give_a_child_the_same_grace_time():
    """The frame imports no package module, so it keeps its own copy of the value."""
    from skellytracker.core.eps import verification

    assert cp.EXIT_GRACE_SECONDS == verification.EXIT_GRACE_SECONDS
