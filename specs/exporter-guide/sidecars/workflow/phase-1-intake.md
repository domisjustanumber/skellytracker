# Phase 1: can the current spec describe the model?

Fill `../freemocap/skellytracker/specs/sidecar/templates/model-intake.md`. Write the result to
`plans/sidecar-intake-<model>.md`. The skill `author-sidecar` gives the order of the steps.

1. List every property of the runtime contract of the model. Use three sources:
   - the ONNX graph: each input and each output;
   - the upstream preprocessing pipeline: each transform step, in order;
   - the upstream postprocessing: each decode step, in order.

   An upstream step that does nothing for this model is also a row. The row gives the evidence that
   the step does nothing.

   The runtime contract starts at the inputs of the model: the source image, and the box for
   `affine_person_crop`. It ends at the decoded outputs in source-image coordinates. An upstream step
   before or after the contract is also a row, with the verdict `out of scope`.
2. For each row, write:
   - the property;
   - the upstream evidence (see "Rules");
   - the section ID (the `id` in the front matter of the section file);
   - the sidecar value;
   - a verdict.
3. Give each row one of these verdicts:
   - `exact`: the section describes the property with these values.
   - `near-miss`: the spec has a section and a field for the property, but no value describes the
     property exactly. A detail differs, for example the rounding, the pixel centres, the arithmetic
     precision, the order of steps or the threshold comparison. A detail that the spec does not define
     is also a near-miss when it changes the output for some input. A name or a path changes no
     tensor and no decoded output, so its row is never a `near-miss`.
   - `gap`: the spec has no section and no field for the property, for example a rotated crop, a
     border mode or a role for an ROI refiner. A property that the spec calls out of scope, or that the
     spec lists in "Considered and deliberately not added"
     (`../freemocap/skellytracker/specs/sidecar/changelog.md`), is also a gap.
   - `unverified`: you do not have the evidence for a verdict. Name the missing evidence in the row. If
     you expect a verdict, write it there too.
   - `out of scope`: the step is before or after the runtime contract of this model. Examples: a step
     that makes the box from the outputs of another model, a gate that decides if the model runs, or a
     choice that uses an earlier frame.

   In each row that is not `exact`, write what differs or what is missing.

   To choose between `near-miss` and `gap`, find the section and the field that hold the property. If
   no section and no field hold it, the verdict is `gap`. If a field holds it but none of its values
   describes the upstream, the verdict is `near-miss`.
4. Continue as follows. A `near-miss` row or a `gap` row comes before an `unverified` row:
   - A `near-miss` or `gap` row: go to phase 2 for that row (the skill `propose-sidecar-change`). A
     near-miss is a gap. Do this also when other rows are `unverified`. List those rows in the final
     verdict.
   - An `unverified` row: get the missing evidence. Then give the row its verdict.
   - An `out of scope` row: write no proposal. Tell the user about the row when you stop. The user
     decides if the spec must describe such steps.
5. If no row is `near-miss` or `gap`:
   - The sidecar writer code of the exporter writes the sidecar (see "Sidecar YAML" and "Path"). Do
     not write the sidecar by hand.
   - If you cannot change the writer code yet, write the exact YAML in the section "The sidecar" of
     the intake. It is a draft. A skellytracker session does not use a draft as a spec example.
   - If a row is `unverified`, use the value that you expect for that row. Do not change the writer
     code for that row. Mark each result that depends on the row as provisional.
   - Walk the validation checklist (see "Validation").
   - Prove parity (see "Parity").
6. Write the final verdict:
   - `describes`: every row is `exact` or `out of scope`, and parity passes.
   - `does not describe`: a row is `near-miss` or `gap`, also when other rows are `unverified`.
   - `pending`: no row is `near-miss` or `gap`, but a row is `unverified` or parity is `to run`.

   If parity fails, you missed or misjudged a property. Go back to step 1 and find it. Until you find
   it, the verdict is `pending`. Do not make the tolerance larger to pass.
