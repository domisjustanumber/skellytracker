# Rules

- The spec is normative. Do not change its meaning in exporter docs or code.
- If a model property does not map exactly to the spec, do not use an approximate mapping. Write a
  change proposal (phase 2) and stop.
- Known case: an ROI refiner is a gap. An ROI refiner is a model that gives a region of interest to
  the next model, for example a hand re-crop model. Do not describe it as a pose estimator with two
  fake keypoints.
- The evidence for a row is an upstream file and line, an upstream config key, or a read of the ONNX
  graph (the command, and the node or tensor name). A plan, a paper, a README, the notes of an
  exporter and a spec reference example are secondary sources. Mark a secondary citation with
  `(secondary)`. A row that has only a secondary source is `unverified`. The next two bullets give
  the exceptions.
- A `near-miss` or a `gap` compares the property with the spec text. If only a secondary source shows
  the property, still give the row its `near-miss` or `gap` verdict. Mark the source `(secondary)`.
  Name the missing primary evidence in the row. The proposal of the row names it in part 1. Before
  the user accepts the proposal, part 1 must cite the primary evidence.
- A value that the exporter chooses has no upstream evidence. Examples are a name, a rule for the
  YAML file and a path. Judge its row against the spec only. Cite the exporter code that writes the
  value. If no such code exists, cite the exporter plan with `(secondary)`, or write
  `none yet (no code)`. Such a row is not `unverified` only because the code does not exist or you
  cannot read it. The model intake template lists these rows (heading "Verdicts").
- Do not publish a `vNEXT` sidecar to a shared or remote folder (see "Publishing").
