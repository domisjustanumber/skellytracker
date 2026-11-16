"""The `ep_pack` test: `selftest()` with the real test pack. Run it with `pytest -m ep_pack`. It needs the network.

`SKELLYTRACKER_EP_WHEEL_CACHE` names a folder that keeps the downloaded wheels between runs. CI
caches it with a key on the sha256 of `ep_lock.yaml`.
"""

import os
import sys
from pathlib import Path

import pytest

from skellytracker.core import eps
from skellytracker.core.eps import _download, cli, store
from skellytracker.core.eps import catalog as catalog_module
from skellytracker.tests.test_eps_store import server  # noqa: F401 - fixture

pytestmark = pytest.mark.ep_pack


def test_selftest_installs_the_test_pack_from_a_local_index_with_a_resume(server, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.setenv(store.STORE_VARIABLE, str(tmp_path / "eps"))
    catalog = eps.load_catalog()
    lock = catalog.pack_lock("openvino")
    if lock is None:  # macOS: no pack; the self test runs the trial sessions of the built-in EPs
        result = eps.selftest()
        assert result.ok, result.steps
        assert [name for name, _, _ in result.steps] == ["catalog", "cpu trial session", "coreml trial session"]
        return
    cache = Path(os.environ.get("SKELLYTRACKER_EP_WHEEL_CACHE", tmp_path / "wheels"))
    for wheel in lock["wheels"]:
        target = cache / wheel["filename"]
        if not (target.is_file() and _download.sha256_of(target) == wheel["sha256"]):
            os.replace(_download.fetch(wheel["url"], wheel["sha256"], cache / f"{wheel['sha256']}.part"), target)
        server.files[wheel["filename"]] = target.read_bytes()
    server.drop_after = 1_000_000  # one dropped connection, then a resume with a byte range
    result = eps.selftest(server.url)
    assert result.ok, result.steps
    assert [name for name, _, _ in result.steps] == ["catalog", "cpu trial session", "test pack"]
    assert any(requested and requested.startswith("bytes=") for requested, _ in server.requests)
    assert store.read_manifest("openvino", "1.8.1")["ep_name"] == "OpenVINOExecutionProvider"
    assert "openvino" not in [row.key for row in eps.status().eps]  # the test pack is not an EP of a user
    assert cli.main(["selftest", "--index-url", server.url, "--json"]) == 0


@pytest.mark.skipif(sys.platform == "darwin", reason="macOS has no pack")
def test_the_test_pack_is_not_a_user_pack():
    assert catalog_module.load_catalog().data["eps"]["openvino"]["kind"] == "reserved"
    assert cli.main(["install", "openvino", "--dry-run"]) == 2
