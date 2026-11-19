"""The child process of the EP verification. Only this process loads the libraries of a pack for a check.

A pack with a library that is missing can end the process with no Python exception. Thus the
checks run in a `spawn` child, and the parent reads the exit code.
"""

import numpy as np

from skellytracker.core._hardware.sanitize import sanitize_text


def judge(ops_by_ep: dict[str, set[str]], ep_name: str, max_abs_diff: float | None, atol: float) -> str | None:
    """The reason why a trial session fails; `None` for a pass. A built session alone is not a pass."""
    others = sorted(name for name in ops_by_ep if name != ep_name)
    if others:
        return f"nodes of the probe model are on {', '.join(others)}, not on {ep_name}"
    if not any("Conv" in op for op in ops_by_ep.get(ep_name, ())):
        return f"the node assignment does not show the Conv node on {ep_name}"
    if max_abs_diff is None or not max_abs_diff <= atol:
        return f"the output differs from the CPU EP by {max_abs_diff}, and the limit is {atol}"
    return None


def run(job: dict) -> dict:
    """Level L2: the EP registers and lists the device. Level L3: a trial session on the probe model."""
    result = {"level": "L2", "ok": False, "reason": None, "max_abs_diff": None}
    try:
        import onnxruntime

        from skellytracker.core.eps import _probe_model, registration, session
        from skellytracker.core.eps.catalog import load_catalog

        key, pack, gpu, device_key = job["key"], job["pack"], job["gpu"], job["device_key"]
        result["hardware_vendor_ids"] = registration.hardware_vendor_ids()
        if pack is None:
            ep_name = registration.ensure_registered(key).ep_name
        else:
            ep_name = registration.register_pack(key, pack).ep_name
        if gpu is not None and registration.ort_device(ep_name, gpu, int(device_key.rsplit(":", 1)[1])) is None:
            result["reason"] = f"the EP {ep_name} registers, but it lists no device for the GPU {device_key}"
            return result
        result["ok"] = True
        if job["level"] == "L2":
            return result
        result.update(level="L3", ok=False)
        model, x = _probe_model.model_bytes(), _probe_model.probe_input()
        (reference,) = onnxruntime.InferenceSession(model, providers=["CPUExecutionProvider"]).run(None, {"x": x})
        trial, _, _ = session.open_session(model, load_catalog(), key, {}, gpu, device_key, strict=True)
        (output,) = trial.run(None, {"x": x})
        ops_by_ep: dict[str, set[str]] = {}
        for subgraph in trial.get_provider_graph_assignment_info():
            ops_by_ep.setdefault(subgraph.ep_name, set()).update(node.op_type for node in subgraph.get_nodes())
        diff = float(np.max(np.abs(output.astype(np.float64) - reference.astype(np.float64))))
        result["max_abs_diff"] = None if np.isnan(diff) else diff
        result["reason"] = judge(ops_by_ep, ep_name, result["max_abs_diff"], job["atol"])
        result["ok"] = result["reason"] is None
    except Exception as error:  # noqa: BLE001 - each failure is a result with its reason
        result["reason"] = sanitize_text(f"{type(error).__name__}: {error}")[:1000]
    return result


def main(job: dict, connection) -> None:
    from skellytracker.core.eps import gate

    with gate.certification_run():  # the probe runs the EP before the EP has a result
        result = run(job)
    connection.send(result)
    connection.close()
