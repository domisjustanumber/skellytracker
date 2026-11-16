# 4CB1 — `suggest_execution_provider()` gives the EP for a saved key of an older release

**Status:** absorbed into [`state.py`](../../skellytracker/core/eps/state.py), [`eps/__init__.py`](../../skellytracker/core/eps/__init__.py), [`ep_catalog.yaml`](../../skellytracker/core/eps/ep_catalog.yaml), 2026-11-16 (user, instruction on legacy settings files and questions G1 to G3, 2026-11-16; PR: pending).

## Decision

1. **The call.** `skellytracker.core.eps` has one public function,
   `suggest_execution_provider(saved_execution_provider: str) -> str | None`. It takes an EP key
   that a setting of an older release holds. It returns the EP key to use on this host, or None.
2. **The table.** `legacy_keys` of `ep_catalog.yaml` gives the successors of each older key, in
   order:

   | Older key | Successors |
   |---|---|
   | `trt` | `trt-rtx`, `cuda` |
   | `cuda` | `trt-rtx`, `cuda` |
   | `directml` | none |

3. **A key of the table.** The result is the first successor whose `PackStatus.usable` is true on
   this host. It is None when no successor is usable.
4. **An other EP key of the catalog on this platform.** The result is that key when it is usable,
   else None.
5. **Each other string.** The result is None: a reserved key with no row in the table, an unknown
   key and the empty string. The function raises for no string. The match is exact and
   case-sensitive, as each other key lookup of the catalog.
6. **The state.** The function uses the state of `status()`. It loads no library and uses no
   network.
7. **When an application calls it.** An application calls it only for a setting that an older
   release saved. A choice of this release stays as chosen. On None, the application uses the
   recommendation, `status().performance`, and shows a notice. The call and the notice are rules
   of the application.
8. **A successor.** Each successor must be an EP key of the catalog that is not reserved.
   `tools/ep_catalog.py --check` checks this.
9. **A request does not change.** The reserved-key rule of the catalog stays: a request for `trt`
   or `directml` raises `EpRequestError`. A request for `cuda` runs on `cuda`. Only
   `suggest_execution_provider()` reads the table.

This entry adds to [ADR-1GGP](1GGP-ep-api-gives-an-application-each-ep-fact.md). That entry does not
change.

## Reason

- An application must hold no EP key and no EP fact
  ([ADR-1GGP](1GGP-ep-api-gives-an-application-each-ep-fact.md)). A table of old keys in freemocap
  is an EP fact.
- freemocap has settings files of releases before skellytracker 2.0. A saved `trt` cannot run in
  2.0: the key is reserved.
- The user, in words: "If loading a legacy settings file, `trt` or `cuda` must suggest `trt-rtx` if
  supported on the current hardware, else suggest `cuda`." The user wants the best NVIDIA EP for an
  older NVIDIA choice.

## Consequences

- A saved `cuda` of an older release becomes `trt-rtx` on a host where `trt-rtx` is usable.
- When classic TensorRT comes back under the key `trt`, the row of `trt` must leave the table. A
  saved `trt` then gives `trt` by item 4.
- A change of `ep_catalog.yaml` changes the catalog revision. An installed pack is
  `installed_unverified` again until the next trial session.
- A pack that is not installed is not usable. The function then gives the next successor or None.
  It gives no install offer: `status().performance` holds the offers.

## Evidence

- `suggest_execution_provider` and `_pack_status` of `skellytracker/core/eps/state.py`, and `check`
  of `tools/ep_catalog.py`.
- The tests are in `skellytracker/tests/test_eps_cli.py` and `tools/tests/test_ep_catalog.py`.

## Alternatives rejected

- **A `successors` value on the EP row of `cuda`.** A reader can then think that a new request for
  `cuda` moves to `trt-rtx`. A reserved row such as `trt` is also not an EP row of a request.
- **The table in the application.** The application then holds EP keys.
- **A check of the table at each load of the catalog.** The catalog has no check at load.
  `tools/ep_catalog.py --check` checks each other rule of the catalog, before each commit.
