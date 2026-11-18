"""Tests of `tools/onnx_stack.py`: the rules of `check`, the solve on a recorded snapshot, and `apply`."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from skellytracker.core import eps
from skellytracker.core.eps import evidence
from skellytracker.core.eps.catalog import EpCatalog

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("onnx_stack", ROOT / "tools" / "onnx_stack.py")
onnx_stack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(onnx_stack)


def rows(catalog: EpCatalog, os_names=("Windows", "Linux")) -> tuple[dict, ...]:
    return tuple({"ep": key, "os": os_name, "gpu": "10de:2484", "set": evidence.set_hash(catalog), "source": "maintainer", "result": "pass"}
                 for key in ("trt-rtx", "cuda") for os_name in os_names)


def test_check_passes_with_maintainer_evidence_for_each_os():
    catalog = eps.load_catalog()
    assert onnx_stack.check(catalog, rows(catalog)) == []


def test_check_needs_evidence_for_each_os_and_for_this_set():
    catalog = eps.load_catalog()
    assert onnx_stack.check(catalog, rows(catalog, ("Windows",))) == [
        f"{key}: no maintainer evidence on Linux for the set {evidence.set_hash(catalog)[:12]}" for key in ("trt-rtx", "cuda")]
    old = tuple(dict(row, set="0" * 64) for row in rows(catalog))
    field = tuple(dict(row, source="field") for row in rows(catalog))
    assert len(onnx_stack.check(catalog, old)) == 4 and len(onnx_stack.check(catalog, field)) == 4


def test_a_vendor_range_blocks_without_an_exception():
    data = copy.deepcopy(eps.load_catalog().data)
    data["ort_core"]["version"] = "1.31.1"
    catalog = EpCatalog(data=data, lock=eps.load_catalog().lock, revision="r")
    problems = onnx_stack.check(catalog, rows(catalog))
    assert len(problems) == 1 and problems[0].startswith("trt-rtx: ONNX Runtime 1.31.1 is outside the range")
    for exception in ({"reason": "no entry", "ort_version": "1.31.1"}, {"entry": "XXXX"}, {"entry": "XXXX", "ort_version": "1.31.0"}):
        data["eps"]["trt-rtx"]["packs"][0]["ort"]["exception"] = exception  # an entry and this ONNX Runtime version are necessary
        assert len(onnx_stack.check(catalog, rows(catalog))) == 1
    data["eps"]["trt-rtx"]["packs"][0]["ort"]["exception"] = {"entry": "XXXX", "ort_version": "1.31.1"}
    assert onnx_stack.check(catalog, rows(catalog)) == []


def test_check_reports_a_malformed_evidence_row_and_does_not_raise():
    catalog = eps.load_catalog()
    good = rows(catalog)
    bad = (dict(good[0], gpu="10DE:2484"), {k: v for k, v in good[0].items() if k != "result"}, "not a row",
           dict(good[0], catalog_package=1), dict(good[0], source="other", set="s"))
    problems = onnx_stack.check(catalog, (*good, *bad, dict(good[0], catalog_package="1.8.0")))
    assert problems == [f"ep_evidence.yaml row {n}: the field {fields} is missing or not valid" for n, fields in (
        (4, "gpu"), (5, "result"), (6, "ep, os, gpu, set, source, result"), (7, "catalog_package"), (8, "set, source"))]


def test_the_set_hash_follows_the_wheels_and_the_core_only():
    catalog = eps.load_catalog()
    data, lock = copy.deepcopy(catalog.data), copy.deepcopy(catalog.lock)
    data["eps"]["cuda"]["description"] = "other text"
    assert evidence.set_hash(EpCatalog(data=data, lock=lock, revision="r")) == evidence.set_hash(catalog)
    lock["packs"]["cuda-cu13"]["win_amd64"]["wheels"][0]["sha256"] = "0" * 64
    assert evidence.set_hash(EpCatalog(data=data, lock=lock, revision="r")) != evidence.set_hash(catalog)
    lock["packs"]["openvino"]["win_amd64"]["wheels"][0]["sha256"] = "0" * 64  # a test pack is not in the set
    changed = evidence.set_hash(EpCatalog(data=data, lock=lock, revision="r"))
    lock["packs"]["openvino"]["win_amd64"]["wheels"][0]["sha256"] = "1" * 64
    assert evidence.set_hash(EpCatalog(data=data, lock=lock, revision="r")) == changed


# A recorded snapshot, written by hand. 1.23.0 has no windowsml build, 1.22.0 has no CPython 3.13 wheel for
# macOS arm64 (only a free-threaded one) and only a windowsml pre-release, and 1.21.0 obeys each rule.
LINUX, MAC, WINDOWS = "manylinux_2_28_x86_64", "macosx_14_0_arm64", "win_amd64"
SNAPSHOT = {
    "schema": 1,
    "pages": {},
    "wheels": {
        "onnxruntime": [*(f"onnxruntime-{v}-cp313-cp313-{p}.whl" for v in ("1.20.0", "1.21.0", "1.23.0") for p in (LINUX, MAC)),
                        f"onnxruntime-1.22.0-cp313-cp313-{LINUX}.whl", f"onnxruntime-1.22.0-cp313-cp313t-{MAC}.whl",
                        f"onnxruntime-1.19.0-cp313-cp313-{LINUX}.whl", "onnxruntime-1.21.0.tar.gz"],
        "onnxruntime-windowsml": [f"onnxruntime_windowsml-{v}-cp313-cp313-{WINDOWS}.whl" for v in ("1.20.0.1", "1.21.0.5", "1.22.0.3")],
        "windowsml": [f"windowsml-{v}-py3-none-{WINDOWS}.whl" for v in ("1.0", "1.1", "1.2rc1")],
        "gpu-ep": [f"gpu_ep-{v}-py3-none-{p}.whl" for v in ("1.0", "2.0") for p in (LINUX, WINDOWS)],
    },
    "windowsml_requires_dist": {
        "1.0": ['onnxruntime-windowsml==1.20.0.1; extra == "with-ort"'],
        "1.1": ['comtypes>=1.4.0; platform_system == "Windows"', 'onnxruntime-windowsml==1.21.0.5; extra == "with-ort"'],
        "1.2rc1": ['onnxruntime-windowsml==1.22.0.3; extra == "with-ort"'],
    },
}
CATALOG = {
    "indexes": {"pypi": "https://pypi.test/simple/", "feed": "https://feed.test/simple/"},
    "platforms": ["win_amd64", "manylinux_x86_64"],
    "eps": {
        "gpu": {"kind": "plugin", "packs": [{"id": "gpu-pack", "package": "gpu-ep", "version": "1.0", "index": "feed",
                                              "ort": {"vendor_tested": ["1.20", "1.22"]}, "status": "ready"}]},
        "cpu": {"kind": "builtin"},
        "old": {"kind": "reserved", "test_packs": [{"id": "test-pack", "package": "test-ep", "version": "1.0", "index": "pypi"}]},
    },
}
CURRENT = {"onnxruntime": "1.20.0", "onnxruntime-windowsml": "1.20.0.1", "windowsml": "1.0", "packs": {"gpu-pack": "1.0"}}
NEW_PACK = "gpu-pack 2.0: ep_catalog.yaml records no ONNX Runtime claim for this pack version"


def solve(snap=SNAPSHOT, catalog=CATALOG, current=CURRENT, allow_prerelease=False):
    return onnx_stack.solve(copy.deepcopy(snap), copy.deepcopy(catalog), copy.deepcopy(current), allow_prerelease)


def test_solve_gives_one_result_for_one_snapshot_and_says_why_each_newer_set_fails():
    first = solve()
    assert json.dumps(solve(), sort_keys=True) == json.dumps(first, sort_keys=True)
    assert first["bump"] and first["proposed"] == {"onnxruntime": "1.21.0", "onnxruntime-windowsml": "1.21.0.5", "windowsml": "1.1",
                                                   "packs": {"gpu-pack": "1.0"}}
    assert first["rejected"] == [
        NEW_PACK,
        "ONNX Runtime 1.23.0: gpu-pack: no claim covers ONNX Runtime 1.23.0, and no exception names it: "
        "1.0 {'vendor_tested': ['1.20', '1.22']}; no windowsml release pins onnxruntime-windowsml 1.23.0",
        "ONNX Runtime 1.22.0: onnxruntime 1.22.0 has no cp313 wheel for macosx_arm64; "
        "windowsml 1.2rc1 is a pre-release (allow it with --allow-prerelease)"]
    assert solve(snap=dict(SNAPSHOT, pages={"x": "y"}))["snapshot_sha256"] != first["snapshot_sha256"]


def test_a_release_needs_plain_onnxruntime_and_windowsml_and_each_wheel():
    snap = copy.deepcopy(SNAPSHOT)
    snap["wheels"]["onnxruntime"].append(f"onnxruntime-1.22.0-cp313-cp313-{MAC}.whl")
    assert solve(snap, allow_prerelease=True)["proposed"]["windowsml"] == "1.2rc1"
    snap["wheels"]["onnxruntime-windowsml"].remove(f"onnxruntime_windowsml-1.22.0.3-cp313-cp313-{WINDOWS}.whl")
    result = solve(snap, allow_prerelease=True)
    assert result["proposed"]["onnxruntime"] == "1.21.0"
    assert result["rejected"][-1] == ("ONNX Runtime 1.22.0: onnxruntime-windowsml 1.22.0.3 (the pin of windowsml 1.2rc1) "
                                      "has no cp313 wheel for win_amd64")


def test_a_vendor_range_blocks_the_solve_and_an_exception_lifts_it(capsys):
    catalog = copy.deepcopy(CATALOG)
    pack = catalog["eps"]["gpu"]["packs"][0]
    pack["ort"] = {"vendor_tested": ["1.20", "1.20"]}
    result = solve(catalog=catalog)
    assert not result["bump"] and result["proposed"] == CURRENT
    assert result["rejected"][-1] == ("ONNX Runtime 1.21.0: gpu-pack: no claim covers ONNX Runtime 1.21.0, and no exception names it: "
                                      "1.0 {'vendor_tested': ['1.20', '1.20']}")
    onnx_stack.print_solution(result)
    assert "\nno bump\n" in capsys.readouterr().out
    for exception in ({"reason": "no entry", "ort_version": "1.21.0"}, {"entry": "XXXX"}, {"entry": "XXXX", "ort_version": "1.23.0"}):
        pack["ort"]["exception"] = exception  # an exception lifts the block only for the version that it names
        assert not solve(catalog=catalog)["bump"]
    pack["ort"]["exception"] = {"entry": "XXXX", "ort_version": "1.21.0"}
    assert solve(catalog=catalog)["proposed"]["onnxruntime"] == "1.21.0"
    pack["ort"] = {"verified_by_us": ["1.20.0"]}
    assert not solve(catalog=catalog)["bump"]


def test_a_claim_in_newer_versions_makes_a_newer_pack_version_a_candidate():
    catalog = copy.deepcopy(CATALOG)
    pack = catalog["eps"]["gpu"]["packs"][0]
    pack["newer_versions"] = [{"version": "2.0", "ort": {"verified_by_us": ["1.21.0"]}}, {"version": "3.0", "ort": {"verified_by_us": ["1.21.0"]}}]
    result = solve(catalog=catalog)
    assert result["bump"] and result["proposed"] == dict(solve()["proposed"], packs={"gpu-pack": "2.0"})
    assert result["rejected"][0] == "gpu-pack 3.0 has no wheel for manylinux_x86_64, win_amd64" and NEW_PACK not in result["rejected"]
    pack["newer_versions"][0]["ort"] = {"verified_by_us": ["1.20.0"]}  # the newest ONNX Runtime comes first, then the newest pack
    result = solve(catalog=catalog)
    assert result["proposed"]["onnxruntime"] == "1.21.0" and result["proposed"]["packs"] == {"gpu-pack": "1.0"}
    assert result["rejected"][-1] == "ONNX Runtime 1.21.0: gpu-pack 2.0: the claim {'verified_by_us': ['1.20.0']} does not cover ONNX Runtime 1.21.0"
    pack["ort"] = {"vendor_tested": ["1.20", "1.20"]}
    result = solve(catalog=catalog)
    assert result["bump"] and result["proposed"] == dict(CURRENT, packs={"gpu-pack": "2.0"})  # a pack bump alone is a bump


def test_only_the_pinned_windowsml_pre_release_is_allowed_without_the_flag():
    snap = copy.deepcopy(SNAPSHOT)
    snap["wheels"]["windowsml"] = [f"windowsml-1.0rc1-py3-none-{WINDOWS}.whl"]
    snap["windowsml_requires_dist"] = {"1.0rc1": SNAPSHOT["windowsml_requires_dist"]["1.0"]}
    current = dict(CURRENT, windowsml="1.0rc1")
    result = solve(snap, current=current)
    assert result["proposed"] == current and not result["bump"]
    assert solve(snap, current=dict(CURRENT, windowsml="0.9"))["proposed"] is None


def test_snapshot_reads_each_page_and_the_metadata_from_the_pinned_windowsml():
    site = {f"https://pypi.test/simple/{name}/": "".join(f'<a href="https://files.test/{f}">{f}</a>' for f in SNAPSHOT["wheels"][name])
            for name in ("onnxruntime", "onnxruntime-windowsml", "windowsml")}
    site["https://feed.test/simple/gpu-ep/"] = "".join(f'<a href="../../{f}#sha256=0">{f}</a>' for f in SNAPSHOT["wheels"]["gpu-ep"])
    site |= {onnx_stack.PYPI_JSON.format(package="windowsml", version=v): json.dumps({"info": {"requires_dist": lines}})
             for v, lines in SNAPSHOT["windowsml_requires_dist"].items()}
    asked = []
    snap = onnx_stack.snapshot(CATALOG, "1.1", lambda url: asked.append(url) or site[url].encode())
    assert snap["wheels"]["onnxruntime"] == sorted(f for f in SNAPSHOT["wheels"]["onnxruntime"] if f.endswith(".whl"))
    assert snap["wheels"]["gpu-ep"] == sorted(SNAPSHOT["wheels"]["gpu-ep"]) and "test-ep" not in snap["wheels"]
    assert list(snap["windowsml_requires_dist"]) == ["1.1", "1.2rc1"]
    assert not any("windowsml/1.0/json" in url for url in asked)


def work_tree(tmp_path: Path, line_end: str = "\n") -> Path:
    for path in (Path("pyproject.toml"), onnx_stack.CATALOG):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / path).read_bytes().decode("utf-8").replace("\r\n", "\n")
        (tmp_path / path).write_bytes(text.replace("\n", line_end).encode("utf-8"))
    return tmp_path


def real_current(root: Path) -> dict:
    return onnx_stack.current_set((root / "pyproject.toml").read_text(encoding="utf-8"),
                                  yaml.safe_load((root / onnx_stack.CATALOG).read_text(encoding="utf-8")))


def test_apply_writes_each_pin_and_keeps_the_line_ends(tmp_path, capsys):
    root = work_tree(tmp_path, "\r\n")
    current = real_current(root)
    proposed = dict(current, **{"onnxruntime": "9.9.9", "onnxruntime-windowsml": "9.9.9.1", "windowsml": "8.0"})
    solution = {"current": current, "proposed": proposed, "bump": True}
    before = {path: (root / path).read_bytes() for path in (Path("pyproject.toml"), onnx_stack.CATALOG)}
    assert onnx_stack.apply(solution, root, dry_run=True) == 0
    assert '+    "windowsml[with-ort]==8.0 ;' in capsys.readouterr().out
    assert all((root / path).read_bytes() == data for path, data in before.items())
    assert onnx_stack.apply(solution, root) == 0
    assert "uv lock" in capsys.readouterr().out
    assert real_current(root) == proposed
    pyproject = (root / "pyproject.toml").read_bytes().decode("utf-8")
    catalog = (root / onnx_stack.CATALOG).read_bytes().decode("utf-8")
    assert '"onnxruntime==9.9.9 ; sys_platform' in pyproject and "\n" not in pyproject.replace("\r\n", "")
    assert yaml.safe_load(catalog)["ort_core"]["windows"]["version"] == "9.9.9.1" and "\n" not in catalog.replace("\r\n", "")
    assert len(pyproject) - len(before[Path("pyproject.toml")].decode("utf-8")) == sum(
        len(proposed[k]) - len(current[k]) for k in onnx_stack.PINS)


NEWER = ('        newer_versions:\n'
         '          - {version: "0.3.0", ort: {verified_by_us: ["1.31.1"]}, dependency_wheels: {nvidia-cublas: "13.9.0.1", '
         'nvidia-cuda-runtime: {manylinux_x86_64: "13.5.1"}}}\n'
         '          - {version: "0.4.0", ort: {verified_by_us: ["1.32.0"]}}\n')


def test_apply_moves_the_claim_of_a_new_pack_version_into_the_pack_row(tmp_path, capsys):
    root = work_tree(tmp_path, "\r\n")
    path = root / onnx_stack.CATALOG
    anchor = '        ort: {verified_by_us: ["1.30.0"]}\r\n'
    path.write_bytes(path.read_bytes().decode("utf-8").replace(anchor, anchor + NEWER.replace("\n", "\r\n")).encode("utf-8"))
    for version, ort in (("0.3.0", ["1.31.1"]), ("0.4.0", ["1.32.0"])):
        current = real_current(root)
        proposed = dict(current, packs=dict(current["packs"], **{"cuda-cu13": version}))
        assert onnx_stack.apply({"current": current, "proposed": proposed, "bump": True}, root) == 0
        assert "tools/ep_catalog.py --refresh" in capsys.readouterr().out
        text = path.read_bytes().decode("utf-8")
        cuda = yaml.safe_load(text)["eps"]["cuda"]["packs"][0]
        assert real_current(root) == proposed and cuda["ort"] == {"verified_by_us": ort} and "\n" not in text.replace("\r\n", "")
        assert [wheel["version"] for wheel in cuda["dependency_wheels"]] == [{"manylinux_x86_64": "13.5.1"}, "13.9.0.1", "9.27.0.42"]
        assert [row["version"] for row in cuda.get("newer_versions", [])] == ([] if version == "0.4.0" else ["0.4.0"])
    assert "newer_versions" not in text and yaml.safe_load(text)["eps"]["trt-rtx"]["packs"][0]["version"] == "0.5.0"


def test_apply_refuses_another_working_tree_and_a_text_that_is_not_there_one_time(tmp_path):
    root = work_tree(tmp_path)
    current = real_current(root)
    solution = {"current": current, "proposed": dict(current, onnxruntime="9.9.9"), "bump": True}
    assert onnx_stack.apply(dict(solution, current=dict(current, windowsml="0.1")), root) == 1
    assert onnx_stack.apply(dict(solution, bump=False), root) == 0
    assert onnx_stack.apply(dict(solution, proposed=dict(current, onnxruntime="9.9.9", packs={})), root) == 1
    assert onnx_stack.apply(dict(solution, proposed=dict(current, packs=dict(current["packs"], **{"cuda-cu13": "0.3.0"}))), root) == 1
    path = root / onnx_stack.CATALOG
    path.write_text(path.read_text(encoding="utf-8") + f'# old: version: "{current["onnxruntime"]}", windows:\n', encoding="utf-8")
    before = (root / "pyproject.toml").read_bytes()
    with pytest.raises(ValueError, match="2 times"):
        onnx_stack.apply(solution, root)
    assert (root / "pyproject.toml").read_bytes() == before
    assert real_current(root) == current
