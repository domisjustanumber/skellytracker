# Reason codes of skellytracker

This file is the list of the reason codes of `skellytracker.certify()`
([ADR-P0JZ](../decisions/entries/P0JZ-certify-contract-in-each-package.md)).
The contract `report-format.md` of the repository `skellycertify` owns the common codes, and section 5.4
of the contract asks each package to keep the list of its own codes.
Add a code to this list in the commit that adds the code to a check.
The list holds the codes of the level `quick`. The codes of `tools/certify_platform.py`, the level
`full` of today, are not in this list yet.

## Common codes that this package uses

| Code | Where | Meaning |
|---|---|---|
| `timed-out` | check | The child process of the check ran longer than its time limit. |
| `crashed` | check | The child process ended with no result. `numbers.exit_code` holds its exit code. |
| `hung-at-exit` | check `<name>:exit` | The child process gave its result and did not end. The package stopped it. |
| `cancelled` | check, `evidence.reasons` | The caller set `cancel`. |
| `not-built` | check, `evidence.reasons` | The level `full` is not in `certify()` yet. It is `tools/certify_platform.py`. |
| `no-version` | `evidence.reasons` | `package.version` is not a SemVer version. |
| `no-commit` | `evidence.reasons` | The package does not know its commit. |
| `modified-tree` | `evidence.reasons` | The source tree had a change that the commit does not hold, or the package does not know. |

The package never writes `gpu-busy`, `bad-output` or `partial-run`. It cannot see the pipelines of
an application. A quick check of a part of the EPs is complete for each EP that it checks.

## Codes of this package

| Code | Where | Meaning |
|---|---|---|
| `no-check` | `evidence.reasons` | The run had no EP to check. For example, each GPU EP of this host has a reviewed row. |
| `not-gpu-ep` | check | The EP runs no model on a GPU, for example `cpu`. The quick check compares a GPU EP with the CPU EP. |
| `ep-<code>` | check | The EP cannot run on this host. `<code>` is the reason code of the EP state, or the state: `ep-os`, `ep-no-device`, `ep-cc-too-low`, `ep-driver-too-old`, `ep-rocm-missing`, `ep-rocm-version`, `ep-not-installed`, `ep-stale`. The quick check installs nothing. |
| `probe-l2-failed` | check `<key>:probe` | The EP did not register, or it lists no device for the GPU. |
| `probe-l3-failed` | check `<key>:probe` | The trial session on the probe model failed: a node is not on the EP, or the output differs from the CPU EP. |
| `probe-not-passed` | check `<key>:image` | The image run did not start, because the probe did not pass. |
| `models-missing` | check `<key>:image` | A model file or an extra of the pipeline is not on this host. The quick check downloads no model. |
| `outputs-not-comparable` | check `<key>:image` | The pipeline has no output `boxes` or no output `wholebody`. The comparison needs the two. |
| `no-person-on-cpu` | check `<key>:image` | The CPU EP found no person on the test image. |
| `people-differ` | check `<key>:image` | The EP and the CPU EP found a different set of persons. |
| `box-differs` | check `<key>:image` | A box IoU is less than `box_iou_min`. |
| `scores-differ` | check `<key>:image` | A keypoint score on the EP is much lower than on the CPU EP. |
| `no-point-to-compare` | check `<key>:image` | No keypoint has a score of `score_min` or more in the two results. |
| `keypoints-differ` | check `<key>:image` | A keypoint is farther than `keypoint_box_fraction_max` of the box diagonal from the CPU EP result. |
| `not-finite` | check `<key>:image` | A value of the EP result is not finite where the CPU EP result is finite. |
| `partial-placement` | check `<key>:image` | Some nodes of the pipeline ran on the CPU EP, not on the EP. |
| `<ExceptionClass>` | check, `cleanup` | A setup step or a cleanup step raised this exception class, for example `EpUnavailableError` or `DownloadError`. The report never holds the message. |

## Check names

| Check | Meaning |
|---|---|
| `<key>:probe` | The L3 probe of the EP `<key>` (`verify()`), in a child process. |
| `<key>:image` | The pipeline on one test image on the EP and on the CPU EP, in a child process, and the comparison. |
| `<key>` | The quick check of the EP. It passes only when `<key>:probe` and `<key>:image` pass. |
| `<key>:probe:exit`, `<key>:image:exit` | The check `exit` of the contract for a child that gave its result and did not end cleanly. |
| `full` | The level `full`. It is `not-run` with `not-built`. |
| cleanup `test-image`, `field-test-opt-in` | The delete of the test image that the run downloaded, and the removal of the opt-in that a check that did not pass wrote. |
