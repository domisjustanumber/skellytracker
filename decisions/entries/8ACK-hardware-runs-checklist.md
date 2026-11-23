# 8ACK — A checklist of the hardware runs, off the read path

**Status:** absorbed into [Rules](../README.md#rules), [Hardware runs](../hardware-runs.md#hardware-runs), 2026-11-23 (absorb at landing; PR: pending).

## Decision

1. The file `decisions/hardware-runs.md` is the checklist of the runs that wait for hardware or for
   an OS that this project does not have at hand. It groups the runs by what they need. Git tracks
   it. It is not on the read path. One line of `open-work.md` links it.
2. An open-work item that waits for such hardware is stated in full in `hardware-runs.md`. The
   absorb rule accepts that file as it accepts `open-work.md`.
3. Each run is a certify run in a freemocap build, with a hand-in of the report file
   ([ADR-Q7VQ](Q7VQ-certify-rulings-of-2026-11-20.md) item 1). An item marked **Measurement** gives
   an evidence entry. An item leaves when the reviewed report exists: delete the item, and write the
   result in an entry.
4. A measurement goes in an entry or in a file of `evidence/`. A subject that the project examined
   and did not build goes in a research note of `research/`
   ([ADR-9NC2](9NC2-research-notes-folder.md)).
5. The limit `OPEN_WORK_LIMIT` of `tools/check_decision_log.py` stays at 20 000 characters.

## Reason

- The user decided items 1 to 5 on 2026-11-23.
- `open-work.md` had 19 928 of its 20 000 characters. After this change it has 13 850. The runs that
  no system at hand can do, the measurements and the research took most of that size.
- An agent reads `open-work.md` for each task. A run that waits for an AMD GPU, Linux or macOS
  applies only to a person who has that system.

## Consequences

- A numbered item of the certification build list keeps its number in `open-work.md`, also when its
  run moved. A citation such as "item 4 of the certification build list" stays valid.
- The 2026-11-17 cost of the detector preprocess is in
  [`evidence/detector-preprocess-cost-2026-11-17.md`](../evidence/detector-preprocess-cost-2026-11-17.md).
  The other dated facts with no entry are in
  [`evidence/8ACK-open-work-facts.md`](../evidence/8ACK-open-work-facts.md).
- The items on the JPEG decode with Intel QSV and with rocJPEG are one line each in `open-work.md`.
  Their research notes hold the rest.

## Open work

See [open-work.md](../open-work.md).
