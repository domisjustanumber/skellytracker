# 0J26 — `suggest_execution_provider()` gives the EP that the host supports, also with no pack

**Status:** absorbed into [`state.py`](../../skellytracker/core/eps/state.py), [`eps/__init__.py`](../../skellytracker/core/eps/__init__.py), 2026-11-16 (user, question G4 of 2026-11-16; PR: pending).

## Decision

1. **Supported.** This host supports an EP key when `status().eps` has a row for the key and the
   `state` of that row is not `unsupported`. A built-in EP on its platform is supported. A plugin
   EP is supported when a GPU of this host passes the floors of its pack: the vendor, the compute
   capability and the driver branch. The pack does not need to be installed. A driver that is too
   old fails a floor. The EP is then not supported.
2. **A key of the table.** The result is the first successor that this host supports. It is None
   when this host supports no successor.
3. **An other EP key of the catalog on this platform.** The result is that key when this host
   supports it, else None.
4. **An install first.** The returned EP can be not usable yet, for example when its pack is not
   installed. The application reads `PackStatus.usable` and `PackStatus.install_hint` of the
   returned key in `status().eps`. It needs no rule of its own. The return type stays
   `str | None`.

This entry replaces items 3 and 4 of
[ADR-4CB1](4CB1-suggested-ep-for-a-saved-key-of-an-older-release.md): "usable on this host" becomes
"supported by this host". Items 2 and 3 of this entry replace them. The other items of ADR-4CB1 do
not change.

## Reason

- The user, in words: "`trt` or `cuda` must suggest `trt-rtx` if supported on the current
  hardware, else suggest `cuda`." The rule names the hardware, not the installed packs.
- A fresh install has no EP pack. With the rule of ADR-4CB1, each saved `trt` or `cuda` then gave
  None, and the application fell back to the recommendation on the CPU. A GPU user must not drop
  to the CPU without a word.
- The predicate uses the existing state model. The INI status file of `skellytracker-eps` already
  writes `supported` as `state != "unsupported"` (`status_ini` of
  `skellytracker/core/eps/cli.py`).
- A driver that is too old gives no install hint: an install does not help. The hardware class of
  such a host gives the `update-driver` offer in `status().performance`. On None, the application
  uses that recommendation, so the user sees the offer.

## Consequences

- A run with the suggested EP fails with `EpUnavailableError` and the install hint until the pack
  is installed.
- A host with only the `cuda` pack and a GPU that passes the `trt-rtx` floors gets `trt-rtx` for a
  saved `cuda`. The `trt-rtx` pack is then not installed, and `usable` is false.
- The fourth consequence of ADR-4CB1 does not hold any more: a pack that is not installed does not
  move the result to the next successor.

## Evidence

- `suggest_execution_provider` and `_pack_status` of `skellytracker/core/eps/state.py`, and
  `pack_state` of `skellytracker/core/eps/store.py`: through `_pack_status`, the state is
  `unsupported` only when no GPU of the host passes the floors of the pack.
- The tests are in `skellytracker/tests/test_eps_cli.py`.
- On the local host with an RTX GPU and no EP pack, `trt` and `cuda` gave `trt-rtx`, `directml`
  gave None and `cpu` gave `cpu`.

## Alternatives rejected

- **Only a usable successor (ADR-4CB1).** A fresh install then gets None on each GPU host.
- **A usable successor first, then a supported one.** It does not follow the rule of the user, and
  it gives a weaker EP when a better pack is only one install away.
- **A driver that is too old counts as supported.** The row then has no install hint, and
  `check_start()` gives an install hint that does not help. The `update-driver` offer of the
  recommendation tells the user what to do.
- **A record result with the key and a flag.** `status()` already gives `usable` and
  `install_hint` for each key.
