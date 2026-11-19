"""The download engine on a local `http.server` with a `Range` handler, and the EP store: install, remove and gc."""

import hashlib
import io
import multiprocessing
import os
import threading
import time
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from skellytracker.core.eps import _download, installer, store
from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps.records import InstallPlan
from skellytracker.core.errors import EpRequestError, EpUnavailableError
from skellytracker.tests.hw_fakes import gpu, host

DATA = bytes(range(256)) * 2000  # 512 000 bytes
SHA = hashlib.sha256(DATA).hexdigest()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        server = self.server
        server.requests.append((self.headers.get("Range"), self.headers.get("If-Range")))
        if self.path.lstrip("/") in server.redirects:
            self.send_response(302)
            self.send_header("Location", server.redirects[self.path.lstrip("/")])
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if server.statuses:
            self.send_response(server.statuses.pop(0))
            self.send_header("Retry-After", "0")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        data = server.files.get(self.path.lstrip("/"))
        if data is None:
            self.send_error(404)
            return
        start, requested = 0, self.headers.get("Range")
        if requested and server.ranges and self.headers.get("If-Range") == server.etag:
            start = int(requested[len("bytes="):-1])
            if start >= len(data):
                self.send_error(416)
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(data) - 1}/{len(data)}")
        else:
            self.send_response(200)
        body = data[start:]
        self.send_header("Content-Length", str(len(body)))
        self.send_header("ETag", server.etag)
        self.end_headers()
        if server.drop_after is not None:  # a dropped connection: a part of the body, then the end
            body, server.drop_after = body[: server.drop_after], None
            self.close_connection = True
        self.wfile.write(body)

    def log_message(self, *_):
        pass


@pytest.fixture
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.files, httpd.requests, httpd.statuses, httpd.redirects = {"file.bin": DATA}, [], [], {}
    httpd.ranges, httpd.etag, httpd.drop_after = True, '"v1"', None
    httpd.url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture(autouse=True)
def ep_store(tmp_path, monkeypatch):
    monkeypatch.setenv(store.STORE_VARIABLE, str(tmp_path / "eps"))
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "win_amd64")
    return tmp_path / "eps"


def test_the_store_and_the_cache_follow_their_variables(ep_store, tmp_path, monkeypatch):
    monkeypatch.delenv(store.CACHE_VARIABLE, raising=False)
    assert store.store_root() == ep_store and store.cache_root().name == "ep-cache" and tmp_path not in store.cache_root().parents
    monkeypatch.setenv(store.CACHE_VARIABLE, str(tmp_path / "cache"))
    assert store.cache_root() == tmp_path / "cache"


def fetch(server, part, **kwargs):
    return _download.fetch(server.url + "file.bin", SHA, part, sleep=lambda seconds: None, **kwargs)


def test_download_and_sha256(server, tmp_path):
    part = fetch(server, tmp_path / "p" / "x.part")
    assert part.read_bytes() == DATA and not (tmp_path / "p" / "x.part.json").exists()
    assert server.requests == [(None, None)]


def test_a_dropped_connection_resumes_with_a_byte_range(server, tmp_path):
    server.drop_after = 100_000
    assert fetch(server, tmp_path / "x.part").read_bytes() == DATA
    assert server.requests == [(None, None), ("bytes=100000-", '"v1"')]


def test_a_server_with_no_ranges_and_a_changed_file_start_again(server, tmp_path):
    server.drop_after, server.ranges = 100_000, False
    assert fetch(server, tmp_path / "x.part").read_bytes() == DATA  # the 200 answer starts the file again
    server.drop_after, server.ranges = 100_000, True
    part = tmp_path / "y.part"
    original, server.etag = _download._attempt, '"v2"'

    def change_the_file_after_the_drop(*args):
        try:
            return original(*args)
        finally:
            server.etag = '"v3"'  # If-Range is then not the validator of the server

    _download._attempt = change_the_file_after_the_drop
    try:
        assert fetch(server, part).read_bytes() == DATA
    finally:
        _download._attempt = original
    assert server.requests[-1] == ("bytes=100000-", '"v2"')


def test_a_complete_partial_file_passes_after_416(server, tmp_path):
    part = tmp_path / "x.part"
    part.write_bytes(DATA)
    store.write_json(tmp_path / "x.part.json", {"url": server.url + "file.bin", "validator": '"v1"'})
    assert fetch(server, part).read_bytes() == DATA
    assert server.requests == [(f"bytes={len(DATA)}-", '"v1"')]


def test_sha256_mismatch_deletes_the_file(server, tmp_path):
    server.files["file.bin"] = DATA[:-1] + b"x"
    with pytest.raises(_download.DownloadError) as caught:
        fetch(server, tmp_path / "x.part")
    assert caught.value.code == "hash-mismatch" and not (tmp_path / "x.part").exists() and len(server.requests) == 2


def test_cancel_keeps_the_partial_file_and_a_later_call_resumes(server, tmp_path):
    cancel = threading.Event()
    with pytest.raises(_download.CancelledError):
        fetch(server, tmp_path / "x.part", cancel=cancel, progress=lambda have: cancel.set() if have >= 200_000 else None)
    size = (tmp_path / "x.part").stat().st_size
    assert 200_000 <= size < len(DATA)
    assert fetch(server, tmp_path / "x.part").read_bytes() == DATA
    assert server.requests[-1] == (f"bytes={size}-", '"v1"')


def test_retry_status_and_no_retry_for_404(server, tmp_path):
    server.statuses = [503, 429]
    assert fetch(server, tmp_path / "x.part").read_bytes() == DATA and len(server.requests) == 3
    with pytest.raises(_download.DownloadError) as caught:
        _download.fetch(server.url + "missing.bin", SHA, tmp_path / "y.part", sleep=lambda seconds: None)
    assert caught.value.code == "http-error" and len(server.requests) == 4
    server.statuses = [500] * 9
    with pytest.raises(_download.DownloadError):
        fetch(server, tmp_path / "z.part")
    assert len(server.requests) == 4 + 6  # the first attempt and 5 new attempts


def test_only_https_and_loopback_http(tmp_path):
    for url in ("http://example.com/x.whl", "ftp://127.0.0.1/x.whl", "file:///x.whl"):
        with pytest.raises(_download.DownloadError):
            _download.fetch(url, SHA, tmp_path / "x.part")


def test_a_redirect_to_a_url_that_is_not_https_is_an_error(server, tmp_path):
    server.redirects["moved.bin"] = "http://example.invalid/file.bin"
    with pytest.raises(_download.DownloadError) as caught:
        _download.fetch(server.url + "moved.bin", SHA, tmp_path / "x.part", sleep=lambda seconds: None)
    assert caught.value.code == "http-error" and len(server.requests) == 1  # refused at once: no request to the new host, no retry
    server.redirects["local.bin"] = server.url + "file.bin"  # loopback http to loopback http: a local test index
    assert _download.sha256_of(_download.fetch(server.url + "local.bin", SHA, tmp_path / "y.part", sleep=lambda s: None)) == SHA
    with pytest.raises(_download.DownloadError, match="from https to http"):
        _download.HttpsRedirectHandler().redirect_request(urllib.request.Request("https://files.example/a"), None, 302, "Found", {},
                                                          "http://127.0.0.1/a")


def test_trust_store_order_and_system_proxy(monkeypatch):
    assert _download.trust_store_source({"SSL_CERT_FILE": "roots.pem"}) == ("environment", "roots.pem")
    assert _download.trust_store_source({"SSL_CERT_DIR": "roots"}) == ("environment", "roots")
    monkeypatch.setattr(_download.sys, "platform", "linux")
    assert _download.trust_store_source({}, exists=lambda path: path == _download.LINUX_BUNDLES[1]) == ("bundle", _download.LINUX_BUNDLES[1])
    assert _download.trust_store_source({}, exists=lambda path: False) == ("system", None)
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.test:3128")
    assert urllib.request.getproxies()["https"] == "http://proxy.test:3128"
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_download.ssl_context()))
    assert any(isinstance(handler, urllib.request.ProxyHandler) for handler in opener.handlers)
    assert "import certifi" not in open(_download.__file__, encoding="utf-8").read()


def wheel(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return buffer.getvalue()


@pytest.fixture
def fake_pack(server, monkeypatch):
    """Make the `cuda` pack of the lock two small wheels on the local server. It returns the plan function."""
    wheels = {
        "plugin-1.0-py3-none-win_amd64.whl": wheel({"onnxruntime_ep_cuda/onnxruntime_providers_cuda.dll": b"plugin",
                                                    "plugin-1.0.dist-info/LICENSE.txt": b"licence text"}),
        "dep-2.0-py3-none-win_amd64.whl": wheel({"nvidia/cudnn/bin/cudnn64_9.dll": b"dependency",
                                                 "dep-2.0.dist-info/licenses/NOTICE": b"notice"}),
    }
    server.files.update(wheels)
    rows = [{"package": name.split("-")[0], "version": "1", "filename": name, "url": "https://example.com/" + name,
             "sha256": hashlib.sha256(data).hexdigest(), "download_bytes": len(data), "unpacked_bytes": 20}
            for name, data in wheels.items()]
    row = {"library": "onnxruntime_ep_cuda/onnxruntime_providers_cuda.dll", "path_dirs": ["nvidia/cudnn/bin"],
           "download_bytes": sum(len(data) for data in wheels.values()), "unpacked_bytes": 40, "wheels": rows}
    catalog = catalog_module.load_catalog()
    monkeypatch.setitem(catalog.lock["packs"]["cuda-cu13"], "win_amd64", row)
    monkeypatch.setattr(installer, "probe_host", lambda: host(gpu()))
    monkeypatch.setattr(installer, "core_mismatch", lambda catalog: None)
    return lambda: installer.plan_install(["cuda"], index_url=server.url)


def test_install_from_a_local_index(fake_pack, ep_store):
    plan = fake_pack()
    assert (len(plan.packs), plan.download_bytes, plan.disk_bytes) == (1, plan.packs[0].download_bytes, 40)
    assert plan.packs[0].licence_url.startswith("https://")
    events = []
    result = installer.install(plan, progress=events.append, verify=False)
    assert (result.ok, result.failed, result.cancelled) == (("cuda",), (), ())
    folder = ep_store / "cuda-cu13" / "0.2.0"
    manifest = store.read_manifest("cuda-cu13", "0.2.0")
    assert (folder / manifest["library"]).read_bytes() == b"plugin" and manifest["path_dirs"] == ["nvidia/cudnn/bin"]
    assert (folder / "licenses" / "plugin" / "LICENSE.txt").read_bytes() == b"licence text"
    assert (folder / "licenses" / "dep" / "NOTICE").read_bytes() == b"notice"
    assert ["nvidia/cudnn/bin/cudnn64_9.dll", 10, hashlib.sha256(b"dependency").hexdigest()] in manifest["files"]
    assert not list((ep_store / ".partial").glob("*")) and not list((ep_store / ".staging").glob("*"))
    assert {event.phase for event in events} == {"download", "unpack"} and events[-1].key == "cuda"
    catalog = catalog_module.load_catalog()
    assert store.pack_state(catalog, "cuda", gpu(), "gpu:10de:2484:0")[0] == "installed_unverified"
    (folder / manifest["library"]).write_bytes(b"changed size")
    assert store.pack_state(catalog, "cuda", gpu(), "gpu:10de:2484:0")[:2] == ("not_ready", "files")
    assert installer.install(plan, verify=False).ok == ("cuda",)  # an installed pack folder is not written again
    assert (folder / manifest["library"]).read_bytes() == b"changed size"


def test_install_from_a_folder_with_no_network(fake_pack, server, ep_store, tmp_path):
    plan = fake_pack()
    for name in ("plugin-1.0-py3-none-win_amd64.whl", "dep-2.0-py3-none-win_amd64.whl"):
        (tmp_path / name).write_bytes(server.files[name])
    server.files.clear()
    assert installer.install(plan, from_dir=tmp_path, verify=False).ok == ("cuda",)
    assert (tmp_path / "dep-2.0-py3-none-win_amd64.whl").exists()  # the folder of the user keeps its files
    installer.remove("cuda-cu13")
    assert not (ep_store / "cuda-cu13").exists()
    (tmp_path / "dep-2.0-py3-none-win_amd64.whl").write_bytes(b"not the wheel")
    assert installer.install(plan, from_dir=tmp_path, verify=False).failed[0][:2] == ("cuda", "hash-mismatch")
    assert installer.install(plan, from_dir=tmp_path / "none", verify=False).failed[0][:2] == ("cuda", "offline")


def test_a_wheel_member_that_leaves_the_folder_is_refused(fake_pack, server, ep_store, monkeypatch):
    bad = wheel({"../evil.dll": b"x"})
    name = "dep-2.0-py3-none-win_amd64.whl"
    server.files[name] = bad
    row = catalog_module.load_catalog().lock["packs"]["cuda-cu13"]["win_amd64"]["wheels"][1]
    monkeypatch.setitem(row, "sha256", hashlib.sha256(bad).hexdigest())
    result = installer.install(fake_pack(), verify=False)
    assert result.failed[0][1] == "failed" and "unsafe member" in result.failed[0][2]
    assert not (ep_store / "cuda-cu13").exists() and not (ep_store.parent / "evil.dll").exists()
    assert not list((ep_store / ".staging").glob("*"))


def test_a_long_store_path_is_refused_with_the_reason(fake_pack, tmp_path, monkeypatch):
    root = tmp_path / ("s" * (store.PATH_LIMIT - len(str(tmp_path)) - 40))
    monkeypatch.setenv(store.STORE_VARIABLE, str(root))
    (code, message), = [failure[1:] for failure in installer.install(fake_pack(), verify=False).failed]
    assert code == "path-guard" and store.STORE_VARIABLE in message and not (root / "cuda-cu13").exists()


def test_cancel_and_core_mismatch(fake_pack, monkeypatch):
    cancel = threading.Event()
    cancel.set()
    assert installer.install(fake_pack(), cancel=cancel, verify=False).cancelled == ("cuda",)
    monkeypatch.setattr(installer, "core_mismatch", lambda catalog: "onnxruntime 1.30.0 is installed. Run `uv sync`.")
    plan = fake_pack()
    assert "uv sync" in plan.warnings[-1] and installer.install(plan, verify=False).failed[0][1] == "core-mismatch"


def test_plan_selections(fake_pack, monkeypatch):
    assert installer.plan_install("cpu-only") == InstallPlan()
    assert [pack.ep_key for pack in installer.plan_install("all-compatible").packs] == ["trt-rtx", "cuda"]
    assert [pack.ep_key for pack in installer.plan_install("recommended").packs] == ["trt-rtx"]
    assert installer.plan_install(["cpu"]).packs == () and "needs no pack" in installer.plan_install(["cpu"]).warnings[0]
    monkeypatch.setattr(installer, "probe_host", lambda: host(gpu(cc="7.5")))
    assert [pack.ep_key for pack in installer.plan_install("all-compatible").packs] == ["cuda"]
    assert "cannot run on this host" in installer.plan_install(["trt-rtx"]).warnings[0]
    for key in ("openvino", "qnn", "tensorrt"):
        with pytest.raises(EpRequestError):
            installer.plan_install([key])


def test_a_field_test_ep_needs_the_opt_in_for_a_plan(ep_store):
    """ADR-Z5X7: `directml` (built-in) is refused with no opt-in and never in `all-compatible`; `--field-test` plans it."""
    with pytest.raises(EpUnavailableError, match="field test") as caught:
        installer.plan_install(["directml"])
    assert caught.value.hint == "Run `skellytracker-eps install directml --field-test`."
    assert "directml" not in [pack.ep_key for pack in installer.plan_install("all-compatible").packs]
    plan = installer.plan_install(["directml"], field_test=True)
    assert plan.packs == () and "needs no pack" in plan.warnings[0] and not (ep_store / "field-test.json").exists()
    store.opt_in_field_test("directml")
    assert installer.plan_install(["directml"]).packs == () and set(store.field_test_opt_ins()) == {"directml"}


def test_download_writes_the_wheels_and_a_manifest(fake_pack, server, tmp_path, monkeypatch):
    catalog = catalog_module.load_catalog()
    for row in catalog.lock["packs"]["cuda-cu13"]["win_amd64"]["wheels"]:
        monkeypatch.setitem(row, "url", server.url + row["filename"])
    dest = installer.download(["cuda"], "win_amd64", tmp_path / "wheels")
    manifest = store.read_json(dest / "manifest.json")
    assert sorted(path.name for path in dest.iterdir()) == ["README.txt", "dep-2.0-py3-none-win_amd64.whl", "manifest.json", "plugin-1.0-py3-none-win_amd64.whl"]
    assert len(manifest["wheels"]) == 2 and manifest["licences"]
    assert installer.install(fake_pack(), from_dir=dest, verify=False).ok == ("cuda",)


def test_gc_and_remove(fake_pack, ep_store, monkeypatch):
    installer.install(fake_pack(), verify=False)
    old = ep_store / "old-pack" / "0.1"
    old.mkdir(parents=True)
    (old / "pack.json").write_text("{}", encoding="utf-8")
    (ep_store / ".partial").mkdir(exist_ok=True)
    (ep_store / ".partial" / "a.part").write_bytes(b"1")
    store.write_json(ep_store / "refs" / "gone.json", {"kind": "environment", "prefix": str(ep_store / "no-such-folder"),
                                                       "last_seen": int(time.time()), "packs": [["old-pack", "0.1"]]})
    result = installer.gc()
    assert result.removed_refs == ("gone",) and result.removed_packs == () and result.removed_partials == 0
    assert len(list((ep_store / "refs").glob("*.json"))) == 1  # the ref of this consumer
    later = time.time() + 40 * 86400
    result = installer.gc(now=later)
    assert result.removed_packs == ("old-pack/0.1",) and result.removed_partials == 1 and not old.exists()
    assert (ep_store / "cuda-cu13" / "0.2.0" / "pack.json").exists()  # the ref of this consumer names it
    installer.remove(consumer="environment")
    assert not list((ep_store / "refs").glob("*.json"))
    old.mkdir(parents=True)
    assert installer.gc(force=True).removed_packs == ("old-pack/0.1",)
    monkeypatch.setattr(multiprocessing, "parent_process", lambda: object())
    with pytest.raises(RuntimeError, match="main process"):
        installer.gc()


def test_two_installers_wait_for_the_store_lock():
    order = []

    def hold():
        with store.store_lock():
            order.append("first in")
            time.sleep(0.3)
            order.append("first out")

    thread = threading.Thread(target=hold)
    thread.start()
    while not order:
        time.sleep(0.01)
    with store.store_lock():
        order.append("second in")
    thread.join()
    assert order == ["first in", "first out", "second in"]


def test_path_guard():
    assert store.path_guard(store.store_root() / "p" / "1", ["a.dll"]) is None
    reason = store.path_guard(store.store_root() / "p" / "1", ["d/" + "x" * store.PATH_LIMIT])
    assert store.STORE_VARIABLE in reason and str(os.sep) not in reason.replace(store.STORE_VARIABLE, "")
