# 0GHT — Python 3.13 in each environment, and `fill` refuses the hand-over folder by `--root`

**Status:** accepted, 2026-11-23 (user).

## Decision

1. **One Python.** Each environment of the project runs Python 3.13: this repository, the tools
   of the kit, the spec repository and each exporter. No tool keeps a path for an older Python.
   The rule "Python 3.9 or later, standard library only" for `pack` and `list` of
   `tools/intake_bundle.py` goes. The bundle tool can import the check tools of its folder.
2. **A library that blocks 3.13.** When a library does not run on Python 3.13, the project looks
   for another library or another route. It does not keep an older Python for it.
3. **`fill`.** `fill` of `tools/make_vectors.py` requires `--root`, the hand-over folder
   `intakes/`. It refuses a vector file and a reference folder in that folder. It still refuses a
   folder of its own checkout and a folder that is not `<payload>/reference` of the vector file.
   This adds to item 5 of [ADR-AD33](AD33-bundles-are-untrusted-input.md).
4. **Patch scope.** `pack` checks a patch with the scope `skellytracker/`. This default is a name
   of the bundle format, as the patch file name `skellytracker.patch` is. `verify` of the gate tool
   gives the scope as a parameter.

## Reason

- Item 1: the user ruled it on 2026-11-23: "We must use the same python 3.13 across the board, 3.9
  and 3.10 are ancient." A path for an old Python is code that no CI job runs.
- Item 3: after the move of the spec tools
  ([ADR-2DJ8](2DJ8-spec-tools-with-no-package-import.md)), "a folder of this checkout" no longer
  holds `intakes/`. Without `--root`, `fill` can run the code of a bundle there.

## Evidence

- The four exporter checkouts on 2026-11-23: none runs a Python below 3.12 on the host. Two require
  3.14 or later, one requires 3.13 or later, and one requires 3.12 to below 3.14.
- The conversion of OpenMMLab-Exporter runs in a Docker image with torch 2.0.0 and the mmdeploy
  stack. Its Python version is not measured.

## Open work

[open-work.md](../open-work.md)
