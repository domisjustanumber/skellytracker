# 1GGP — The EP API gives an application each EP fact that it shows

**Status:** absorbed into [`skellytracker/AGENTS.md#layout`](../../skellytracker/AGENTS.md#layout), [`eps/__init__.py`](../../skellytracker/core/eps/__init__.py), [`run.py`](../../skellytracker/core/pipelines/run.py), 2026-11-16 (user, rule on execution providers in applications, 2026-11-16; PR: pending).

## Decision

1. **The rule.** An application, for example freemocap, holds no fact about an execution provider.
   It shows the EPs from `eps.status()`. It takes its recommended and automatic choices from
   `eps.recommend()`. A fact that an application needs gets a field of the API.
2. **`PackStatus.usable`.** A boolean: true when the state of the EP is a state that a run can use.
   An application does not compare `state` with a list of states.
3. **`PackStatus.install_hint`.** The text with the command that installs or repairs the pack. It
   is the text of `EpUnavailableError.hint` and of `InstallOffer.note`. It is None when the EP is
   usable, and when an install does not help (the state `unsupported`).
4. **`PackStatus.uses_gpu`.** A boolean, from `gpu` of the EP catalog.
5. **`PackStatus.description`.** One sentence for a user, from the new value `description` of each
   EP of `ep_catalog.yaml`: what the EP runs on and what it needs. It has 120 characters or fewer.
6. **`PackStatus.devices`.** The GPUs of this host that the EP can use, as `RunDevice` records, in
   the order of `run_devices(key)`: the most VRAM first. It is empty for a built-in EP and for an EP
   that is not usable. `status()` still loads no library and uses no network.
7. **The order of `EpStatus.eps`.** The order is the order of the EP keys of the EP catalog:
   `trt-rtx`, `cuda`, `coreml`, `cpu`, without the keys that the platform does not have. The order
   is a contract. Each hardware class of the catalog lists its candidates in this order. The order
   is not the recommendation.
8. **`PipelineRun.models`.** The item of each `onnx_model` node also has `size` and `precision` of
   the artifact that runs, `execution_provider` (the EP key that the session uses) and `device`
   (the device key of the GPU, or None). For a node with a session on each of two or more GPUs,
   `device` is the list of the device keys in the order of the GPUs of the run. A node that does
   not run has `execution_provider` None and `device` None.

This entry adds to item 10 of [ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md). That entry
does not change.

## Reason

- The user, in words: "FreeMoCap must not keep any knowledge of Execution Providers. It uses the
  API surface of skellytracker to populate the available options and sets the recommended/auto
  options based on the suggestions from skellytracker."
- An inventory of freemocap found the facts that `skellytracker.core.eps` did not give: the usable
  states (a private constant), the install text (a private function), the GPU flag, a text for a
  user, the GPUs of each EP, the order of the rows, and the EP and the device of a model of a run.

## Consequences

- A change of `ep_catalog.yaml` changes the catalog revision. The key of a stored verification
  result holds the revision, so an installed pack is `installed_unverified` again until the next
  trial session.
- `status --json` has the new fields in each item of `eps`. The schema name stays
  `skellytracker.eps.status/1`: the change only adds fields.
- `coreml` has `uses_gpu` true and no `devices`: a built-in EP takes no device key.
- `devices` holds each GPU that passes the floors of the pack. The state of the row is the state of
  the first of them.

## Evidence

- `PackStatus` and `EpStatus` of `skellytracker/core/eps/records.py`, `_pack_status` of
  `skellytracker/core/eps/state.py`, and `PipelineRun.models` of
  `skellytracker/core/pipelines/run.py`.
- The tests are `skellytracker/tests/test_eps_cli.py`, `skellytracker/tests/pipelines/test_run.py`
  and `skellytracker/tests/pipelines/test_sessions.py`.

## Alternatives rejected

- **A public `USABLE_STATES`.** An application then still holds the rule that the list means.
- **`install_command` with only the command.** The other two places hold the full text. One concept
  has one form.
- **A break-out of `PipelineRun.models` for each GPU.** One item for each node is the form that
  exists. A list in `device` gives the GPUs.
