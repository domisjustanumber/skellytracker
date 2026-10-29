# Rules

- The spec is normative. Do not change its meaning in your docs or code.
- If a model property does not map exactly to the spec, do not use an approximate mapping. Write a
  change proposal (phase 2) and stop.
- Known case: an ROI refiner is a gap. An ROI refiner is a model that gives a region of interest to
  the next model, for example a hand re-crop model. Do not describe it as a pose estimator with two
  fake keypoints.
- The evidence for a row is an upstream file and line, an upstream config key, or a read of the ONNX
  graph (the command, and the node or tensor name). A plan, a paper, a README, the notes of a
  contributor (for example an exporter) and a spec reference example are secondary sources. Mark a secondary citation with
  `(secondary)`. A row that has only a secondary source is `unverified`. The next two bullets give
  the exceptions.
- A `near-miss` or a `gap` compares the property with the spec text. If only a secondary source shows
  the property, still give the row its `near-miss` or `gap` verdict. Mark the source `(secondary)`.
  Name the missing primary evidence in the row. The proposal of the row names it in part 1. Before
  the user accepts the proposal, part 1 must cite the primary evidence.
- An exporter document is a secondary source. A user decision cannot make it primary.
- A committed check can map a claim of a document to an upstream file and line. The check table must
  pin a full 40-character SHA on the default branch of the upstream repo. If the check passes, cite
  that upstream file and line as the primary evidence. Also cite the check ID and the document line,
  with the commit of the check table ([ADR-FDTD](../../../decisions/FDTD-evidence-sources-and-exporter-permalinks.md)).
- A claim that no passing check maps to an upstream line stays `(secondary)`.
- A value that you choose (in an exporter, the exporter chooses it) has no upstream evidence.
  Examples are a name, a rule for the YAML file and a path. Judge its row against the spec only. Cite
  your code that writes the value. If no such code exists, write `none yet (no code)`. Such a row is
  not `unverified` only because the code does not exist or you cannot read it. The model intake
  template lists these rows (heading "Verdicts").
- Do not publish a `vNEXT` sidecar to a shared or remote folder (see
  [Publishing](validation-and-publishing.md#publishing)).

## User decisions

These rules come from [ADR-FDTD](../../../decisions/FDTD-evidence-sources-and-exporter-permalinks.md).

- A user decision is not evidence. It can choose a policy or a value. It cannot show an upstream
  property.
- A submission must not rely on a user decision that only a plan holds. Write each user decision in
  words. Do not cite its item number. Do not cite the path of the plan.
- If the decision is about your exporter, record it as an entry in the decision log of your repo.
  Cite the entry by the repo name, the ID and the commit.
- If the decision is about the spec, list it under "Plan decisions" in part 1 of the proposal. The
  user confirms or refuses it before acceptance. The decision entry of the proposal records it in
  words.
- If the decision is about the workflow or these rules, tell the user. A bundle does not change the
  workflow ([Workflow changes](hand-over.md#workflow-changes),
  [ADR-FADS](../../../decisions/FADS-hand-over-bundles-in-intakes.md)).

## Sources

These forms come from [ADR-FDTD](../../../decisions/FDTD-evidence-sources-and-exporter-permalinks.md).

- Use the citation forms of [`AGENTS.md`](../../../AGENTS.md#5-decision-log) and of the decision-log
  [Rules](../../../decisions/README.md#rules)
  ([ADR-Z05A](../../../decisions/Z05A-essential-decision-log-rules.md)) also in an intake, a
  proposal, a reference file and spec guidance. The rule "Do not cite or link `plans/`"
  also applies to a bundle file of any repo. Cite upstream code, and the code of another repo, with
  a GitHub permalink. The permalink must pin a full 40-character SHA on the default branch of that
  repo. The next bullets give the other forms.
- Cite an untracked plan or note of your repo as `the untracked <topic> plan of <repo> (secondary)`.
  Do not write its path or an item number. `verify` gives a finding for each line of a bundle file
  that contains `plans/` ([Session steps](hand-over.md#session-steps)).
- If the upstream source gives only a tag, find its SHA with `git rev-list -n 1 <tag>`. Make sure
  that the SHA is on the default branch with
  `git merge-base --is-ancestor <sha> origin/<default-branch>`. Write the SHA, then the tag.
- A commit that is not on the default branch of its repo is a secondary source. Give the repo, the
  full SHA and the branch.
- For a file of a released package, give the package name, the version, the name of the
  distribution file and the path of the file in the distribution. Example: `mediapipe==0.10.14`,
  `<wheel file name>`, `mediapipe/python/solutions/hands.py:79-83`.
- A file that git does not track is not evidence ([Parity](parity.md)). Cite the committed script
  that makes the file and the commit of the script. Give the full SHA-256 of the file.
- Cite a recorded proposal by its path `specs/model-sidecar/proposals/<slug>/proposal.md` and its
  entry `ADR-<ID>`. Cite a proposal that is not recorded by its exporter and its slug, then write
  `(not recorded, secondary)`.
- Do not cite a bundle. Cite the tracked copy of its file ([Location](hand-over.md#location)).
- A GitHub permalink to a repo of a freemocap exporter is allowed. This is also true when the repo is
  private ([Private data](../../../AGENTS.md#8-private-data)).
