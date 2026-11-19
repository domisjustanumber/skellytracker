"""Tests of `tools/ep_catalog.py`: the offline check and the refresh on a recorded PEP 503 page."""

import copy
import hashlib
import importlib.util
import io
import zipfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("ep_catalog", ROOT / "tools" / "ep_catalog.py")
ep_catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ep_catalog)

CATALOG_TEXT = (ep_catalog.EPS / "ep_catalog.yaml").read_text(encoding="utf-8")
PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
UV_LOCK = (ROOT / "uv.lock").read_text(encoding="utf-8")


def load() -> tuple[dict, dict]:
    return yaml.safe_load(CATALOG_TEXT), yaml.safe_load((ep_catalog.EPS / "ep_lock.yaml").read_text(encoding="utf-8"))


def problems(catalog: dict, lock: dict, pyproject: str = PYPROJECT) -> list[str]:
    return ep_catalog.check(catalog, lock, CATALOG_TEXT, pyproject, UV_LOCK)


def test_the_catalog_and_the_lock_pass_offline():
    assert problems(*load()) == []
    assert ep_catalog.main(["--check"]) == 0


def test_the_revision_does_not_depend_on_the_line_ends():
    assert ep_catalog.revision_of(CATALOG_TEXT.replace("\n", "\r\n")) == ep_catalog.revision_of(CATALOG_TEXT)


def break_pin(catalog, lock):
    catalog["ort_core"]["version"] = "1.29.0"


def break_windows_pin(catalog, lock):
    catalog["ort_core"]["windows"]["version"] = "1.30.0"


def break_group(catalog, lock):
    catalog["eps"]["cuda"]["packs"].append(dict(catalog["eps"]["cuda"]["packs"][0], id="cuda-2", exclusive_group="other"))


def break_darwin(catalog, lock):
    catalog["platforms"].append("macosx_arm64")


def break_reserved(catalog, lock):
    catalog["eps"]["openvino"]["packs"] = catalog["eps"]["openvino"]["test_packs"]


def break_evidence(catalog, lock):
    del catalog["hardware_classes"][0]["ranking_evidence"]


def break_candidate(catalog, lock):
    catalog["hardware_classes"][0]["candidates"] = ["openvino", "cpu"]


def break_device_id(catalog, lock):
    catalog["eps"]["cuda"]["options"]["allowed"]["device_id"] = ["0"]


def break_url(catalog, lock):
    wheel = lock["packs"]["trt-rtx-cu13"]["win_amd64"]["wheels"][0]
    wheel["url"] = wheel["url"].replace("https://", "http://")


def break_sha(catalog, lock):
    lock["packs"]["cuda-cu13"]["win_amd64"]["wheels"][0]["sha256"] = "abc"


def break_lock_row(catalog, lock):
    del lock["packs"]["cuda-cu13"]["manylinux_x86_64"]


def break_revision(catalog, lock):
    lock["catalog_revision"] = "0" * 64


def break_successor(catalog, lock):
    catalog["legacy_keys"]["directml"] = ["trt"]  # a reserved key


def break_unknown_successor(catalog, lock):
    catalog["legacy_keys"]["cuda"] = ["trt-rtx", "tensorrt"]


def break_status(catalog, lock):
    catalog["eps"]["directml"]["status"] = "field_test"  # a typo: the opt-in would not apply


def break_newer_version(catalog, lock):
    catalog["eps"]["cuda"]["packs"][0]["newer_versions"] = [{"version": "0.1.0", "ort": {"verified_by_us": ["1.30.0"]}}]


def break_newer_dependency(catalog, lock):
    catalog["eps"]["cuda"]["packs"][0]["newer_versions"] = [{"version": "0.3.0", "ort": {}, "dependency_wheels": {"other": "1.0"}}]


MODEL = {"path": "detectors/m.onnx", "url": "https://example.invalid/m.onnx", "sha256": "0" * 64, "bytes": 1}


def test_a_valid_model_row_passes():
    catalog, lock = load()
    catalog["certification"]["models"] = [MODEL]
    assert problems(catalog, lock) == []


def break_model_path(catalog, lock):
    catalog["certification"]["models"] = [{**MODEL, "path": "../escape.onnx"}]


def break_model_url(catalog, lock):
    catalog["certification"]["models"] = [{**MODEL, "url": "http://example.invalid/m.onnx"}]


def break_model_sha(catalog, lock):
    catalog["certification"]["models"] = [{**MODEL, "sha256": "abc"}]


def break_model_bytes(catalog, lock):
    catalog["certification"]["models"] = [{**MODEL, "bytes": 0}]


def break_windows_ml_name(catalog, lock):
    del catalog["eps"]["amdgpu"]["ep_name"]


def break_plugin_without_route(catalog, lock):
    del catalog["eps"]["amdgpu"]["windows_ml"]


def break_linux_lock_row(catalog, lock):
    del lock["packs"]["migraphx-rocm10.2"]["manylinux_x86_64"]


def test_a_linux_only_pack_needs_no_windows_lock_row_and_a_local_version_is_exact():
    catalog, lock = load()
    pack = catalog["eps"]["migraphx"]["packs"][0]
    assert pack["version"] == "1.0.0+rocm10.2.0" and set(lock["packs"]["migraphx-rocm10.2"]) == {"manylinux_x86_64"}
    assert ep_catalog.pack_platforms(pack, catalog["platforms"]) == ["manylinux_x86_64"] and problems(catalog, lock) == []


def test_a_newer_versions_row_with_a_claim_passes():
    catalog, lock = load()
    catalog["eps"]["cuda"]["packs"][0]["newer_versions"] = [{"version": "0.10.0", "ort": {"verified_by_us": ["1.31.1"]},
                                                              "dependency_wheels": {"nvidia-cublas": "13.9.0.1"}}]
    assert problems(catalog, lock) == []


@pytest.mark.parametrize("change", [break_pin, break_windows_pin, break_group, break_darwin, break_reserved, break_evidence, break_candidate,
                                    break_device_id, break_url, break_sha, break_lock_row, break_revision,
                                    break_successor, break_unknown_successor, break_status, break_newer_version, break_newer_dependency,
                                    break_model_path, break_model_url, break_model_sha, break_model_bytes, break_windows_ml_name,
                                    break_plugin_without_route, break_linux_lock_row],
                         ids=lambda change: change.__name__)
def test_check_finds_each_defect(change):
    catalog, lock = (copy.deepcopy(part) for part in load())
    change(catalog, lock)
    assert len(problems(catalog, lock)) >= 1


def wheel_bytes(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return buffer.getvalue()


FAKE_CATALOG = {
    "indexes": {"test": "https://index.test/simple/"},
    "platforms": ["win_amd64", "manylinux_x86_64"],
    "eps": {"fake": {"kind": "plugin", "packs": [{
        "id": "fake-pack", "package": "fake-ep", "version": "1.0", "index": "test", "ep_name": "FakeExecutionProvider",
        "library": {"win_amd64": "fake.dll", "manylinux_x86_64": "libfake.so"}, "preload_own": ["libown.so"],
        "dependency_wheels": [{"package": "fake-dep", "index": "test", "version": "2.0"},
                              {"package": "fake-rt", "index": "test", "version": {"manylinux_x86_64": "3.0"}}]}]}},
}


def fake_index(tamper: str | None = None, scheme: str = "https") -> dict[str, bytes]:
    """The pages and the files of a fake index. `tamper` names a file whose bytes change after the page is made."""
    files = {
        "fake_ep-1.0-py3-none-win_amd64.whl": wheel_bytes({"fake_ep/fake.dll": b"dll", "fake_ep-1.0.dist-info/LICENSE": b"l"}),
        "fake_ep-1.0-py3-none-manylinux_2_28_x86_64.whl": wheel_bytes({"fake_ep/libfake.so": b"so", "fake_ep/libown.so.1.2.3": b"o"}),
        "fake_dep-2.0-py3-none-win_amd64.whl": wheel_bytes({"dep/bin/dep.dll": b"12345"}),
        "fake_dep-2.0-py3-none-manylinux_2_27_x86_64.whl": wheel_bytes({"dep/lib/libdep.so.2": b"1", "dep/lib/libcublasLt.so.13": b"2"}),
        "fake_rt-3.0-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl": wheel_bytes({"rt/lib/libcudart.so.13": b"3"}),
    }
    site: dict[str, bytes] = {}
    for package in ("fake-ep", "fake-dep", "fake-rt"):
        links = "".join(f'<a href="{scheme}://files.test/{name}#sha256={hashlib.sha256(data).hexdigest()}" data-requires-python=">=3.11">{name}</a>\n'
                        for name, data in files.items() if name.startswith(package.replace("-", "_")))
        site[f"https://index.test/simple/{package}/"] = links.encode()
    for name, data in files.items():
        site[f"https://files.test/{name}"] = data + (b"x" if name == tamper else b"")
    return site


def test_refresh_is_reproducible_on_a_recorded_index(tmp_path):
    site = fake_index()
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first = ep_catalog.refresh(FAKE_CATALOG, "text", tmp_path / "a", site.__getitem__)
    assert ep_catalog.refresh(FAKE_CATALOG, "text", tmp_path / "b", site.__getitem__) == first
    windows, linux = first["packs"]["fake-pack"]["win_amd64"], first["packs"]["fake-pack"]["manylinux_x86_64"]
    assert windows["library"] == "fake_ep/fake.dll" and windows["path_dirs"] == ["dep/bin"]
    assert linux["library"] == "fake_ep/libfake.so" and linux["preload"] == [
        "fake_ep/libown.so.1.2.3", "rt/lib/libcudart.so.13", "dep/lib/libcublasLt.so.13", "dep/lib/libdep.so.2"]
    assert len(linux["wheels"]) == 3  # the wheel of the version map is a Linux wheel only
    assert [wheel["unpacked_bytes"] for wheel in windows["wheels"]] == [4, 5]
    assert windows["download_bytes"] == sum(len(site[wheel["url"]]) for wheel in windows["wheels"])
    assert first["catalog_revision"] == ep_catalog.revision_of("text")


def test_refresh_takes_the_cp313_wheel_and_the_explicit_dependency_preload(tmp_path):
    """ADR-XSE7: a page with one wheel for each Python, a local version, a Linux-only pack and `preload_dependencies`."""
    catalog = {"indexes": {"amd": "https://amd.test/simple/"}, "platforms": ["win_amd64", "manylinux_x86_64"],
               "eps": {"m": {"kind": "plugin", "packs": [{
                   "id": "m-10.0", "package": "m-ep", "version": "1.0.0+rocm10.0.0", "index": "amd", "ep_name": "MEP",
                   "library": {"manylinux_x86_64": "libm-ep.so"}, "preload_dependencies": ["libm_c.so"],
                   "dependency_wheels": [{"package": "m-libs", "index": "amd", "version": "2.17.0+rocm10.0.0"}]}]}}}
    files = {f"m_ep-1.0.0+rocm10.0.0-{tag}-{tag}-manylinux_2_28_x86_64.whl": wheel_bytes({"m_ep/libm-ep.so": tag.encode()})
             for tag in ("cp311", "cp313", "cp314")}
    files["m_libs-2.17.0+rocm10.0.0-py3-none-manylinux_2_28_x86_64.whl"] = wheel_bytes(
        {"m_libs/libm_c.so.3": b"c", "m_libs/libm.so.2017000": b"m", "m_libs/libm_py_3.10.so": b"p"})
    site = {}
    for package in ("m-ep", "m-libs"):  # no sha256 on the page, and `+` as `%2B` in the link, as on the AMD index
        site[f"https://amd.test/simple/{package}/"] = "".join(
            f'<a href="{name.replace("+", "%2B")}">{name}</a>' for name in files if name.startswith(package.replace("-", "_"))).encode()
    site |= {f"https://amd.test/simple/{name.split('-')[0].replace('_', '-')}/{name.replace('+', '%2B')}": data for name, data in files.items()}
    lock = ep_catalog.refresh(catalog, "text", tmp_path, site.__getitem__)
    (row,) = lock["packs"]["m-10.0"].values()
    assert set(lock["packs"]["m-10.0"]) == {"manylinux_x86_64"} and row["preload"] == ["m_libs/libm_c.so.3"]
    assert row["wheels"][0]["filename"] == "m_ep-1.0.0+rocm10.0.0-cp313-cp313-manylinux_2_28_x86_64.whl"
    assert row["wheels"][0]["index_hash"] == "none" and row["wheels"][0]["url"].endswith("%2Brocm10.0.0-cp313-cp313-manylinux_2_28_x86_64.whl")
    catalog["eps"]["m"]["packs"][0]["preload_dependencies"] = []
    assert next(iter(ep_catalog.refresh(catalog, "text", tmp_path, site.__getitem__)["packs"]["m-10.0"].values()))["preload"] == []


def test_refresh_refuses_a_sha_mismatch_and_an_http_url(tmp_path):
    site = fake_index(tamper="fake_dep-2.0-py3-none-win_amd64.whl")
    with pytest.raises(ValueError, match="sha256"):
        ep_catalog.refresh(FAKE_CATALOG, "text", tmp_path, site.__getitem__)
    assert not (tmp_path / "fake_dep-2.0-py3-none-win_amd64.whl").exists()
    with pytest.raises(ValueError, match="https"):
        ep_catalog.refresh(FAKE_CATALOG, "text", tmp_path, fake_index(scheme="http").__getitem__)
    with pytest.raises(ValueError, match="https"):
        ep_catalog.http_get("http://index.test/simple/")
