"""The script that the slow PyInstaller test freezes. It downloads no model.

It prints `SMOKE OK` when each check passes. It does not import the old sidecar loader: it checks
only that the YAML files of the package are in the bundle. It builds one session on the CPU EP from
the probe model, to check the hook of ONNX Runtime. It uses no GPU.
"""

import importlib.resources
import os
import sys
import tempfile


def main() -> int:
    import skellytracker.core  # noqa: F401 - the eager core must import in a frozen app
    from skellytracker.core import eps, metrics, system
    from skellytracker.core.eps.cli import main as eps_cli

    os.environ.setdefault("SKELLYTRACKER_EP_STORE", os.path.join(tempfile.mkdtemp(), "eps"))
    host = system.probe_host()
    environment = system.probe_environment()
    metrics.LiveSampler().sample([os.getpid()])
    out = os.path.join(tempfile.mkdtemp(), "status.ini")
    assert eps_cli(["status", "--format", "ini", "--out", out]) == 0, "status failed"
    assert open(out, "rb").read(2) == bytes([0xFF, 0xFE]), "status.ini has no BOM"
    assert "onnxruntime" not in sys.modules, "status imported onnxruntime"
    assert eps.recommend("accuracy").chosen.ep_key == "cpu"
    package = importlib.resources.files("skellytracker.core")
    assert package.joinpath("eps", "ep_catalog.yaml").is_file() and package.joinpath("eps", "ep_lock.yaml").is_file()
    schemas = [item.name for item in package.joinpath("model_zoo", "landmark_schemas").iterdir() if item.name.endswith(".yaml")]
    assert schemas, "the landmark schema files are not in the bundle"
    runtime = system.probe_runtime()
    assert runtime.ort_version is not None, runtime.probe_errors
    from skellytracker.core.eps import _probe_model
    from skellytracker.core.eps.installer import core_mismatch, installed_ort

    assert installed_ort() is not None and core_mismatch(eps.load_catalog()) is None, "no ONNX Runtime metadata"
    session, report = eps.build_session(_probe_model.model_bytes(), execution_provider="cpu")
    session.run(None, {"x": _probe_model.probe_input()})
    if sys.platform == "win32":
        import windowsml  # noqa: F401 - the import loads its DLL from `windowsml/lib`

        assert "DmlExecutionProvider" in runtime.ep_names, runtime.ep_names
    print(f"frozen={environment.frozen} gpus={len(host.gpus)} ort={runtime.ort_version} schemas={len(schemas)} used_ep={report.used_ep}")
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
