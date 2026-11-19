# SP4Z — The certify suite calls the level `full` and writes the report file of `skellycertify`

**Status:** absorbed into [`certify_platform.py`](../../tools/certify_platform.py), [`certify_eps.py`](../../tools/certify_eps.py), [`certification.py`](../../skellytracker/certification.py), [`errors.py`](../../skellytracker/core/errors.py), [`records.py`](../../skellytracker/core/eps/records.py), [the certify suite](../../skellytracker/REASON_CODES.md#the-certify-suite), 2026-11-19 (user; PR: pending).

## Decision

Built today: each item. Only sections 1 and 2 of the suite ran on a host. Sections 3 and 4 ran only in
tests with fakes.

1. **Sections.** `tools/certify_platform.py` has four sections: `checkout` (the versions against
   `uv.lock`), `hardware` (the hardware probe against the tools of the OS), `packs` (the install and the
   verify of each pack in the EP store of the work folder) and `full` (`skellytracker.certify("full")` in
   that EP store). The old sections 4 to 7 go: the level `full` holds the pipeline checks and the JPEG
   checks.
2. **One report.** The suite writes one module report. Its base is the report of `certify("full")`.
   Each section adds the check `suite:<slug>`, and each check of a section is `suite:<slug>:<name>`.
   `details.suite` holds the summaries, the answers and the telemetry booleans. A section that was not
   selected or did not run gives the evidence reason `partial-run`.
3. **Report file.** The file is the report file of the repository `skellycertify`: a Markdown file
   `certify-report-<UTC time>.md` with a summary for a person and, last, the heading `## Data` with one
   JSON block. The block holds `schema`, `app` (null), `modules` (one module) and `note`.
4. **No second environment.** The suite tests each EP only on the pinned ONNX Runtime. The second
   environment, the variable `SKELLYTRACKER_EP_ORT_FALLBACK` and `certification.ort_fallback` of the EP
   catalog go. This replaces item 9 of [ADR-XSE7](XSE7-amd-eps-in-the-field-test.md) ("**Suite, Linux,
   second environment.** ...").
5. **Each GPU counts.** A result of an EP on a GPU counts at each level and in the suite, also when the
   hardware class of the GPU does not list the EP, for example `directml` on an NVIDIA GPU. A reviewer
   decides if such a report gives a reviewed row. This replaces the sentence of item 11 of
   [ADR-Y14H](Y14H-certify-suite.md) that makes such a result `record-only`.
6. **Refusal fields.** A refusal of the check rule gives `execution_provider`, `device_key` and
   `reason_code` as fields of `EpUnavailableError`. `DeviceCheck.reason_code` gives the reason for each
   GPU.
7. **Installed pack.** For an EP with a pack, `details.eps.<ep>` of a report holds
   `installed_pack_version` and `wheels_match_lock`, from the manifest of the installed pack. A reviewed
   row does not need a clean install: it needs what the level `full` proves on the EP store of the
   person. The install check stays in the section `packs` of the suite.
8. **Cancel object.** Each `cancel` argument of `eps` takes an object with `is_set()`, not only a
   `threading.Event`.

## Reason

- User rulings, 2026-11-19: items 1 to 6. The session of the repository `skellycertify` gave item 7 as
  a ruling of the user of the same day.
- No application build can repeat a result of a second ONNX Runtime, and no AMD hardware ran it.
- The check rule needs a pass or a fail to let an EP run. A record only would keep `directml` off each
  NVIDIA and Intel GPU.
- Item 8: freemocap passed a `multiprocessing` event, and the type check refused it.

## Consequences

- `wheels_match_lock` compares the sha256 values that the install recorded. It does not read a wheel or
  an unpacked file again. The EP store checks the size of each unpacked file.
- The suite runs the probe of each plugin pack two times: in the section `packs` and in the level
  `full`.
- The time estimate and the time limit of the section `full` are not calibrated.
- [ADR-75J6](75J6-full-level-in-certify-and-uuid-report-id.md) gives "about 150" JPEG checks for each
  EP. One run on `directml` gave 66 for the CPU EP and 66 for the EP.
