---
name: brief-subagent
description: Use this skill in skellytracker before you start a sub-agent or a workflow agent, for example for a review, a search, a draft or a landing. Use it also before you tell the user what a sub-agent found.
---

# Brief a sub-agent and check its result

This skill uses ASD-STE100 Simplified Technical English.

A sub-agent knows only its brief. Its report can give a wrong line number or a wrong claim in the
same words as a correct one ([ADR-9K2M](../../../decisions/entries/9K2M-agent-session-rules.md)).

## The brief

1. State the goal, the files to read and the facts that you already know.
2. State the files that the agent can change. A review or a search changes no file. In the
   spec-build stage, no agent changes a file under `skellytracker/`.
3. Tell the agent to give each location as `path:line` from `grep -n` output or Read output, with
   the quoted line.
4. If the agent runs a tool on bundle content, give the safety check of
   [Session steps](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#session-steps)
   in the brief ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).

## The result

1. Open each cited line of each claim that you tell the user or act on.
2. Correct a wrong line number before you tell the user.
3. Tell the user which claims you checked.
