# Reason codes of skellytracker

This file is the list of the reason codes of `skellytracker.certify()`
([ADR-P0JZ](../decisions/entries/P0JZ-certify-contract-in-each-package.md)).
The contract `report-format.md` of the repository `skellycertify` owns the common codes, and section 5.4
of the contract asks each package to keep the list of its own codes.
Add a code to this list in the commit that adds the code to a check.
The list holds the codes of the levels `quick` and `full`, and the codes of the certify suite
`tools/certify_platform.py` (see [The certify suite](#the-certify-suite)).

## Common codes that this package uses

| Code | Where | Meaning |
|---|---|---|
| `timed-out` | check | The child process of the check ran longer than its time limit. |
| `crashed` | check | The child process ended with no result. `numbers.exit_code` holds its exit code. |
| `hung-at-exit` | check `<name>:exit` | The child process gave its result and did not end. The package stopped it. |
| `cancelled` | check, `evidence.reasons` | The caller set `cancel`. |
| `no-version` | `evidence.reasons` | `package.version` is not a SemVer version. |
| `no-commit` | `evidence.reasons` | The package does not know its commit. |
| `modified-tree` | `evidence.reasons` | The source tree had a change that the commit does not hold, or the package does not know. |

The function `certify()` never writes `gpu-busy`, `bad-output` or `partial-run`. It cannot see the
pipelines of an application. A quick check of a part of the EPs is complete for each EP that it checks.
The certify suite writes `bad-output`, `not-selected` and `partial-run`.

## Codes of this package

| Code | Where | Meaning |
|---|---|---|
| `no-check` | `evidence.reasons`, check `<ep>:jpeg` | The run had no EP to check. For example, each GPU EP of this host has a reviewed row. On `<ep>:jpeg`: no check of the JPEG certification passed or failed. |
| `not-gpu-ep` | check | The EP runs no model on a GPU, for example `cpu`. The quick check compares a GPU EP with the CPU EP. |
| `image-not-passed` | check `<ep>:jpeg-decode`, `<ep>:jpeg-preprocess`, `<ep>:pipeline-<n>` | The JPEG checks or the pipeline timing did not start, because the image check did not pass. |
| a code of `REASONS` | check `<ep>:jpeg-decode`, `<ep>:jpeg-preprocess`, `<ep>:jpeg`, `<ep>:jpeg:<name>` | A reason code of the JPEG certification, for example `component_not_installed` or `over_limit`. The tuple `REASONS` of `core/decode/certification.py` is the list. |
| `gpu-not-usable` | check | The caller named the EP and a GPU with the option `device`, and the EP cannot use that GPU. |
| `ep-<code>` | check | The EP cannot run on this host. `<code>` is the reason code of the EP state, or the state: `ep-os`, `ep-no-device`, `ep-cc-too-low`, `ep-driver-too-old`, `ep-rocm-missing`, `ep-rocm-version`, `ep-not-installed`, `ep-stale`. The quick check installs nothing. |
| `probe-l2-failed` | check `<ep>:probe` | The EP did not register, or it lists no device for the GPU. |
| `probe-l3-failed` | check `<ep>:probe` | The trial session on the probe model failed: a node is not on the EP, or the output differs from the CPU EP. |
| `probe-not-passed` | check `<ep>:image`, `<ep>:jpeg` | The image run or the JPEG certification did not start, because the probe did not pass. |
| `models-missing` | check `<ep>:image`, `cpu:pipeline-<n>` | A model file or an extra of the pipeline is not on this host. No level downloads a model. |
| `outputs-not-comparable` | check `<ep>:image` | The pipeline has no output `boxes` or no output `wholebody`. The comparison needs the two. |
| `no-person-on-cpu` | check `<ep>:image` | The CPU EP found no person on the test image. |
| `people-differ` | check `<ep>:image` | The EP and the CPU EP found a different set of persons. |
| `box-differs` | check `<ep>:image` | A box IoU is less than `box_iou_min`. |
| `scores-differ` | check `<ep>:image` | A keypoint score on the EP is much lower than on the CPU EP. |
| `no-point-to-compare` | check `<ep>:image` | No keypoint has a score of `score_min` or more in the two results. |
| `keypoints-differ` | check `<ep>:image` | A keypoint is farther than `keypoint_box_fraction_max` of the box diagonal from the CPU EP result. |
| `not-finite` | check `<ep>:image` | A value of the EP result is not finite where the CPU EP result is finite. |
| `partial-placement` | check `<ep>:image` | Some nodes of the pipeline ran on the CPU EP, not on the EP. |
| `<ExceptionClass>` | check, `cleanup` | A setup step or a cleanup step raised this exception class, for example `EpUnavailableError` or `DownloadError`. The report never holds the message. |

## Fixed values in `numbers`

| Field | Values | Meaning |
|---|---|---|
| `speed_against_cpu` | `faster`, `slower`, `similar` | The warm call of the pipeline on the EP against the warm call on the CPU EP, on one image (`ep_ms`, `cpu_ms`). `similar` is within 20 %. It is a record only. A check `<ep>:pipeline-<n>` gives the same value from its median against the median of the CPU EP (`against_cpu` is the ratio). |

## Check names

`<ep>` is `<key>@<device>`, for example `cuda@10de-2484-0`: the EP key, and the device key of the GPU
with no `gpu:` and with `-` for `:`. It is `<key>` alone for an EP with no GPU to run on. The name of
an EP check has no `:`. `details.eps.<ep>.device` gives the device key.

| Check | Meaning |
|---|---|
| `<ep>:probe` | The L3 probe of the EP (`verify()`) on the GPU, in a child process. |
| `<ep>:image` | The pipeline on one test image on the EP and on the CPU EP, in a child process, and the comparison. |
| `<ep>:jpeg-decode`, `<ep>:jpeg-preprocess` | Only on `cuda` and `trt-rtx`: the two quick checks of the GPU frame path (`run_jpeg_quick_checks()` of `core/decode/certification.py`), in one child process. They never change `<ep>`. |
| `<ep>` | The quick check of the EP on one GPU. It passes only when `<ep>:probe` and `<ep>:image` pass. |
| `<ep>:probe:exit`, `<ep>:image:exit` | The check `exit` of the contract for a child that gave its result and did not end cleanly. |
| `<ep>:pipeline-1`, `<ep>:pipeline-3`, `<ep>:pipeline-6` | Level `full`: the timing of the pipeline on the EP at 1, 3 and 6 cameras, each in a child process. It is `record-only`, and `numbers` holds the times and the VRAM of the child. A run that raises is `not-run` with the exception class. |
| `<ep>:jpeg` | Level `full`: the outcome of the JPEG certification (`run_jpeg_certification()` of `core/decode/certification.py`) on the EP, in one child process. It is `fail` when a check failed, else `pass` when a check passed. It never changes `<ep>`. |
| `<ep>:jpeg:<name>` | Level `full`: one check of the JPEG certification, with the name, the result, the reason code and the numbers of that check. |
| `cpu:pipeline-<n>`, `cpu:jpeg`, `cpu:jpeg:<name>` | Level `full`: the same checks of the CPU EP. They run first. The CPU EP has no EP check. |
| cleanup `test-image`, `field-test-opt-in` | The delete of the test image that the run downloaded, and the removal of the opt-in that a check that did not pass wrote. |

## The certify suite

The certify suite `tools/certify_platform.py` writes one report file with one module report. That module
report is the report of `certify("full")` of its section 4, with the checks of the suite first. The
sections have these slugs: `checkout` (1), `hardware` (2), `packs` (3) and `full` (4).

### Check names of the suite

Each check name of the suite holds a `:`. Thus it is never the check of an EP on a GPU. The suite
changes each character that a check name cannot hold to `-`.

| Check | Meaning |
|---|---|
| `suite:<slug>` | The result of a section, with the reason code of the section. `numbers` holds `seconds` and `exit_code` of the child process of the section. Section 4 gives `suite:full` only when it gave no module report. |
| `suite:<slug>:<name>` | One check of a section, with its reason code. `numbers` holds its other number fields. |
| `suite:checkout:checkout`, `suite:checkout:python`, `suite:checkout:packages`, `suite:checkout:onnx-stack`, `suite:checkout:telemetry-switch` | Section 1: the git checkout, the Python version and the packages against `uv.lock`, the ONNX Runtime stack, and `ORT_DISABLE_TELEMETRY`. |
| `suite:hardware:probe-host`, `suite:hardware:eps-state`, `suite:hardware:<method>` | Section 2: `probe_host()`, `eps.status()` with `eps.recommend()`, and each OS tool, for example `nvidia-smi` or `cim-video-controller`. |
| `suite:packs:<key>`, `suite:packs:<ep>` | Section 3: the install and the probe of an EP. An EP that runs on one GPU has one check for each GPU, for example `suite:packs:directml@10de-2484-0`. `<ep>` is the name of the EP check of `certify()` for the EP on that GPU. |
| `suite:packs:remove-<package>` | Section 3: the removal of a Windows ML package that the suite installed. A package with no known name gives `remove-<key>`. |
| `suite:<slug>:exit` | The check `exit` of the contract for a section child that gave its result and did not end cleanly. |
| cleanup `remove-windows-packages`, `remove-listed-file`, `delete-work-folder` | The removal of the Windows ML packages, the delete of a downloaded model file, and the delete of the work folder `.certify-work/`. |

### Codes of the certify suite

| Code | Where | Meaning |
|---|---|---|
| `bad-output` | check `suite:<slug>` | The child process of the section gave output that is not a result. |
| `crashed`, `timed-out` | check `suite:<slug>`, `suite:<slug>:exit` | The child process of the section ended with no result, or ran longer than its time limit. On `exit`, the child gave its result first. |
| `hung-at-exit` | check `suite:<slug>:exit` | The child process of the section did not end 20 seconds after its result. The suite stopped it. |
| `not-selected` | check `suite:<slug>` | The option `--only` did not select the section. |
| `cancelled` | check `suite:<slug>`, `evidence.reasons` | The person stopped the run with Ctrl+C, SIGTERM, SIGHUP or SIGBREAK. |
| `unspecified` | check | A `fail` or a `not-run` that has no reason code. |
| `no-isolated-store` | check `suite:packs`, `suite:full` | The isolated EP store of the work folder is not set. The section does not run. |
| `differences-flagged` | check `suite:hardware` | A value of skellytracker differs from the value of an OS tool. The section only records it. |
| `no-git`, `no-tag` | check `suite:checkout:checkout` | Git is not on the host or the folder is not a git checkout, or no tag points at the commit. It is a fact, not an evidence rule. |
| `modified-tree` | check `suite:checkout:checkout`, `evidence.reasons` | The checkout has a change that the commit does not hold. The work folder of the suite does not count. |
| `python-mismatch` | check `suite:checkout:python` | The Python version is not in `requires-python` of `uv.lock`. |
| `packages-differ` | check `suite:checkout:packages`, `evidence.reasons` | An installed package has a version that differs from `uv.lock`, or a required package is missing. |
| `no-lock` | check `suite:checkout:python`, `suite:checkout:packages` | The checkout has no `uv.lock`. |
| `telemetry-on` | check `suite:checkout:telemetry-switch` | `ORT_DISABLE_TELEMETRY` is not `1` or `true`. The check is `record-only`. |
| `tool-missing`, `tool-failed`, `parse-failed` | check `suite:hardware:<method>` | The OS tool or file is absent, the tool exited with an error, or its output did not parse. |
| `not-offered` | check `suite:packs:<key>` | The Windows ML catalog does not offer the AMD EP for this PC. |
| `catalog-<ExceptionClass>` | check `suite:packs:<key>` | The Windows ML catalog raised this exception class. |
| `install-<code>` | check `suite:packs:<key>` | The install of the pack failed with this code of `eps.install()`, for example `install-offline`. |
| `certify-<result>` | check `suite:packs:<key>` | The probe of `eps.certify()` gave this result with no reason code. |
| a state code of the EP | check `suite:packs:<key>` | The host cannot use the EP, for example `os`, `vendor` or `cc`. |
| a code of `windows_ml.remove_installed()` | check `suite:packs:remove-<package>` | The Windows ML package did not go, for example `package-not-removed`, `package-unknown` or `record-refused`. |
| `cleanup-<ExceptionClass>` | check `suite:packs:remove-<key>` | The removal of the Windows ML packages raised this exception class. |
| `outside-model-root` | cleanup `remove-listed-file` | A file of the remove list is not inside `skellytracker/core/model_zoo/`. The suite does not delete it. |
| `not-deleted` | cleanup `delete-work-folder` | The work folder `.certify-work/` did not go. Delete it by hand. |
| `section-1-not-run` | `evidence.reasons` | Section 1 gave no facts of the checkout. |
| `no-commit` | `evidence.reasons` | Section 1 found no commit, or the package does not know its commit. |
| `python-differs` | `evidence.reasons` | The check `suite:checkout:python` failed. |
| `partial-run` | `evidence.reasons` | A section was not selected, did not run, or gave no result. |

A section and a check of the suite can also hold a code of the list above, for example `probe-l3-failed`,
and the bare class name of an exception.
