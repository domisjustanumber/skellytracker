# Decision log

This log records the technical decisions for skellytracker that affect more than one module, with
their reasons and evidence. The [spec log](../specs/model-sidecar/decisions/README.md) holds the
decisions of the sidecar spec only ([ADR-GN3D](entries/GN3D-module-decision-logs.md)). The
[pipeline spec log](../specs/pipeline/decisions/README.md) holds the decisions of the pipeline spec
only ([ADR-3SF2](entries/3SF2-pipeline-spec-and-node-workflow.md)). Read this file before you change the spec, a sidecar, the
sidecar code, the agent instructions or the PR workflow. Also read [open-work.md](open-work.md). The
[Rules](#rules) tell you which entries to read.

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. Entries 0002 to 0012, here and in
the spec log, are backfilled. They record decisions made before this log existed, and they cite the original sources.
When a decision changes, add a new entry that supersedes the old entry in full. The body of a
decided entry changes only by the edits that the [Rules](#rules) allow. To write an entry, use
[template.md](template.md).

## Index

### Active

These entries are `accepted`.

| # | Decision | Status |
|---|----------|--------|
| [AMJ8](entries/AMJ8-replace-package-onnx-detectors.md) | Replace the package ONNX detectors with exporter models; no legacy layer; shipped sidecars in `core/model_zoo/`; RTMPose replacements block v2.0.0 | accepted |
| [0XW9](entries/0XW9-entry-points-layout-guard-test-and-session-code.md) | Entry points `detectors` and `pipelines`; `system/`, `metrics/`, `eps/` under an eager `core`; one `eps` guard test; new session code in `core/eps/` | accepted |
| [NHM3](entries/NHM3-phases-to-the-exporter-checkpoint.md) | Phase 0 and phase 1 to the exporter checkpoint; pre-release at the checkpoint; new code beside old; supersedes EM74 | accepted |
| [9NW0](entries/9NW0-ep-keys-options-and-failures.md) | EP keys from the EP catalog; a run takes `ep_options`; a whole-EP failure raises before frame 0; CPU nodes are reported | accepted |
| [N6E8](entries/N6E8-onnxruntime-1-30-on-each-os.md) | Exact pins; Python `==3.13.18`; ONNX Runtime 1.30.0 on each OS, Windows ML build on Windows; same CUDA 13 plugin packs on each OS; supersedes M2C6 | accepted |
| [W5QD](entries/W5QD-pipeline-entries-consolidation.md) | Consolidation of the pipeline entries 7NY2, ZYS9, V7GZ and 0WTV: links to the pipeline spec, and the Python API names that it does not state | accepted |
| [MF2R](entries/MF2R-ep-store-install-and-certification.md) | EP catalog, lock and store; download after the user accepts; the app prompts; `certify()` with a local report; `ep_evidence.yaml`; supersedes 246B | accepted |
| [D8DH](entries/D8DH-sessions-errors-and-the-ready-rule.md) | `core/errors.py`; one exit-code table; an EP pack is ready when installed, current, registered and with a device; no EP variables | accepted |
| [P1F3](entries/P1F3-hardware-probe-devices-and-multi-gpu.md) | Hardware probe fields; `free_vram`; `device_key`; default GPU by VRAM; a run splits its cameras across GPUs; no pre-Turing GPUs | accepted |
| [4WR9](entries/4WR9-params-schema-in-the-node-catalog.md) | `NodeTypeInfo.params_schema` and `NodeTypeInfo.any_from`: the JSON Schema of the params and the inputs that type an `any` output, for an editor | accepted |
| [Y14H](entries/Y14H-certify-suite.md) | Certify suite: one command from a clone at a tag, seven sections in child processes, one private Markdown report; AMD EPs; Linux gate of N6E8 | accepted |
| [Z5X7](entries/Z5X7-field-test-state-and-directml.md) | Field-test EP state: opt-in in the EP store, refused without it, never recommended; `directml` built in on Windows, GPU by ORT device | accepted |
| [XSE7](entries/XSE7-amd-eps-in-the-field-test.md) | AMD EPs in the field test: `migraphx` ROCm packs on Linux, Windows ML `amdgpu` and `migraphx`; field-test packs not in the set hash; ORT 1.29 fallback | accepted |
| [YPH2](entries/YPH2-verdict-key-of-the-own-catalog-entry.md) | The key of a stored verification verdict holds the sha256 of the own EP row, pack row and lock row, not the whole-catalog revision | accepted |
| [P0JZ](entries/P0JZ-certify-contract-in-each-package.md) | `certify(level)` in each package; reports to `skellycertify`; any recorded build is evidence; OS and EP layers | accepted |
| [21BK](entries/21BK-quick-check-local-pass-and-hand-in.md) | Quick check in a child process on the user's pipeline; local pass; hard failures; passive record; hand-in | accepted |
| [K8Q0](entries/K8Q0-platform-rulings-of-2026-11-19.md) | Host facts only in `core/system`, `core/metrics`; ONNX Runtime and its hook through this package; EP page from `status()` | accepted |

### Evidence

These entries are `evidence`: measurements. They are not in the read path. Scan these rows before
you make a measurement ([Rules](#rules)).

| # | Decision | Status |
|---|----------|--------|
| [Z0CC](entries/Z0CC-exporter-coverage-measurements.md) | Exporter coverage measurements of 2026-10: RF-DETR graph checks, RTMDet AP of resize and NMS, COCO id and in-graph cap defects | evidence |
| [X6S9](entries/X6S9-mediapipe-close-from-the-garbage-collector.md) | A MediaPipe landmarker closed by the garbage collector on its own worker thread hangs; the runner and the old detectors close on a new thread | evidence |
| [0YYY](entries/0YYY-host-reader-costs.md) | Host reader costs: first `probe_host()` about 76 ms on Windows; the D3DKMT query joins a LUID to a bus id and finds the second DXGI adapter | evidence |
| [73Q4](entries/73Q4-local-gpu-gate-of-the-ep-api.md) | Local GPU gate on an RTX 3070: L3 and sessions pass on `cuda` and `trt-rtx`; fp16 files have 0 CPU nodes, except 5 stale opset 11 RTMW files; frozen install ok | evidence |
| [GPW6](entries/GPW6-model-gate-of-the-first-models.md) | Model gate of `yolox-person` and `rtmw-wholebody133` at the detector level: parity passes on the CPU EP, `cuda` and `trt-rtx`; batch conversion 0.01 s to 1.02 s | evidence |
| [7E4Z](entries/7E4Z-box-parity-of-the-built-in-with-sfn26.md) | Box parity of `yolox-rtmw-wholebody` with the tracker of `sfn26`: recording script and fixture; test A passes on 200 frames; report B on the CPU EP and `cuda` | evidence |
| [ZGF5](entries/ZGF5-certify-measurements-of-2026-11-18.md) | Certify reports of 2026-11-18/19: source reports, 2 px failure, spread of 10 suite reports, rehearsal clone; XSE7 rehearsal stale | evidence |
| [1SZ9](entries/1SZ9-gpu-preprocess-and-gpu-jpeg-decode-in-the-pipeline-run.md) | GPU preprocess and JPEG decode on an RTX 3070: detector call -35 to -56 %; keypoint-only call on `cuda` slower at 1080p; one exit hang | evidence |
| [FBV5](entries/FBV5-gpu-path-agreement-on-the-freemocap-sample-data.md) | GPU against CPU path on the freemocap sample data: keypoint median / p99 1.18 / 7.55 px, as large as between two EPs | evidence |
| [BP5Y](entries/BP5Y-gpu-huffman-decode-threshold.md) | nvJPEG GPU Huffman threshold 500000 halves `frame.decode` at 1280x720, equal pixels; 0 slows small frames; the exit text | evidence |
| [975Z](entries/975Z-nvimagecodec-one-image-decode-hang.md) | nvImageCodec 0.10.0.9 one-image decode hangs with fewer CUDA streams than threads: 19 of 62 cells; workaround, self-test | evidence |
| [71YY](entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md) | Intel QSV JPEG decode (PyAV, UHD 770): slower than the CPU thread pool to BGR at 2, 4 and 28 CPUs; 4:2:2 loses chroma; not built | evidence |
| [C6A5](entries/C6A5-exit-hang-of-the-cuda-ep-plugin.md) | Exit hang of `cuda-cu13` 0.3.0 on Windows: 9 of 192 long runs; hard end 0 of 60; 1DS telemetry client in the DLL; switch not tested | evidence |
| [58F5](entries/58F5-native-jpeg-numbers-on-the-pinned-versions.md) | Native JPEG numbers on ONNX Runtime 1.30.0, `cuda-cu13` 0.2.0: detector call -35 to -63 %; keypoint-only call on `cuda` +15 to +47 % on the GPU path | evidence |
| [C9ME](entries/C9ME-exit-hang-rate-with-the-telemetry-switch.md) | Exit hang of the minimal reproducer, `cuda-cu13` 0.3.0: 0 of 120 with `ORT_DISABLE_TELEMETRY=1`, 1 of 120 without; not separated (p = 1.0) | evidence |

### Proposed

These entries wait for a decision of the user. Section is the spec section of the change, or `none`
when the change has no one section. The spec change proposals of the sidecar spec are in the
[spec log](../specs/model-sidecar/decisions/README.md#proposed).

| # | Decision | Section | Status |
|---|----------|---------|--------|

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work and the repository state are in [open-work.md](open-work.md). The spec defects are
in the [open work of the spec log](../specs/model-sidecar/decisions/open-work.md). The
implementation-stage work is in the [implementation plan](../specs/sidecar-implementation-plan.md).

## Rules

- Read the Active entries that apply to your task. Then you do not repeat a settled question. Before
  you make a measurement, scan the rows of the Evidence table of each log, and read the entries that
  apply. Then you do not repeat a completed measurement. The Evidence entries are not in the read
  path ([ADR-J9QT](entries/J9QT-evidence-table-off-the-read-path.md)). Read a Proposed entry only for spec work in its section, or when a skill
  tells you to. Read an entry of [historical.md](historical.md) only to find the reason for a
  decision ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- The body of an entry that is not `proposed` changes only by four edits: a link or anchor repair, a
  typo that does not change the meaning, the redaction of private data, and a change of ID with the
  repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._` at the end of the
  entry, for example `re-ID from XXXX` ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)). For a
  change of ID, the renamed entry gets `re-ID from XXXX`, and each repaired entry gets
  `citation repair`. Add these two lines only to an entry that is on `development`. A plain-text
  old path in a decided entry, a script or a vector-file comment stays, and means the same file at
  its new path. A path of an exporter repo stays
  ([ADR-2XW6](entries/2XW6-process-entries-consolidation.md)).
- An entry in a commit that is not pushed to a remote can change in that commit, in each part. Make
  the correction and report it to the user. Do not write a new entry for it, and do not ask. The
  four edits apply from the first push
  ([ADR-C3E5](entries/C3E5-one-place-for-the-form-of-a-question.md)).
- A decision that a document or code refers to must be in an entry. "This log" in an older entry or
  in the Rules means all logs ([ADR-2XW6](entries/2XW6-process-entries-consolidation.md)).
- An absorb document is one of these: the spec (the sidecar spec and the pipeline spec), the root or a nested `AGENTS.md`
  ([ADR-GN3D](entries/GN3D-module-decision-logs.md)), the skills, the model addition workflow, the exporter
  guide, the templates of `specs/model-sidecar/templates/`, the Rules of this file with
  [template.md](template.md), and the docstring of a tool in `tools/` for the rules that it checks
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)). A test in `tools/tests/` or in
  `skellytracker/tests/` is a tool here: its docstring states the rules that it checks.
  `pyproject.toml` is an absorb document for a rule that a test checks. Its `absorbed into` link
  stands beside the link of that test ([ADR-99FH](entries/99FH-tests-and-pyproject-as-absorb-documents.md)).
  From the implementation stage, the docstring of a public module of the package is an absorb
  document for the rules of the API of that module ([ADR-W823](entries/W823-absorb-in-the-commit-group-that-states-the-rules.md)).
  The spec includes the `notes` of its vector files. An accepted entry is absorbed when the absorb
  documents together state all of its rules. Open work of the entry does not stop the absorb when
  `open-work.md` or the implementation plan states that work in full. A link to the entry is not
  enough ([ADR-5EVP](entries/5EVP-absorb-across-documents.md)).
- Absorb at landing. The commit group that writes or lands an entry, or that writes the rules of an
  entry into the absorb documents, absorbs the entry in its last commit when the absorb documents
  state all of its rules. This applies in each log, in each skill and without a skill. If an absorb
  document does not state a rule, the entry stays `accepted`. Do not ask the user
  ([ADR-W823](entries/W823-absorb-in-the-commit-group-that-states-the-rules.md)).
- The status `absorbed into` has one link for each heading that states a rule of the entry. Link a
  heading one time, also when it states two or more rules. Link a file with no anchor only when the
  rule is not under a heading, for example in a tool docstring or a YAML file. When the status
  paragraph is longer than `STATUS_EXEMPTION_LIMIT`, replace the headings of one file with the title
  heading of that file. Start with the file that has the most links. If the paragraph is still too
  long, replace the files of one document, for example the workflow, with the title heading of its
  main file. A commit that renames a heading repairs each status link to that heading. A change from
  a file link to heading links is a link repair
  ([ADR-995P](entries/995P-absorb-status-links-headings.md)).
- The entry that supersedes an old entry restates each rule of the old entry that stays. A link can
  restate a rule. The link must go to a heading of an absorb document, and that heading must state
  the rule. Link the heading of each kept rule that a heading states. Write text only for a changed
  rule and for a kept rule that no heading states ([ADR-W823](entries/W823-absorb-in-the-commit-group-that-states-the-rules.md)). The commit that changes the text under such a heading cites its own entry next to the
  changed rule. That change does not supersede the entry that links the heading
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- Only these status changes are allowed: `proposed` to `accepted` or `rejected`; `accepted` to
  `superseded by XXXX`, `absorbed into <path>#<anchor>` or `done`; `absorbed into <path>#<anchor>`
  to `superseded by XXXX` ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)); and `evidence` to
  `evidence; used by XXXX`, when an accepted entry cites the `evidence` entry for its decision.
  `done` is for an accepted entry that records a one-off action, with no rule that stays, when the
  action is complete. Each status change adds its date and the PR that made it. In the same PR,
  change the status in the index and move the row to the table for the new status
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- `tools/check_decision_log.py` checks the tables, the status forms, the Section cell, the ID
  alphabet and the size limits. Its docstring states them. `tools/check_links.py` checks the links
  and the full-SHA permalinks. A tool is the source of a rule that it checks
  ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. It changes no decision. Write one at the end of the spec-build stage.
- When the read path is at 90% of its limit or more, first absorb each accepted entry whose rules
  the absorb documents state ([ADR-3AM0](entries/3AM0-absorb-at-landing-and-landed-copies.md)). Then
  write each rule that no absorb document states in the absorb document where it belongs, and
  absorb its entry ([ADR-5EVP](entries/5EVP-absorb-across-documents.md)).
- A commit that only makes a workflow, skill, template or tool copy agree with a landed spec entry
  cites that entry. It needs no entry of its own. A new rule is not a copy
  ([ADR-3AM0](entries/3AM0-absorb-at-landing-and-landed-copies.md)).
- Delete an open-work item when the work is done. Put a dated fact in `open-work.md` or in an
  entry, not in `AGENTS.md`.
- Put long evidence in a tracked file in `evidence/` of the log folder, and link to it
  ([ADR-2XW6](entries/2XW6-process-entries-consolidation.md)). A PR that raises a limit
  of `tools/check_decision_log.py` must add an entry.
- An ID changes only on a `re-ID:` line of `tools/check_decision_log.py`, to the ID of a new `--new`
  run. An older entry keeps its lower-case ID in its file name, heading and index row. Do not edit
  older text only to change the case ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
- Until a commit is on `development`, cite its PR number and the file path, not its SHA ([ADR-0027](entries/0027-single-working-branch.md)).
  The `ADR-` prefix is for citations only: a file name, a
  heading, an index row and a status line hold the bare ID. Cite a provisional entry of another repo
  by the repo name, the PR number and the slug. Do not edit a decided entry only to add or move the
  prefix or the link ([ADR-Z05A](entries/Z05A-essential-decision-log-rules.md)).
