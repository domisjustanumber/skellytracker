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
