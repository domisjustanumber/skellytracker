"""The EP catalog loader, `recommend()` for each hardware class, `select_precision()` and `run_devices()`."""

import dataclasses
import json
import pickle

import pytest

from skellytracker.core import eps
from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps import recommendation
from skellytracker.core.eps import store
from skellytracker.core.errors import EpRequestError, EpUnavailableError
from skellytracker.tests.hw_fakes import GIB, fake_pack, gpu, host

RTX = gpu()
GTX_1650 = gpu(cc="7.5", vram=4 * GIB, device_id=0x1F91, name="NVIDIA GeForce GTX 1650")
INTEL = gpu("intel", cc=None, driver="32.0.101.7088", vram=None, bus="0000:00:02.0", device_id=0xA780, name="UHD 770")


@pytest.fixture(autouse=True)
def ep_store(tmp_path, monkeypatch):
    monkeypatch.setenv(store.STORE_VARIABLE, str(tmp_path / "eps"))
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "win_amd64")
    return tmp_path / "eps"


def test_catalog_keys_and_reserved_keys():
    catalog = eps.load_catalog()
    assert catalog.keys() == ("trt-rtx", "cuda", "coreml", "directml", "cpu")
    assert [catalog.ep_status(key) for key in catalog.keys()] == ["ready", "ready", "ready", "field-test", "ready"]
    for key in ("trt", "openvino", "qnn", "migraphx", "vitisai"):
        with pytest.raises(EpRequestError, match="reserved"):
            catalog.ep(key)
    with pytest.raises(EpRequestError, match="not an EP key"):
        catalog.ep("tensorrt")
    assert catalog.ort_untested(catalog.pack("trt-rtx"), "1.31.1") and not catalog.ort_untested(catalog.pack("trt-rtx"))
    assert not catalog.ort_untested(catalog.pack("cuda"))


@pytest.mark.parametrize(("key", "options"), [
    ("cuda", {"prefer_nhwc": "1", "use_tf32": "0", "arena.max_mem": "2147483648"}),
    ("trt-rtx", {"enable_cuda_graph": "0"}), ("coreml", {"MLComputeUnits": "CPUAndGPU"}), ("cpu", {}), ("cpu", None),
])
def test_allowed_options(key, options):
    assert eps.load_catalog().check_options(key, options) == tuple(sorted((options or {}).items()))


@pytest.mark.parametrize(("key", "options"), [
    ("cuda", {"device_id": "0"}), ("trt-rtx", {"device_id": "0"}), ("coreml", {"device_id": "0"}), ("cpu", {"device_id": "0"}),
    ("cuda", {"use_tf32": "banana"}), ("cuda", {"fuse_conv_bias": "1"}), ("cuda", {"arena.max_mem": "0"}),
    ("cuda", {"arena.max_mem": "-5"}), ("cuda", {"prefer_nhwc": 1}), ("trt-rtx", {"nv_runtime_cache_path": "x"}),
    ("trt-rtx", {"bogus_key": "1"}), ("cpu", {"session.intra_op_num_threads": "4"}), ("coreml", {"MLComputeUnits": "all"}),
])
def test_refused_options(key, options):
    with pytest.raises(EpRequestError):
        eps.load_catalog().check_options(key, options)


@pytest.mark.parametrize(("driver", "branch"), [("582.78", 580), ("576.88", 575), ("610.88", 610), ("580.65.06", 580), (None, None)])
def test_driver_branch(driver, branch):
    assert catalog_module.driver_branch(driver) == branch


CASES = [
    # the host, the installed packs, the row, the chosen EP, the skipped EPs, the offer kinds
    (host(gpu(brand="tesla"), os_name="Linux"), ("cuda",), "nvidia-datacenter-r580", "cuda", (), ()),
    (host(RTX, INTEL), ("trt-rtx", "cuda"), "nvidia-cc80-r580", "trt-rtx", (), ()),
    (host(RTX, INTEL), ("cuda",), "nvidia-cc80-r580", "cuda", ("trt-rtx",), ("add-pack",)),
    (host(RTX), (), "nvidia-cc80-r580", "cpu", ("trt-rtx", "cuda"), ("add-pack", "add-pack")),
    (host(gpu(cc="8.0")), ("trt-rtx",), "nvidia-cc80-r580", "trt-rtx", (), ()),
    (host(gpu(driver="576.88")), ("trt-rtx", "cuda"), "nvidia-cc80-pre580", "cpu", (), ("update-driver",)),
    (host(gpu(driver="582.78")), ("trt-rtx",), "nvidia-cc80-r580", "trt-rtx", (), ()),
    (host(GTX_1650), ("trt-rtx", "cuda"), "nvidia-cc75-r580", "cuda", (), ()),
    (host(gpu(cc="7.5", driver="566.36")), ("cuda",), "nvidia-cc75-pre580", "cpu", (), ("update-driver",)),
    (host(gpu(cc="6.1")), ("cuda",), "nvidia-pre-turing", "cpu", (), ("none-available",)),
    (host(INTEL), (), "intel-gpu", "cpu", (), ()),
    (host(gpu("amd", cc=None, device_id=0x73BF)), (), "amd-windows", "cpu", (), ("none-available",)),  # `directml` is a field-test EP
    (host(gpu("amd", cc=None, device_id=0x73BF), os_name="Linux"), (), "amd-deferred", "cpu", (), ("none-available",)),
    (host(gpu("other", cc=None)), (), "unknown-gpu", "cpu", (), ()),
    (host(), (), "cpu-only", "cpu", (), ()),
    (host(os_name="Windows", arch="AMD64", native_arch="ARM64"), (), "snapdragon-x", "cpu", (), ()),
    (host(os_name="Darwin", arch="x86_64", native_arch="arm64"), (), "cpu-only", "cpu", (), ()),  # a translated Python
]


@pytest.mark.parametrize(("fake_host", "installed", "row", "chosen", "skipped", "offers"), CASES, ids=[case[2] + "-" + case[3] for case in CASES])
def test_recommend_for_each_hardware_class(fake_host, installed, row, chosen, skipped, offers):
    for key in installed:
        fake_pack(key)
    result = eps.recommend("performance", fake_host)
    assert (result.hardware_class, result.chosen.ep_key) == (row, chosen)
    assert tuple(c.ep_key for c in result.skipped) == skipped and all(c.reason for c in result.skipped)
    assert tuple(offer.kind for offer in result.offers) == offers
    assert result.source.row_id == row and result.source.catalog_revision == eps.load_catalog().revision
    assert result.precision == ("fp32" if chosen == "cpu" else "fp16")
    accuracy = eps.recommend("accuracy", fake_host)
    assert (accuracy.chosen.ep_key, accuracy.precision, accuracy.options, accuracy.hardware_class) == ("cpu", "fp32", (), row)
    never = {"trt", "openvino", "qnn", "migraphx", "vitisai", "directml"}  # reserved keys and the field-test EP
    assert not never & {c.ep_key for c in (result.chosen, *result.skipped)} and not never & {o.ep_key for o in result.offers}


def test_recommend_details():
    fake_pack("trt-rtx")
    fake_pack("cuda")
    best = eps.recommend("performance", host(RTX))
    assert best.chosen.status == "installed_unverified" and best.chosen.device_key == "gpu:10de:2484:0"
    assert best.source.ranking_evidence == "MWY9" and best.options == ()
    turing = eps.recommend("performance", host(GTX_1650))
    assert turing.chosen.status == "installed_unverified" and turing.options == (("prefer_nhwc", "1"),)
    assert turing.source.ranking_evidence is None  # the order is not measured
    for record in (best, turing):  # the record rules
        assert pickle.loads(pickle.dumps(record)) == record and hash(record)  # noqa: S301
        json.dumps(dataclasses.asdict(record))
    offer = eps.recommend("performance", host(gpu(driver="576.88"))).offers[0]
    assert "R580" in offer.note
    assert eps.recommend("performance", host(gpu(cc="6.1"))).offers[0].note == "Use the CPU EP. CUDA 13 has no kernels for this GPU."
    with pytest.raises(ValueError, match="form"):
        eps.recommend("fastest", host())


def test_each_offer_has_a_note():
    """An application shows `InstallOffer.note` for each offer: no offer kind may give None."""
    rows = eps.load_catalog().data["hardware_classes"]
    assert {row["offer"] for row in rows if "offer" in row} <= {"add-pack", "update-driver", "none-available"}
    for row in rows:
        if row.get("offer") in ("update-driver", "none-available"):
            assert isinstance(row.get("note"), str) and row["note"].strip(), row["id"]
    assert recommendation.install_hint("cuda") == "Run `skellytracker-eps install cuda`."  # the note of an add-pack offer


def test_recommended_device_is_the_gpu_with_the_most_vram_then_the_lowest_bus_id():
    fake_pack("cuda")
    small, large = gpu(vram=8 * GIB, bus="0000:01:00.0"), gpu(vram=24 * GIB, bus="0000:02:00.0", device_id=0x2684)
    assert eps.recommend("performance", host(small, large)).chosen.device_key == "gpu:10de:2684:0"
    twins = host(gpu(bus="0000:02:00.0"), gpu(bus="0000:01:00.0"))
    assert eps.recommend("performance", twins).chosen.device_key == "gpu:10de:2484:0"  # rank 0 is bus 01


def test_add_pack_offer_has_the_sizes_of_the_lock():
    (offer,) = eps.recommend("performance", host(GTX_1650)).offers
    lock = eps.load_catalog().pack_lock("cuda-cu13", "win_amd64")
    assert (offer.ep_key, offer.pack_id, offer.download_bytes, offer.disk_bytes) == ("cuda", "cuda-cu13", lock["download_bytes"], lock["unpacked_bytes"])
    assert offer.licence_url.startswith("https://") and "skellytracker-eps install cuda" in offer.note


def test_stale_and_failed_packs_are_skipped(ep_store):
    catalog = eps.load_catalog()
    (ep_store / "cuda-cu13" / "0.1.0").mkdir(parents=True)
    result = eps.recommend("performance", host(GTX_1650))
    assert (result.chosen.ep_key, result.skipped[0].status) == ("cpu", "stale")
    fake_pack("cuda")
    key = store.verdict_key(catalog, catalog.pack("cuda"), GTX_1650, "gpu:10de:1f91:0", None)
    store.write_verdict(key, {"level": "L2", "ok": False, "reason": "the EP lists no device"})
    result = eps.recommend("performance", host(GTX_1650))
    assert (result.chosen.ep_key, result.skipped[0].status, result.skipped[0].reason) == ("cpu", "not_ready", "the EP lists no device")
    store.write_verdict(key, {"level": "L3", "ok": True})
    assert eps.recommend("performance", host(GTX_1650)).chosen.status == "ready"


def test_apple_silicon_gives_coreml_with_fp16(monkeypatch):
    mac = host(os_name="Darwin", arch="arm64")
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "macosx_arm64")
    result = eps.recommend("performance", mac)
    assert (result.hardware_class, result.chosen.ep_key, result.precision, result.chosen.status) == ("apple-silicon", "coreml", "fp16", "ready")


@pytest.mark.parametrize(("key", "artifacts", "expected"), [
    ("cuda", {"fp32", "fp16"}, "fp16"), ("trt-rtx", ["fp32", "fp16"], "fp16"), ("coreml", ("fp16", "fp32"), "fp16"),
    ("cuda", {"fp32"}, "fp32"), ("cpu", {"fp32", "fp16"}, "fp32"), ("cpu", {"fp32"}, "fp32"),
])
def test_select_precision(key, artifacts, expected):
    assert eps.select_precision(key, artifacts) == expected


def test_run_devices_on_two_fake_gpus(monkeypatch):
    large = gpu(vram=24 * GIB, bus="0000:02:00.0", device_id=0x2684, name="RTX 4090")
    old = gpu(cc="6.1", vram=11 * GIB, bus="0000:03:00.0", device_id=0x1B06, name="GTX 1080 Ti")
    monkeypatch.setattr(recommendation, "probe_host", lambda: host(RTX, large, old, INTEL))
    both = eps.run_devices("cuda")
    assert [device.device_key for device in both] == ["gpu:10de:2684:0", "gpu:10de:2484:0"]  # the most VRAM first
    assert both[0] == eps.RunDevice("gpu:10de:2684:0", "0000:02:00.0", "RTX 4090", "0000:02:00.0", 24 * GIB)
    assert [d.device_key for d in eps.run_devices("cuda", "gpu:10de:2484:0")] == ["gpu:10de:2484:0"]
    assert [d.device_key for d in eps.run_devices("trt-rtx", ["gpu:10de:2484:0", "gpu:10de:2684:0"])] == ["gpu:10de:2684:0", "gpu:10de:2484:0"]
    for bad in ("gpu:10de:1b06:0", "gpu:8086:a780:0", "gpu:10de:ffff:0"):  # below the floors, not NVIDIA, not a GPU
        with pytest.raises(EpUnavailableError, match="not a GPU"):
            eps.run_devices("cuda", bad)
    assert eps.run_devices("cpu") == ()
    with pytest.raises(EpUnavailableError):
        eps.run_devices("cpu", "gpu:10de:2484:0")
    with pytest.raises(EpRequestError):
        eps.run_devices("migraphx")
    # `directml` has no vendor floor: each GPU, the most VRAM first (ADR-Z5X7)
    assert [d.device_key for d in eps.run_devices("directml")] == ["gpu:10de:2684:0", "gpu:10de:1b06:0", "gpu:10de:2484:0", "gpu:8086:a780:0"]
    assert [d.device_key for d in eps.run_devices("directml", "gpu:8086:a780:0")] == ["gpu:8086:a780:0"]
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "manylinux_x86_64")
    assert eps.run_devices("directml") == ()  # Windows only


def test_a_field_test_ep_is_never_recommended_also_after_the_opt_in():
    """ADR-Z5X7: an AMD GPU on Windows has the class `amd-windows` with `directml`, but `recommend()` gives the CPU EP."""
    amd = host(gpu("amd", cc=None, device_id=0x73BF, name="Radeon RX 6800"))
    for opted_in in (False, True):
        if opted_in:
            store.opt_in_field_test("directml")
        result = eps.recommend("performance", amd)
        assert (result.hardware_class, result.chosen.ep_key, result.skipped) == ("amd-windows", "cpu", ())
        assert [offer.kind for offer in result.offers] == ["none-available"]
    assert eps.recommend("performance", host(RTX, INTEL)).chosen.ep_key != "directml"
