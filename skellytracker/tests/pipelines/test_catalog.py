"""The pipeline catalog, on a temporary package root and a temporary user root (pipeline.file, Behaviour items 6 and 7)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from skellytracker.core.detectors.catalog import USER_ROOT_VARIABLE
from skellytracker.core.pipelines import catalog
from skellytracker.core.pipelines.catalog import (
    PipelineEntry,
    PipelineNotFoundError,
    PipelineUnavailableError,
    find_pipeline,
    list_pipelines,
)
from skellytracker.core.pipelines.loading import load_pipeline
from skellytracker.tests.pipelines.test_loading import BASE, changed, write

KEY = "demo@demo-source"


@pytest.fixture
def package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The package root of the test. The catalog of these tests has no file of `core/model_zoo/`."""
    monkeypatch.delenv(USER_ROOT_VARIABLE, raising=False)
    monkeypatch.setattr(catalog, "PACKAGE_PIPELINE_ROOT", tmp_path / "package" / "pipelines")
    return tmp_path / "package" / "pipelines"


@pytest.fixture
def user(tmp_path: Path, package: Path) -> Path:
    return tmp_path / "user"


def version(value: str, name: str = "demo-source") -> dict[str, Any]:
    return changed(source={"name": name, "version": value})


def test_the_catalog_finds_the_files_of_the_package_root_and_of_the_user_root(package: Path, user: Path) -> None:
    built_in = write(package, changed(pipeline_id="built-in", source={"name": "skellytracker", "version": "2.0.0"}, description="A text."), "built-in.pipeline.yaml")
    mine = write(user / "pipelines", BASE)
    write(user / "pipelines" / "deeper", changed(pipeline_id="deep"), "deep.pipeline.yaml")  # not directly in the root
    write(user / "pipelines", changed(pipeline_id="plain"), "plain.yaml")  # not `*.pipeline.yaml`
    write(user / "detectors", changed(pipeline_id="other"), "other.pipeline.yaml")  # not in `pipelines/`
    assert list_pipelines(user) == [
        PipelineEntry("built-in@skellytracker", "2.0.0", built_in, "A text.", True, needs_execution_provider=False),
        PipelineEntry(KEY, "1.0.0", mine, "", True, needs_execution_provider=False),
    ]
    assert find_pipeline(KEY, user).path == mine
    assert find_pipeline(KEY, user).warnings == ()


def test_the_user_root_comes_from_the_environment_variable(package: Path, user: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write(user / "pipelines", BASE)
    assert list_pipelines(user / "empty") == []
    monkeypatch.setenv(USER_ROOT_VARIABLE, str(user))
    assert [entry.key for entry in list_pipelines()] == [KEY]
    assert load_pipeline(KEY) == load_pipeline(BASE)


def test_the_newest_version_of_a_key_wins_in_pep_440_order(package: Path, user: Path) -> None:
    old = write(package, version("1.9.0"))
    new = write(user / "pipelines", version("1.10.0rc1"))
    entries = list_pipelines(user)
    assert [(entry.version, entry.path, entry.superseded) for entry in entries] == [("1.10.0rc1", new, False), ("1.9.0", old, True)]
    assert all(entry.available for entry in entries)
    assert find_pipeline(KEY, user).path == new
    assert load_pipeline(KEY, user_root=user).source.version == "1.10.0rc1"


def test_a_pin_wins_over_the_newest_version(package: Path, user: Path) -> None:
    old = write(package, version("1.9.0"))
    write(user / "pipelines", version("1.10.0"))
    assert find_pipeline(f"{KEY}==1.9.0", user).path == old
    assert find_pipeline(f"{KEY}==1.9", user).path == old  # the same PEP 440 version
    assert load_pipeline(f"{KEY}==1.9.0", user_root=user).source.version == "1.9.0"
    with pytest.raises(PipelineNotFoundError, match="no version '3.0.0'"):
        find_pipeline(f"{KEY}==3.0.0", user)


def test_a_key_that_the_catalog_does_not_have_is_not_found(package: Path, user: Path) -> None:
    write(user / "pipelines", BASE)
    with pytest.raises(PipelineNotFoundError, match="no entry 'other@demo-source'"):
        find_pipeline("other@demo-source", user)
    with pytest.raises(KeyError):
        load_pipeline("other@demo-source", user_root=user)


def test_the_source_name_skellytracker_is_reserved_for_the_package_root(package: Path, user: Path) -> None:
    write(package, version("2.0.0", "skellytracker"))
    assert find_pipeline("demo@skellytracker", user).available
    (package / "demo.pipeline.yaml").unlink()
    path = write(user / "pipelines", version("2.0.0", "skellytracker"))
    (entry,) = list_pipelines(user)
    assert (entry.key, entry.available) == ("demo@skellytracker", False)
    assert "reserved for the package root" in entry.unavailable_reason
    with pytest.raises(PipelineUnavailableError, match="reserved"):
        load_pipeline("demo@skellytracker", user_root=user)
    assert load_pipeline(path).source.name == "skellytracker"  # a load by path always works


def test_the_same_key_and_version_in_two_files_is_an_error_that_names_both_paths(package: Path, user: Path) -> None:
    first, second = write(package, BASE), write(user / "pipelines", BASE)
    entries = list_pipelines(user)
    assert [(entry.path, entry.available, entry.superseded) for entry in entries] == [(first, True, False), (second, True, False)]
    with pytest.raises(PipelineUnavailableError) as error:
        load_pipeline(KEY, user_root=user)
    assert str(first) in str(error.value) and str(second) in str(error.value)
    assert load_pipeline(second) == load_pipeline(BASE)  # a load by path always works
    write(user / "pipelines", version("1.0.1"))
    assert find_pipeline(KEY, user).path == second
    assert find_pipeline(f"{KEY}==1.0.0", user).path == first


def test_a_file_that_does_not_load_is_in_the_list_with_the_reason(package: Path, user: Path) -> None:
    write(user / "pipelines", changed(outputs={"holistic": "nothing.keypoints"}))
    write(user / "pipelines", changed(pipeline_id="misnamed"), "wrong.pipeline.yaml")
    write(user / "pipelines", changed(pipeline_id="no-source", source=...), "no-source.pipeline.yaml")
    write(user / "pipelines", {**version("one"), "pipeline_id": "bad-version"}, "bad-version.pipeline.yaml")
    reasons = {entry.key: entry.unavailable_reason for entry in list_pipelines(user)}
    assert all(not entry.available for entry in list_pipelines(user))
    assert "V-pipeline.outputs-1" in reasons[KEY]
    assert reasons["misnamed@demo-source"].startswith("V-pipeline.file-2")
    assert "Field required" in reasons["no-source@unknown"]
    assert reasons["bad-version@demo-source"] == "source.version 'one' is not a PEP 440 version"
    with pytest.raises(PipelineUnavailableError, match=f"{KEY} is unavailable: .*V-pipeline.outputs-1"):
        load_pipeline(KEY, user_root=user)


def test_a_file_with_no_plain_parse_or_no_pipeline_id_is_not_in_the_list(package: Path, user: Path, caplog: pytest.LogCaptureFixture) -> None:
    folder = user / "pipelines"
    folder.mkdir(parents=True)
    (folder / "broken.pipeline.yaml").write_text("nodes: [", encoding="utf-8")
    (folder / "list.pipeline.yaml").write_text("- 1\n", encoding="utf-8")
    write(folder, changed(pipeline_id=...), "no-id.pipeline.yaml")
    with caplog.at_level(logging.WARNING, logger=catalog.__name__):
        assert list_pipelines(user) == []
    assert len(caplog.records) == 3
