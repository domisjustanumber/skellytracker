"""Shared ONNX Runtime session utilities: provider resolution, session building and batched runs.

The base ``onnxruntime`` package gives the CPU EP, and the CoreML EP on macOS.
"""

import logging
import sys
import time
from pathlib import Path

import onnxruntime as ort
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


# Re-exported from a backend-free module so consumers (configs, etc.) can import
# the type without pulling onnxruntime into their import graph.
from skellytracker.core.sessions.execution_provider_name import ExecutionProviderName  # noqa: E402


# =============================================================================
# Provider resolution
# =============================================================================

_PROVIDER_EP_NAME: dict[str, str] = {
    "coreml": "CoreMLExecutionProvider",
    "cpu": "CPUExecutionProvider",
}


def auto_detect_provider() -> ExecutionProviderName:
    """Probe available ONNX Runtime providers and return the best one.

    Called when the caller did not specify an execution provider. Probes in
    preference order: coreml (macOS only) → cpu. Never raises — cpu is always
    available.
    """
    available = set(ort.get_available_providers())
    probe_order: list[ExecutionProviderName] = ["coreml", "cpu"]
    for candidate in probe_order:
        ep = _PROVIDER_EP_NAME[candidate]
        if candidate == "coreml" and sys.platform != "darwin":
            continue
        if ep in available:
            logger.info("auto_detect_provider: selected %r (available: %s)", candidate, sorted(available))
            return candidate
    return "cpu"


def require_provider(requested: ExecutionProviderName) -> None:
    """Verify that *requested* is available in the current ONNX Runtime install.

    Called when the caller explicitly specified an execution provider. Raises
    ``SessionCreationError`` if the provider is not registered — there is no
    fallback. This ensures users know immediately when the EP they asked for
    isn't working, rather than silently running on CPU.

    Raises
    ------
    SessionCreationError
        If the requested provider is not in ``ort.get_available_providers()``.
    """
    from skellytracker.core.sessions.session_errors import SessionCreationError

    available = set(ort.get_available_providers())
    ep_name = _PROVIDER_EP_NAME.get(requested)
    if ep_name and ep_name in available:
        return
    raise SessionCreationError(
        f"Requested execution_provider={requested!r} is not available in this "
        f"ONNX Runtime install (available: {sorted(available)}). "
        f"Choose a different provider. No fallback will be used."
    )


# =============================================================================
# Session construction
# =============================================================================


def build_tuned_ort_session(
    *,
    onnx_path: str,
    provider: ExecutionProviderName,
    log_label: str = "model",
    coreml_options: dict | None = None,
) -> ort.InferenceSession:
    """Construct an ORT session with explicit SessionOptions + provider options.

    Args:
        onnx_path: Path to the ONNX model file (caller is responsible for any
                   graph surgery like dynamic-batch rewriting before passing).
        provider: Which execution provider to request.
        log_label: Human-readable label for log messages.
        coreml_options: Provider options for the CoreML EP.
    """
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.intra_op_num_threads = 1
    sess_options.inter_op_num_threads = 1

    providers: list[tuple[str, dict] | str] = []
    if provider == "coreml":
        # CoreML EP uses Metal on Apple Silicon. Dynamic batch dims crash CoreML
        # (SIGSEGV), so callers must use batch_size=1 (RTMPoseSession enforces
        # this via supports_batching=False). fp16 is also unsupported by CoreML.
        if coreml_options:
            providers.append(("CoreMLExecutionProvider", coreml_options))
        else:
            providers.append("CoreMLExecutionProvider")
        providers.append("CPUExecutionProvider")
    else:
        providers.append("CPUExecutionProvider")

    provider_names = [p if isinstance(p, str) else p[0] for p in providers]
    logger.info(
        "Building ORT session: label=%r  provider=%r  providers=%s",
        log_label, provider, provider_names,
    )

    t0 = time.perf_counter()
    session = ort.InferenceSession(
        path_or_bytes=onnx_path,
        sess_options=sess_options,
        providers=providers,
    )
    elapsed_s = time.perf_counter() - t0
    actual = session.get_providers()
    actual_string = ", ".join(map(str, actual))
    logger.info(
        "  [%s] session ready in %.1fs  active providers: %s",
        log_label, elapsed_s, actual_string,
    )
    return session


# =============================================================================
# Batch inference helpers
# =============================================================================


def probe_supports_batch(session: ort.InferenceSession, label: str = "") -> bool:
    """Return True if the session's first input has a dynamic (or > 1) batch dim."""
    try:
        first_input_shape = session.get_inputs()[0].shape
    except Exception:
        return True
    if not first_input_shape:
        return True
    batch_dim = first_input_shape[0]
    if isinstance(batch_dim, str):
        return True
    supports = int(batch_dim) > 1
    if not supports:
        logger.debug(
            f"{label!r} ONNX model has static batch_size={batch_dim}; "
            f"per-image inference will be used."
        )
    return supports


def session_run_batched(
    session: ort.InferenceSession,
    batch: NDArray,
    *,
    input_name: str | None = None,
    output_names: list[str] | None = None,
) -> list[NDArray]:
    """Run an ORT session with a batched input.

    Prefer passing *input_name* and *output_names* (cached at session build
    time) to avoid per-frame graph-metadata traversal overhead.
    """
    if input_name is None:
        input_name = session.get_inputs()[0].name
    if output_names is None:
        output_names = [o.name for o in session.get_outputs()]
    return session.run(output_names, {input_name: batch})


# =============================================================================
# Dynamic-batch ONNX rewriting
# =============================================================================

_DYNBATCH_PARAM = "N"
_DYNBATCH_SUFFIX = ".dynbatch.onnx"


def ensure_dynamic_batch_onnx(
    src_path: str | Path,
    dst_path: str | Path | None = None,
) -> Path:
    """Rewrite an ONNX model to accept dynamic batch sizes.

    Changes ``dim[0]`` from a static ``dim_value=1`` to the symbolic
    ``dim_param="N"`` on the first graph input and all graph outputs.

    **No Reshape surgery is performed.**  Models whose graph contains
    Reshape nodes that hardcode ``batch=1`` will continue to fail.
    For YOLOX-style models see ``_yolox_dynamic_batch.py`` for the full
    Reshape fixup pipeline.

    Parameters
    ----------
    src_path : Path
        Path to the static-batch ONNX model.
    dst_path : Path or None
        Where to write the modified model.  Defaults to
        ``<src_stem>.dynbatch.onnx`` in the same directory.

    Returns
    -------
    Path
        Path to the dynamic-batch model (cached if it already exists).
    """
    import onnx

    src = Path(src_path)
    dst = Path(dst_path) if dst_path else src.with_suffix("").with_suffix(_DYNBATCH_SUFFIX)
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        logger.info(f"Using cached dynamic-batch model: {dst}")
        return dst

    logger.info(f"Rewriting static-batch ONNX → dynamic batch: {src}")
    model = onnx.load(str(src))

    # --- Symbolize batch dim on first input ---
    graph = model.graph
    if graph.input:
        _symbolize_batch_dim(graph.input[0])

    # --- Symbolize batch dim on all outputs ---
    for out in graph.output:
        _symbolize_batch_dim(out)

    onnx.save(model, str(dst))
    logger.info(f"Dynamic-batch model written: {dst}")
    return dst


def _symbolize_batch_dim(value_info) -> None:
    """Replace a hard ``dim_value=1`` on the leading axis with ``dim_param='N'``."""
    tensor_type = value_info.type.tensor_type
    shape = tensor_type.shape
    if not shape.dim:
        return
    leading = shape.dim[0]
    if leading.HasField("dim_value") and leading.dim_value == 1:
        leading.ClearField("dim_value")
        leading.dim_param = _DYNBATCH_PARAM
    elif not leading.HasField("dim_param"):
        leading.dim_param = _DYNBATCH_PARAM

