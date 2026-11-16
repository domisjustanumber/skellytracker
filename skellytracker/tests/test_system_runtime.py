"""`probe_runtime()`, `probe_environment()` and `probe_loaded_libraries()`."""

import dataclasses
import json
import os
import sys

import pytest

from skellytracker.core import system
from skellytracker.core._hardware import libraries
from skellytracker.core.system import environment, loaded_libraries, runtime
from skellytracker.tests.hw_fakes import FakeNvml, install_nvml, nvml_gpu


@pytest.mark.parametrize(
    ("direct_url", "expected"),
    [
        (None, None),
        ({"url": "https://ann:secret@example.com/freemocap/skellytracker.git",
          "vcs_info": {"vcs": "git", "commit_id": "a" * 40, "requested_revision": "main"}},
         {"vcs": "git", "url": "https://example.com/freemocap/skellytracker.git", "commit": "a" * 40, "requested_revision": "main"}),
        ({"url": "file:///data/ann/skellytracker", "dir_info": {"editable": True}},
         {"url": None, "local": "skellytracker", "editable": True}),
        ({"url": "git+file:///data/ann/repo", "vcs_info": {"vcs": "git", "commit_id": "b" * 40}},
         {"url": None, "local": "repo", "commit": "b" * 40}),
        ({"url": "https://example.com/pkg-1.0.whl", "archive_info": {"hashes": {"sha256": "ab"}}},
         {"url": "https://example.com/pkg-1.0.whl", "hashes": (("sha256", "ab"),)}),
    ],
)
def test_package_source(direct_url, expected):
    source = environment.package_source(None if direct_url is None else json.dumps(direct_url))
    if expected is None:
        assert source is None
        return
    assert {name: getattr(source, name) for name in expected} == expected
    assert "secret" not in repr(source) and "/data/ann" not in repr(source)


def test_environment_has_no_local_path(monkeypatch):
    monkeypatch.setattr(environment, "_cached", None)
    monkeypatch.setattr(sys, "orig_argv", [sys.executable, os.path.join(sys.prefix, "run.py"), "--flag"])
    info = system.probe_environment()
    assert info.frozen is False and info.python.version.count(".") == 2
    assert info.argv[1:] == ("run.py", "--flag")
    assert "pyyaml" in {package.name for package in info.packages}
    text = json.dumps(dataclasses.asdict(info))
    for local in (sys.prefix, sys.executable, os.path.expanduser("~")):
        assert local not in text and local.replace("\\", "\\\\") not in text and local.replace("\\", "/") not in text
    assert system.probe_environment() is info


def test_runtime_facts(monkeypatch):
    import onnxruntime

    install_nvml(monkeypatch, FakeNvml([nvml_gpu()]))
    monkeypatch.setattr(runtime, "_cached", None)
    monkeypatch.setenv("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    info = system.probe_runtime()
    assert info.ort_version == onnxruntime.__version__ and "CPUExecutionProvider" in info.ep_names
    assert info.ort_packages == ("onnxruntime",) and info.python_version.count(".") == 2
    assert info.nvidia.cuda_device_order == "PCI_BUS_ID" and info.nvidia.driver_supported_cuda_version == "13.3"
    assert system.probe_runtime() is info


def test_runtime_with_no_onnxruntime_and_no_nvml(monkeypatch):
    install_nvml(monkeypatch, FakeNvml(fail="no driver"))
    monkeypatch.setattr(runtime, "_cached", None)
    monkeypatch.delenv("CUDA_DEVICE_ORDER", raising=False)
    monkeypatch.setitem(sys.modules, "onnxruntime", None)  # makes `import onnxruntime` raise
    info = runtime._probe()
    assert info.ort_version is None and info.ep_names == () and info.nvidia is None
    assert any(line.startswith("onnxruntime: ") for line in info.probe_errors)


def test_loaded_libraries_from_a_fake_module_list(monkeypatch):
    paths = ["/opt/app/lib/libcudnn.so.9.27.0", "/opt/app/lib/libcublas.so.13", "/usr/lib/libc.so.6",
             "/opt/app/lib/libopenvino.so.2026.1", "/opt/app/lib/libcudnn.so.9.27.0"]
    monkeypatch.setattr(libraries, "loaded_module_paths", lambda: paths)
    monkeypatch.setattr(libraries.sys, "platform", "linux")
    info = loaded_libraries.probe_loaded_libraries()
    assert [(row.name, row.version, row.source) for row in info.nvidia.libraries] == [
        ("cublas.so.13", "13", "soname:libcublas.so.13"), ("cudnn.so.9.27.0", "9.27.0", "soname:libcudnn.so.9.27.0")]
    assert [row.name for row in info.libraries] == ["openvino.so.2026.1"]
    assert "/opt/app" not in repr(info)


def test_proc_maps_lines():
    lines = ["7f00-7f01 r-xp 00000000 08:01 123    /usr/lib/libc.so.6\n", "7f02-7f03 rw-p 00000000 00:00 0 \n",
             "7f04-7f05 rw-p 00000000 00:00 0          [heap]\n", "7f06-7f07 r--p 00000000 08:01 9  /opt/a b/libcudnn.so.9\n"]
    assert libraries.maps_paths(lines) == ["/opt/a b/libcudnn.so.9", "/usr/lib/libc.so.6"]


def test_loaded_libraries_reads_this_process():
    info = system.probe_loaded_libraries()
    assert info.probe_errors == () and all("/" not in row.source and "\\" not in row.source for row in info.libraries)


@pytest.mark.skipif(sys.platform != "win32", reason="version.dll")
def test_file_version_of_a_system_dll():
    version = libraries.file_version(os.path.join(os.environ["SystemRoot"], "System32", "kernel32.dll"))
    assert version is not None and version.count(".") == 3
