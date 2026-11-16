"""The test pack step of `selftest()` on fake hosts: the device list is checked only on a host with an Intel device."""

import pytest

from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps import installer, self_test, verification
from skellytracker.core.eps.records import InstallResult

NO_DEVICE = ("EpUnavailableError: The EP pack 'openvino' registers, but the EP 'OpenVINOExecutionProvider' lists no device "
             "on this host. ONNX Runtime lists these devices: CPUExecutionProvider on cpu 1022:0000.")
NOT_REGISTERED = "EpUnavailableError: The EP pack 'openvino' does not register: the library did not load"
# The PCI vendor ids of the hardware devices that ONNX Runtime lists on each fake host.
INTEL_CPU = (0x10DE, 0x8086)  # an NVIDIA GPU and an Intel CPU
INTEL_GPU = (0x8086, 0x1022)  # an Intel GPU and an AMD CPU
AMD = (0x10DE, 0x1022)
UNREADABLE = None  # ONNX Runtime did not give its hardware devices


def run_step(monkeypatch, vendor_ids, reason):
    """The `test pack` step of `selftest()` with a fake install and a fake child result. `reason` None is an L2 pass."""
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "win_amd64")
    monkeypatch.setattr(self_test, "_trial", lambda key: "L3")
    monkeypatch.setattr(installer, "install", lambda plan, verify=True: InstallResult(ok=("openvino",)))
    monkeypatch.setattr(verification, "run_child", lambda job: {"level": "L2", "ok": reason is None, "reason": reason,
                                                                 "hardware_vendor_ids": vendor_ids})
    result = self_test.selftest()
    return result.ok, result.steps[-1]


@pytest.mark.parametrize("vendor_ids", [INTEL_CPU, INTEL_GPU, AMD], ids=["intel-cpu", "intel-gpu", "amd"])
def test_a_pack_that_lists_a_device_passes_on_each_host(monkeypatch, vendor_ids):
    assert run_step(monkeypatch, vendor_ids, None) == (True, ("test pack", True, "openvino 1.8.1 registers and lists a device"))


@pytest.mark.parametrize("vendor_ids", [INTEL_CPU, INTEL_GPU], ids=["intel-cpu", "intel-gpu"])
def test_an_intel_host_with_no_device_fails(monkeypatch, vendor_ids):
    ok, (name, step_ok, detail) = run_step(monkeypatch, vendor_ids, NO_DEVICE)
    assert (ok, name, step_ok) == (False, "test pack", False) and "lists no device on this host" in detail


def test_a_host_with_no_intel_device_passes_when_the_pack_registers(monkeypatch):
    assert run_step(monkeypatch, AMD, NO_DEVICE) == (True, (
        "test pack", True, "openvino 1.8.1 registers; this host has no Intel device, so the device list is not checked"))


def test_an_unreadable_hardware_list_keeps_the_strict_rule(monkeypatch):
    ok, (_, step_ok, detail) = run_step(monkeypatch, UNREADABLE, NO_DEVICE)
    assert (ok, step_ok) == (False, False) and "lists no device on this host" in detail
    assert detail.endswith("The hardware device list of ONNX Runtime could not be read, so the step needs a device of the EP.")
    assert run_step(monkeypatch, UNREADABLE, None)[0] is True


def test_hardware_vendor_ids_of_this_host_and_of_a_build_with_no_such_function(monkeypatch):
    from onnxruntime.capi import _pybind_state

    from skellytracker.core.eps import registration

    ids = registration.hardware_vendor_ids()
    assert ids and all(isinstance(vendor, int) for vendor in ids)  # each host has a CPU device
    monkeypatch.delattr(_pybind_state, "get_hardware_devices")
    assert registration.hardware_vendor_ids() is None


@pytest.mark.parametrize("vendor_ids", [INTEL_CPU, AMD], ids=["intel-cpu", "amd"])
def test_a_pack_that_does_not_register_fails_on_each_host(monkeypatch, vendor_ids):
    ok, (_, step_ok, detail) = run_step(monkeypatch, vendor_ids, NOT_REGISTERED)
    assert (ok, step_ok) == (False, False) and "does not register" in detail


def test_a_failed_install_fails(monkeypatch):
    monkeypatch.setattr(installer, "install", lambda plan, verify=True: InstallResult(failed=(("openvino", "hash-mismatch", "bad sha256"),)))
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "win_amd64")
    monkeypatch.setattr(self_test, "_trial", lambda key: "L3")
    result = self_test.selftest()
    assert not result.ok and result.steps[-1] == ("test pack", False, "RuntimeError: hash-mismatch: bad sha256")
