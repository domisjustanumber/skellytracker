"""`build_session()`: build one ONNX Runtime session on the requested EP, with its `SessionReport`.

`run_session()` runs one call of a session. `run_preprocess()` runs one call of a preprocess graph,
and `run_bound()` runs the model session on its output in device memory. An out-of-memory error of ONNX Runtime at the build, at
the warm-up run or during a call is a `VRAMExhaustionError`. No code retries the call or changes the
batch.

skellytracker never runs a session on an other EP than the requested EP. A node of the model can
run on the CPU EP: `SessionReport.cpu_nodes` and `cpu_op_types` report it. `build_session()` serves
the new code only. The caller fills `ModelRef` from the sidecar: this module reads no sidecar.
"""

import os
import time
from collections.abc import Mapping

import numpy as np

from skellytracker.core._hardware.sanitize import sanitize_text
from skellytracker.core.eps import gate, registration, store
from skellytracker.core.eps.catalog import EpCatalog, load_catalog
from skellytracker.core.eps.recommendation import ep_gpus, install_hint
from skellytracker.core.eps.records import USABLE_STATES, ModelRef, SessionReport
from skellytracker.core.errors import EpRequestError, EpUnavailableError, SessionCreationError, VRAMExhaustionError
from skellytracker.core.system.host import physical_cores, probe_host

CPU_EP = "CPUExecutionProvider"
OOM_MARKS = ("out of memory", "cudamalloc", "alloc failed", "failed to allocate", "bfcarena", "available memory", " oom")
DTYPES = {"tensor(float)": np.float32, "tensor(float16)": np.float16, "tensor(double)": np.float64, "tensor(uint8)": np.uint8,
          "tensor(int8)": np.int8, "tensor(int32)": np.int32, "tensor(int64)": np.int64, "tensor(bool)": np.bool_}


def assignment(session) -> tuple[tuple[tuple[str, int], ...], int, tuple[str, ...]]:
    """The node count of each EP, the CPU node count and the CPU op types of a session."""
    counts: dict[str, int] = {}
    cpu_ops: set[str] = set()
    for subgraph in session.get_provider_graph_assignment_info():
        nodes = list(subgraph.get_nodes())
        counts[subgraph.ep_name] = counts.get(subgraph.ep_name, 0) + len(nodes)
        if subgraph.ep_name == CPU_EP:
            cpu_ops |= {node.op_type for node in nodes}
    return tuple(sorted(counts.items())), counts.get(CPU_EP, 0), tuple(sorted(cpu_ops))


def zero_inputs(session) -> dict:
    """One zero tensor for each input of a session. A dimension with no fixed size is 1."""
    return {item.name: np.zeros([dim if isinstance(dim, int) and dim > 0 else 1 for dim in item.shape],
                                dtype=DTYPES.get(item.type, np.float32)) for item in session.get_inputs()}


def cpu_thread_count(cpu_threads: int | None = None) -> int:
    """The intra-op thread count of a session on the built-in CPU EP: `cpu_threads`, or the default for None.

    The default is half of the physical cores of the host, at least 1. The sessions thus leave cores
    free for the camera capture and the application (ADR-HB8Z). When the OS gives no physical core
    count, the default is half of the logical CPUs of `os.cpu_count()`, at least 1. Raise
    `EpRequestError` for 0, a negative value, a bool or a value that is not an integer.
    """
    if cpu_threads is None:
        return max(1, (physical_cores() or os.cpu_count() or 1) // 2)
    if isinstance(cpu_threads, bool) or not isinstance(cpu_threads, int) or cpu_threads < 1:
        raise EpRequestError(f"cpu_threads must be a positive integer or None, not {cpu_threads!r}")
    return cpu_threads


def open_session(model, catalog: EpCatalog, key: str, options: Mapping[str, str], gpu=None, device_key: str | None = None,
                 strict: bool = False, cpu_threads: int | None = None):
    """Register the EP and create the session with no retry on the CPU. `strict` refuses each node on the CPU EP.

    `cpu_threads` sets the intra-op threads of a session with no GPU. With None, ONNX Runtime
    uses its default. A session on a GPU (a GPU pack or `directml`) uses one intra-op thread and
    takes the ONNX Runtime device of the GPU `gpu`, never a `device_id` option.
    """
    import onnxruntime

    row, pack = catalog.ep(key), catalog.pack(key)
    ep_name = registration.ensure_registered(key).ep_name
    session_options = onnxruntime.SessionOptions()
    session_options.log_severity_level = 3
    session_options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
    session_options.add_session_config_entry("session.record_ep_graph_assignment_info", "1")
    if strict and ep_name != CPU_EP:
        session_options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    options = dict(options)
    providers, ep_device_id = None, None
    if gpu is None:
        providers = [(ep_name, options)]
        if cpu_threads is not None:
            session_options.intra_op_num_threads = cpu_threads
            session_options.inter_op_num_threads = 1
    else:
        session_options.intra_op_num_threads = 1  # attributes: a session config entry has no effect for them
        session_options.inter_op_num_threads = 1
        cache_option = row["options"].get("cache_path_option")
        if cache_option:
            cache = store.cache_root() / key / pack["version"] / str(gpu.driver_version)
            cache.mkdir(parents=True, exist_ok=True)
            options[cache_option] = str(cache)
        device = registration.ort_device(ep_name, gpu, int(device_key.rsplit(":", 1)[1]))
        if device is None:
            raise EpUnavailableError(f"The EP '{key}' lists no device for the GPU {device_key}.", install_hint(key))
        ep_device_id = dict(device.ep_options).get("device_id")
        session_options.add_provider_for_devices([device], options)  # never `providers=[name]` for a plugin EP
    model = model if isinstance(model, bytes) else os.fspath(model)
    return onnxruntime.InferenceSession(model, sess_options=session_options, providers=providers, enable_fallback=0), ep_name, ep_device_id


def _is_out_of_memory(text: str) -> bool:
    return any(mark in text.lower() for mark in OOM_MARKS)


def run_session(session, output_names, inputs: Mapping) -> list:
    """Run one call of a session. Each call of the generic detectors and of a pipeline run uses this function.

    An error of ONNX Runtime with an out-of-memory text raises `VRAMExhaustionError`, with no
    retry. Each other error passes through with no change.
    """
    try:
        return session.run(output_names, inputs)
    except Exception as error:  # noqa: BLE001 - ONNX Runtime raises its own error types
        _raise_out_of_memory(error)
        raise


def _raise_out_of_memory(error: Exception) -> None:
    text = sanitize_text(str(error))[:2000]
    if _is_out_of_memory(text):
        raise VRAMExhaustionError(f"The GPU memory is exhausted during a call of the session: {text}") from error


def run_preprocess(preprocess, frames, index: np.ndarray, theta: np.ndarray | None = None, device_type: str = "cuda", device_id: int = 0):
    """Run one call of a preprocess graph with IO bindings. Return its output `tensor`: an `OrtValue` in device memory.

    `preprocess` is a session of `build_preprocess_graph`. `frames` holds the `OrtValue` of each
    input `frame_<i>` (from `upload_frame`). `index` (int64) and `theta` (float32, for
    `affine_crop` only) are host arrays. `tensor` stays in the memory of `device_type` and
    `device_id`. The call waits for the outputs, so its time is the time of the graph. The binding
    lives for this call only. An out-of-memory error raises `VRAMExhaustionError`, as in `run_session`.
    """
    try:
        bound = preprocess.io_binding()
        for slot, frame in enumerate(frames):
            bound.bind_ortvalue_input(f"frame_{slot}", frame)
        bound.bind_cpu_input("index", np.ascontiguousarray(index, np.int64))
        if theta is not None:
            bound.bind_cpu_input("theta", np.ascontiguousarray(theta, np.float32))
        bound.bind_output("tensor", device_type, device_id)
        preprocess.run_with_iobinding(bound)
        bound.synchronize_outputs()
        return bound.get_outputs()[0]
    except Exception as error:  # noqa: BLE001 - ONNX Runtime raises its own error types
        _raise_out_of_memory(error)
        raise


def run_bound(session, input_name: str, output_names, tensor) -> list:
    """Run one call of a model session on the `OrtValue` `tensor` of `run_preprocess`, with no host copy of it.

    The model outputs come back as host arrays, as `run_session` gives them, with the same
    out-of-memory mapping. The binding lives for this call only.
    """
    try:
        bound = session.io_binding()
        bound.bind_ortvalue_input(input_name, tensor)
        for name in output_names:
            bound.bind_output(name)  # host memory
        session.run_with_iobinding(bound)
        return bound.copy_outputs_to_cpu()
    except Exception as error:  # noqa: BLE001 - ONNX Runtime raises its own error types
        _raise_out_of_memory(error)
        raise


def upload_frame(image: np.ndarray, ep_device_id: str | int | None, device_type: str = "cuda"):
    """Copy a host frame (BGR `uint8` `(H, W, 3)`) to GPU memory. Return an `onnxruntime.OrtValue`.

    `ep_device_id` is the `SessionReport.ep_device_id` of a session on `cuda` or `trt-rtx`: the
    CUDA device id. None is device 0. `device_type` `cpu` gives an `OrtValue` in host memory: the
    tests run the GPU preprocess on the CPU EP with it, and a run on `directml` gives it to the graph,
    because a DML session does not see a frame of the device type `dml`.
    """
    import onnxruntime

    return onnxruntime.OrtValue.ortvalue_from_numpy(np.ascontiguousarray(image), device_type, int(ep_device_id or 0))


def _failure(error: Exception, report: SessionReport, what: str) -> Exception:
    text = sanitize_text(str(error))[:2000]
    if _is_out_of_memory(text):
        return VRAMExhaustionError(f"The GPU memory is exhausted at the {what} of the session on '{report.requested_ep}': {text}", report)
    return SessionCreationError(f"The session on the EP '{report.requested_ep}' failed at its {what}: {text}", report)


def build_session(model: str | os.PathLike | bytes, *, execution_provider: str, ep_options: Mapping[str, str] | None = None,
                  device_key: str | None = None, model_ref: ModelRef | None = None, cpu_threads: int | None = None):
    """Build a session on `execution_provider`. It returns `(onnxruntime.InferenceSession, SessionReport)`.

    `model` is the bytes or the path of an ONNX file. `execution_provider` is a concrete key of the
    EP catalog. `ep_options` maps option names to string values. `device_key` selects the GPU of a
    GPU EP. With no `device_key`, the session uses the GPU with the most VRAM that the EP can use;
    on a tie, the GPU with the lowest PCI bus id. The session takes the ONNX Runtime EP device of
    that GPU (the PCI ids, then the LUID on Windows), never the `device_id` option: for `directml`,
    `device_id` is the DXGI adapter index, which can name an other GPU (ADR-Z5X7).

    `cpu_threads` is the intra-op thread count of a session on the built-in CPU EP `cpu`. With
    None, it is the default of `cpu_thread_count()`: half of the physical cores, at least 1. The
    inter-op thread count of that session is 1. `SessionReport.cpu_threads` gives the applied
    count. A session on a GPU (a GPU pack or `directml`) uses one intra-op thread and one inter-op
    thread, and ignores `cpu_threads`. A session on an other built-in EP, for example `coreml`, ignores it and keeps
    the default of ONNX Runtime.

    It raises, before frame 0:

    - `EpRequestError` for a reserved or unknown key, for an option that the catalog does not
      list, also `device_id`, and for a `cpu_threads` that is not a positive integer, before a
      call of ONNX Runtime;
    - `EpUnavailableError` when the pack is not installed, does not register or lists no device,
      for a `field-test` EP with no opt-in in the EP store, and for an EP on a GPU with no reviewed
      row and no passed quick check on this PC, or with a quick check that failed here (`gate.py`);
    - `SessionCreationError` when the EP does not start, is not the first provider or has no node;
    - `VRAMExhaustionError` when the GPU memory is exhausted at the build or at the warm-up run.

    The session is not built again on the CPU. The warm-up is one run on zero inputs.
    """
    catalog = load_catalog()
    key = execution_provider
    row = catalog.ep(key)
    options = catalog.check_options(key, ep_options)
    pack = catalog.pack(key)
    threads = cpu_thread_count(cpu_threads)  # the same check for each EP
    if pack is not None or row["ep_name"] != CPU_EP:
        threads = None  # only a session on the built-in CPU EP uses it
    gpu = None
    if catalog.device_row(key) is None:
        if device_key is not None:
            raise EpRequestError(f"The EP '{key}' takes no device key.")
        state, _, reason = store.pack_state(catalog, key)
        if state not in USABLE_STATES:  # for example a `field-test` EP with no opt-in (ADR-Z5X7)
            raise EpUnavailableError(f"The EP '{key}' is not available: {reason}.", install_hint(key))
    else:  # only a GPU EP reads the host: an NVML call wakes the GPU of a hybrid laptop
        host = probe_host()
        usable = ep_gpus(catalog, key, host)
        if device_key is None and usable:  # the first GPU that the check rule lets run, else the first GPU
            device_key = next((d for d, g in usable if gate.rule_passes(catalog, key, g, host.os_name)), usable[0][0])
        gpu = dict(usable).get(device_key)
        state, _, reason = store.pack_state(catalog, key, gpu, device_key, host.os_build)
        if device_key is not None and gpu is None:
            reason = f"'{device_key}' is not a GPU that the EP can use on this host"
        if gpu is None or state not in USABLE_STATES:
            raise EpUnavailableError(f"The EP '{key}' is not available: {reason}.", install_hint(key))
        gate.require(catalog, key, gpu, host.os_name)
        if state not in ("ready", "builtin"):
            store.warn_once(f"{key}:{state}", f"The EP '{key}' is in the state {state}: {reason}.")
    precisions = () if model_ref is None else model_ref.precisions
    report = SessionReport(
        requested_ep=key, used_ep=None, ep_name=pack["ep_name"] if pack else row["ep_name"], ort_version=catalog.ort_version,
        catalog_revision=catalog.revision, device_kind="gpu" if row["gpu"] else "cpu",
        pack_id=pack["id"] if pack else None, pack_version=pack["version"] if pack else None, device_key=device_key,
        device_name=None if gpu is None else gpu.name,
        gpu_uuid=None if gpu is None or gpu.nvidia is None else gpu.nvidia.uuid, gpu_key=None if gpu is None else gpu.key,
        ep_options=options, precision=precisions[0] if len(precisions) == 1 else None,
        artifact_sha256=None if model_ref is None else model_ref.artifact_sha256, cpu_threads=threads,
    )
    start = time.perf_counter_ns()
    try:
        session, ep_name, ep_device_id = open_session(model, catalog, key, dict(options), gpu, device_key, cpu_threads=threads)
    except (EpRequestError, EpUnavailableError):
        raise
    except Exception as error:  # noqa: BLE001 - ONNX Runtime raises its own error types
        raise _failure(error, report, "build") from error
    build_ns = time.perf_counter_ns() - start
    start = time.perf_counter_ns()
    try:
        session.run(None, zero_inputs(session))
    except Exception as error:  # noqa: BLE001
        raise _failure(error, report, "warm-up") from error
    warmup_ns = time.perf_counter_ns() - start
    nodes_by_ep, cpu_nodes, cpu_op_types = assignment(session)
    import onnxruntime

    first = session.get_providers()[0]
    used = next((name for name in catalog.keys() if (catalog.pack(name) or catalog.ep(name))["ep_name"] == first), None)
    fields = dict(vars(report), used_ep=used, ep_device_id=ep_device_id, ort_version=onnxruntime.__version__, nodes_by_ep=nodes_by_ep, cpu_nodes=cpu_nodes,
                  cpu_op_types=cpu_op_types, build_ns=build_ns, warmup_ns=warmup_ns)
    report = SessionReport(**fields)
    if first != ep_name or dict(nodes_by_ep).get(ep_name, 0) < 1:
        raise SessionCreationError(
            f"The session did not start on the EP '{key}': its first provider is {first}, and the EP {ep_name} has "
            f"{dict(nodes_by_ep).get(ep_name, 0)} nodes.", report)
    return session, report
