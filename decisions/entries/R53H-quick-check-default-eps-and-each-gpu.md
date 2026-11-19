# R53H — The quick check: `directml` and the Windows ML EPs in the default selection, and one check for each GPU

**Status:** absorbed into [`certification.py`](../../skellytracker/certification.py), 2026-11-19 (user; PR: pending).

## Decision

1. **Default selection.** With no EP named, the quick level of `skellytracker.certify()` checks each GPU
   EP of the host that has no reviewed row in `ep_evidence.yaml` for the GPU model and OS. This is each
   usable plugin EP, and also `directml` and each EP of the Windows ML catalog. Before this entry, a
   `field-test` EP was checked only when the caller named it.
2. **GPUs.** The check runs on the GPUs that the caller names with the option `device`: one device key
   or a list of device keys. With no GPU named, it runs on each GPU that the EP can use. Before this
   entry, it ran on the first GPU of `run_devices(key)`.
3. **Check names.** Each EP on each GPU gives the checks `<ep>:probe`, `<ep>:image` and `<ep>`. `<ep>`
   is `<key>@<device>`, for example `cuda@10de-2484-0`: the device key with no `gpu:` and with `-` for
   `:`. It is `<key>` alone for an EP with no GPU to run on. Thus the name of an EP check has no `:`.
   `details.eps.<ep>.device` gives the device key.
4. A named EP that cannot use a named GPU is `not-run` with the reason code `gpu-not-usable`. A device
   key that is not a GPU of the host raises `EpRequestError`.

## Reason

- User rulings, 2026-11-19: the default includes `directml` and the Windows ML EPs when they are not
  certified; the check runs on the GPU that the caller selects, and by default on each GPU.
- Item 3 is the choice of the agent: the contract requires a unique check name, and a caller must find
  the EP rows with no parse of the device key.

## Consequences

- A quick run with no argument can be longer on a host with two GPUs: about 7 to 8 seconds for each EP
  and GPU on one Windows host with an RTX 3070
  ([ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md)).
- An EP that is slower than the CPU EP passes its check and becomes usable. `speed_against_cpu` is a
  record only.
- The stored result of `quick-checks.json` is for the GPU model. Two GPUs of one model share it, and
  the last check wins.
- An EP of the Windows ML catalog whose package is not installed is `not-run`. The quick level
  installs nothing.
- `status().certify_offers` does not change: it lists the plugin EPs only, on the first GPU.

## Alternatives rejected

- **The device key unchanged in the name** (`cuda@gpu:10de:2484:0:probe`). A caller cannot then split
  the EP check from its parts at a `:`.
- **`<key>` alone for a host with one GPU.** A caller would need two forms of the name.
