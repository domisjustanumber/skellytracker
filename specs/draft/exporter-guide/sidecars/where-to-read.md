# Where to read the spec

These steps apply in an exporter repo. They check the skellytracker checkout before each sidecar
task.

- Read the sidecar spec, the templates and the skills in the skellytracker checkout
  `../freemocap/skellytracker`. Read it only.
- That checkout must be on the branch `dom/sidecar-implementation` ("The branch" in
  `../freemocap/skellytracker/specs/model-sidecar/model-addition-workflow/reading-the-spec.md`).
  Examine the branch: `git -C ../freemocap/skellytracker branch --show-current`.
- If the command gives a different branch, stop. Do not change the branch. Tell the user the name of
  the branch, and ask what to do.
- Read the files as normal files. Then the relative links in the spec and in the skills resolve.
- If the folder `../freemocap/skellytracker` does not exist, stop. Ask the user which skellytracker
  folder to read. Then read only that folder, and write its path in the header of the intake or the
  proposal.
- Get the commit of the spec text that you read
  ("The commit of the spec text" in `../freemocap/skellytracker/specs/model-sidecar/model-addition-workflow/reading-the-spec.md`).
- Never edit a file in skellytracker.
- Never commit to skellytracker. Never change its branch.

## Files, path bases and links

Moved to
[model-addition-workflow/reading-the-spec.md](../../../model-sidecar/model-addition-workflow/reading-the-spec.md#read-the-spec).
That file gives the files to read, the path bases, the decision entries, the section IDs, the vectors,
the reference examples and the links to the spec. It applies to each contributor.
