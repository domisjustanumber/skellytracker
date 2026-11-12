# 9NW0 — EP keys from the EP catalog; a run takes EP options; a whole-EP failure raises; CPU nodes are reported

**Status:** accepted, 2026-11-12 (user).

## Decision

1. **EP keys.** The EP catalog in `core/eps/` owns the EP keys. v2 keys: `trt-rtx` (TensorRT for
   RTX), `cuda`, `coreml` and `cpu`. These keys are reserved, and a request for one raises with the
   reason: `trt` (classic TensorRT, a separate EP), `directml`, `openvino` (deferred: discrete Intel
   GPUs only), `qnn`, `migraphx` and `vitisai`. The pipeline spec links to the catalog. The example
   key `tensorrt` of [ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) item 12 is `trt-rtx`.
2. **EP options.** A run takes an EP key and a mapping `ep_options` of strings to strings. A
   `detector` node can give its own `execution_provider` and `ep_options`. The CLI takes
   `--ep <key>` and `--ep-option <name>=<value>` (repeatable). The catalog lists the allowed option
   names and values of each EP. `eps.build_session()` refuses a name or a value that the catalog
   does not list, before it calls ONNX Runtime.
3. **Recommended forms.** `eps.recommend(form)` with `form` `performance` or `accuracy` gives a
   concrete EP key and its options. `performance` is the fastest EP of the host that is ready.
   `accuracy` is `cpu`. The caller (freemocap, the CLI) resolves the form and passes the key and the
   options. The pipeline has no EP policy (ADR-7NY2 item 12 stays). When `recommend()` skips a
   candidate that is not ready, its result names the candidate and the reason. That is a choice of
   the caller, not a fallback.
4. **A whole-EP failure raises.** skellytracker never runs a session on another EP than the
   requested EP. `eps.build_session()` builds the ONNX Runtime session with `enable_fallback=0`, so
   the Python wrapper of ONNX Runtime does not build the session again on the CPU. It then checks
   that the requested EP is the first provider of the session and has at least one node. It raises
   before frame 0:
   - `EpUnavailableError` when the pack is not installed, does not register, or lists no device;
   - `SessionCreationError` when the EP does not start or has no node, with the text of ONNX Runtime;
   - `VRAMExhaustionError` when the GPU memory is exhausted at build or warm-up.
   An EP failure during a run raises from `process_batch`. The EP does not change during a run.
5. **CPU nodes are allowed and reported.** `session.disable_cpu_ep_fallback` stays `0`.
   `session.record_ep_graph_assignment_info=1` is set for each session. The session report gives
   the requested EP, the options, the node count of each EP, the CPU node count and the CPU op
   types. When the CPU node count is not zero, the run gives the warning `ep_partial_placement` one
   time for each session, with these counts. The timing header `execution` block holds the CPU node
   count and the CPU op types.
6. **CLI exit codes.** 3: an EP is not available. 4: a session was not created. 5: the GPU memory is
   exhausted. Each error prints one line on stderr.
7. **The NMS graph.** The ONNX `NonMaxSuppression` session of the detector node
   ([ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) item 9) requests `cpu`.

## Reason

- The user, in words: "I want to avoid fallback situations where an EP is not installed or fails to
  start entirely and the whole run drops to cpu. Individual nodes dropping to CPU is fine as long as
  that count is reported back." Also: "I want to have loud EP fallback notifications."
- A whole-session CPU fallback is silent today. The Python wrapper of ONNX Runtime catches the
  error of an EP that does not start, prints one line and builds the session on the CPU
  (Evidence).
- The CUDA plugin ignores an unknown option name and an invalid value with no message. The TensorRT
  RTX plugin fails to start on an unknown option name. Only a catalog check catches both.
- A CPU node is not a fault. ONNX Runtime puts a node on the CPU when the EP has no kernel for it,
  or when it computes a shape. The count shows the cost.

## Evidence

- `onnxruntime` 1.31.0, `onnxruntime/python/onnxruntime_inference_collection.py` L682-L697 (the
  retry on the CPU) and L661 (`enable_fallback`).
- Measured on 2026-11-12 on an RTX 3070 with `onnxruntime-ep-nv-tensorrt-rtx-cu13` 0.5.0: the option
  `bogus_key=1` gives "Unknown provider option", and the session runs with 388 nodes on the CPU EP and
  no error. `onnxruntime-ep-cuda13` 0.3.0 accepts `use_tf32=banana` and runs with TF32 on.
- The same host: the CUDA plugin puts 3 `Clip` nodes of the fp16 `rtmw-wholebody133` artifact (opset
  11) on the CPU EP, and no node of the fp32 artifacts.

## Alternatives rejected

- **A strict session (`session.disable_cpu_ep_fallback=1`).** The user: too strict. It refuses a
  model with one CPU node.
- **A list of allowed CPU op types for each EP.** It refuses a model with another op type, and a
  count reports the cost.
- **A warning for a whole-EP failure** (`ep_fallback` of
  [ADR-8NVD](8NVD-pipeline-api-warnings-and-catalog.md) item 6). The user wants no run on another
  EP.
- **CPU nodes in the report only, with no warning.** The user chose the warning: a count in a report
  is easy to miss.
