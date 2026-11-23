# 9NC2 — A tracked folder for research notes

**Status:** absorbed into [Purpose](../../AGENTS.md#1-purpose), [Research notes](../../research/README.md#research-notes), 2026-11-23 (absorb at landing; PR: pending).

## Decision

1. The folder `research/` in the repository root holds the research notes. Git tracks it.
2. A research note records what is known about a subject that the project examined and did not
   build. It is not a decision, and it changes no rule.
3. A measured fact stays in a decision entry. A note cites the entry.
4. A note marks each statement as measured by this project, as documented by a vendor with the URL,
   or as a guess. It gives the date of its research.
5. A note ends with the next step: the measurement to make before a build, and the result that
   means "do not build".
6. The first notes are the JPEG decode on an Intel GPU with Quick Sync Video and the JPEG decode on
   an AMD GPU with rocJPEG.

## Reason

- The user asked for research documents "so a future worker can pick up where we left off", and
  then for a tracked research folder.
- `plans/` is a local folder that git ignores, and a tracked file must not cite it. An open-work
  item can link a note in `research/`.
- An entry holds a decision or a measurement. The research of a subject with no measurement and no
  decision had no tracked home.

## Consequences

- A note obeys the rules of each tracked document: ASD-STE100, the private data rules and working
  links.
- A vendor page can change after the date of a note. A worker must read the source again before a
  build.

## Open work

- None.
