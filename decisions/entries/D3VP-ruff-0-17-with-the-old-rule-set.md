# D3VP — Ruff 0.17.5 with the rule set of ruff 0.15

**Status:** accepted, 2026-11-13 (user).

## Decision

1. The dev group pins `ruff==0.17.5`.
2. `[tool.ruff.lint]` of `pyproject.toml` keeps the rules of ruff 0.15.17:
   `select = ["E4", "E7", "E9", "F", "B", "S", "C4", "ISC", "PERF"]` and `ignore = ["ISC004"]`.
3. Before the 2.0.0 release, a review examines the rules that ruff 0.16 added to the default set
   and ISC004. It decides which rules to adopt. Each adopted rule gets its fixes in the commit group
   of that review. The review is in the gate of stage 2.5 of the
   [implementation plan](../../specs/sidecar-implementation-plan.md#25-release-200).

## Reason

- Ruff 0.16.0 enables 413 default rules, up from 59. `extend-select` adds to that default. With the
  old config, ruff 0.17.5 reports 352 findings in the paths of the lint command.
- ISC004 left preview in ruff 0.16.0. It is in the selected `ISC` group and reports 36 findings.
- The autofix of import sorting (I001) alone changes 83 files, 60 in `skellytracker/`.
  [`skellytracker/AGENTS.md`](../../skellytracker/AGENTS.md#code-conventions) forbids reformatting
  of lines that a change does not need. Fixes in `decisions/scripts/` also change scripts of decided
  entries ([ADR-EY8R](EY8R-tools-and-scripts.md)).
- The bump with the old rule set changes no code.

## Evidence

- `uvx ruff@0.17.5 check` with the old config: 352 findings, 236 fixable (2026-11-13).
- `uvx ruff@0.15.17 check --preview --select ISC004`: the same 36 findings.
- With the config of item 2, ruff 0.17.5 reports no finding. `--show-settings` lists the same 184
  enabled rules as ruff 0.15.17.
- Source of the changes: the ruff 0.16.0 changelog (2026-07-23), "Ruff now enables a much larger set
  of rules by default (413, up from 59)", and its stabilization list, which has ISC004.

## Alternatives rejected

- **Fix ISC004 now.** 36 unsafe fixes, which add parentheses, in `tools/` and `decisions/scripts/`.
  The review of item 3 decides it with the other rules.
- **Adopt the new default without I001.** 259 findings stay. Some fixes change behaviour (TRY004) or
  re-sort the public `__all__` (RUF022).
- **Keep `ruff==0.15.17`.** The user chose the bump.
