# 9VN4 — No camera recordings or camera frames in git, except golden reference files

**Status:** absorbed into [`AGENTS.md#8-private-data`](../../AGENTS.md#8-private-data), [`stack-commit/SKILL.md#commit-commands`](../../.claude/skills/stack-commit/SKILL.md#commit-commands), [`tools/check_camera_media.py`](../../tools/check_camera_media.py), [`tools/sync_bootstrap_kit.py`](../../tools/sync_bootstrap_kit.py), 2026-11-17 (user).

## Decision

1. **The rule.** Do not commit a camera recording (video or audio) or a camera frame (a still image
   or a raw frame from a camera). The one exception is a golden reference file: its path starts with
   an item of `GOLDEN_PATHS` in `tools/check_camera_media.py`. A screenshot that shows a camera
   image is a camera frame. A chart, a diagram or a UI screenshot that shows no camera image is not
   a camera frame. A results folder holds summaries, not the media. To show a camera frame to the
   user, give its local path.
2. **The tool.** `tools/check_camera_media.py` refuses such a file in the files of a commit, by its
   extension and by its first bytes. The `camera-media` pre-commit hook runs it.
   `tools/tests/test_camera_media.py` tests it, and its test of the tracked files runs in
   `pytest tools/tests`. `--all` lists each tracked file that the rule refuses.
3. **`GOLDEN_PATHS` for this repository** is `()`. This repository has no golden reference
   recording or frame.
4. **The commit steps.** The skill `stack-commit` gives the steps before a commit and the steps when
   a recording or a frame is already committed. This repository has no skill `commit-files`.
5. **The kit.** The tool and its test are copies of the bootstrap kit. The kit has its own skill
   `commit-files`. The block edit of section 8 in `tools/sync_bootstrap_kit.py` changes the link to
   `stack-commit` into a link to that skill.

## Reason

- The user decided on 2026-11-17 that skellytracker adopts the rule: "skellytracker adopts the
  rule. I add the camera-media check, its test, the hook and the paragraph here, so both sides state
  the same rule."
- The bootstrap kit got the rule, the tool and the skill from the skellycam work of the same day
  (skellycam ADR-G5S0 `no-camera-recordings-or-frames-in-git` and skellycam ADR-NMM1
  `design-of-the-camera-media-check`, on the branch `dom/native-jpeg`, no PR yet). The kit keeps no
  rule that this repository does not state
  ([ADR-P3NK](P3NK-bootstrap-kit-in-freemocap-project.md)). Without the rule here,
  `tools/sync_bootstrap_kit.py --check` failed.
- Recordings and frames are large, and they can show people and rooms. Git history is permanent.
- `stack-commit` is the commit skill of this repository. A second commit skill would repeat its
  commit commands.

## Evidence

- `uv run python tools/check_camera_media.py --all` on 2026-11-17 on `dom/sidecar-implementation`:
  no findings in 937 tracked files, with `()` and with the kit default `golden/`. The tracked images
  are `shared/skellytracker-logo.png` and `shared/skellytracker-logo.svg`. The files in
  `skellytracker/tests/sidecar/fixtures/golden/` are JSON files.

## Alternatives rejected

- A live copy of the kit skill `commit-files`. It repeats the commit commands of `stack-commit`.
- `GOLDEN_PATHS = ("golden/",)`. No golden reference file needs it, and the narrowest list is
  empty.
