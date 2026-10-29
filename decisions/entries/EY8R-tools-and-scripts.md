# EY8R — Tools and scripts

**Status:** accepted, 2026-10-28 (user).

## Decision

1. **Script.** A script is code that made the evidence for an entry, or did a one-off job that an
   entry records, and that entry names it. No test, hook, CI job, skill or workflow step runs it on
   the files of the repository. Its own unit tests on small inputs are allowed. They are next to it
   in `scripts/tests/`. A script does not change after its entry is decided. It is in `scripts/` of
   the log that holds its entry ([ADR-GN3D](GN3D-module-decision-logs.md)).
2. **Tool.** A tool is code that the repo runs in its normal work: a test, a hook, a CI job, a skill
   or a workflow step calls it, or it writes a tracked file. It changes with the rules that it
   enforces, and it has tests. Each tool is in the root [`tools/`](../../tools/). This also applies to
   a tool that only one module uses.
3. **A script becomes a tool.** When a later step starts to run a script, the script becomes a tool.
   Move it to `tools/` and add a test.
4. **Classification on 2026-10-28.** The split checker
   [`check_split_verbatim.py`](../scripts/check_split_verbatim.py), its
   [`split_manifest.yaml`](../scripts/split_manifest.yaml) and its test
   [`test_check_split_verbatim.py`](../scripts/tests/test_check_split_verbatim.py) are a script with its
   test. They are in `decisions/scripts/` ([ADR-D9VT](D9VT-decision-log-move.md)).
   [`next_number_timing.py`](../scripts/next_number_timing.py) is a script. Each other file in `tools/`
   is a tool and stays there. This includes `tools/make_vectors.py`.

## Reason

- A task in one module does not load rules for code that does not run again.
- A fixed place for each kind of code stops the same question in each PR.
- A script that does not change shows what ran for its entry.

## Alternatives rejected

- **A `tools/` folder in each module.** The tests, the hooks, CI and the ruff commands then need a
  path for each module. A move of `tools/make_vectors.py` also needs a change to its imports.

_Edited 2026-10-29 (this PR): link repair._
