---
name: update-docs-site
description: Use this skill in skellytracker when a change can make a page of the docs site `skellytracker-docs/` false, for example a change of a public name, a signature, a default, a CLI flag, an extra, a supported Python or OS, a built-in pipeline, a reason code, the report format or the EP catalog. Use it also when you add, rename or delete a docs page, and when the commit hook prints a docs site reminder.
---

# Keep the docs site true

This skill uses ASD-STE100 Simplified Technical English.

The docs site is the Docusaurus site in `skellytracker-docs/`. Each page took its facts from the
code and the specs of this checkout, and each Python example ran. A change of the public API must
change its page in the same commit. The bullet "The docs site" of
[`specs/sidecar-implementation-plan.md`](../../../specs/sidecar-implementation-plan.md#later)
states this rule.

## When it applies

Apply this skill when a commit changes one of these:

- a public name, a signature or a default of `skellytracker`, `skellytracker.core.pipelines`,
  `skellytracker.core.detectors` or `skellytracker.core.eps`;
- a CLI command or flag of `python -m skellytracker`, `skellytracker-eps` or the pipeline commands;
- an install extra, the supported Python versions or the supported OS;
- a built-in pipeline in `skellytracker/core/model_zoo/pipelines/`;
- a reason code in `skellytracker/REASON_CODES.md`, the report format of `certify()` or the EP
  catalog;
- the list of docs pages: a new page, a page with a new name or a deleted page.

The pre-commit hook `docs-site` prints a reminder when a commit changes a public API file and no
docs file. The reminder does not stop the commit. Not each change of such a file needs a page
change. Find the pages that state the changed fact, and decide.

## Page map

The pages are in `skellytracker-docs/docs/`. Search the pages for the changed name with Grep
before you use this map. A fact can be on more than one page.

| Page | It states |
|---|---|
| `intro.mdx` | What the package does, the built-in pipelines and the page list |
| `getting-started/installation.mdx` | Python and OS, the install commands, the extras, MediaPipe, the ONNX model files, the GPU EP packs, the install from source |
| `getting-started/quick-start.mdx` | The first run of each built-in pipeline, the recommended EP, the result of one call |
| `getting-started/processing-videos.mdx` | One video, synchronized videos of more cameras, a folder of images |
| `getting-started/running-demos.mdx` | The webcam demo with `--pipeline`, the command `validate`, the command `detectors` |
| `core-concepts/pipeline-overview.mdx` | The parts of a pipeline file, nodes and ports, `yolox-rtmw-wholebody`, load and check, the pipeline roots |
| `core-concepts/detectors.mdx` | The detector catalog, sidecars, `create_detector` |
| `core-concepts/running-modes.mdx` | `image`, `video` and `live`, frames, state between frames, refused calls, `set_params`, threads |
| `core-concepts/execution-providers.mdx` | The EP keys, the recommended EP, the EP packs and store, field-test EPs, the check rule, the EP errors |
| `core-concepts/outputs-and-keypoints.mdx` | The result of one camera, `CanonicalKeypoints`, `OutputBoxes`, the output schema, taps |
| `guides/certifying-a-system.mdx` | The levels of `certify()`, the plan, the quick checks, the check results, the report |
| `guides/choosing-a-pipeline.mdx` | The built-in pipelines side by side, calibration boards, your own pipeline |
| `guides/extending-skellytracker.mdx` | The user root, a new pipeline file, a new ONNX model, a new node type |
| `guides/gpu-setup.mdx` | The GPU needs of each EP, the pack install, the field-test opt-in, the quick check, the offline install, the exit codes of `skellytracker-eps` |
| `guides/multi-camera-batching.mdx` | The batch rules, many GPUs, sessions |
| `guides/temporal-smoothing.mdx` | `smooth_boxes`, `smooth_keypoints`, `redetect_trigger`, frame time |
| `technical/api-reference.mdx` | Each exported name with its signature, each record and each error |
| `technical/architecture.mdx` | The two specs, the entry points, the flow of a run, cameras and GPUs, the package layout |
| `technical/onnx-runtime-and-eps.mdx` | The session build, CPU threads, the preprocess place, JPEG frames, the batch, the exit codes |
| `technical/output-values.mdx` | The fields of each output value, padding rows, the output schema |
| `technical/timing-and-taps.mdx` | The timing spans, the taps, the command `run` |
| `development/index.mdx` | The development install, the checks, the lint, the CLI from source |
| `development/contributing.mdx` | The rules for a code change, a new model, a new pipeline or node type |
| `community.mdx` | The links to the issues, the main project and the roadmap |

`skellytracker-docs/blog/` holds the posts. The tool checks them as pages.

## Evidence

1. Take each fact from a file of this checkout: the code, a spec, a sidecar or a pipeline file.
2. Write no sentence that has no source. If you cannot find the source, remove the sentence.
3. Write no performance number unless a tracked file states it.
4. Run each Python example that you add or change on the CPU, with `uv run --no-sync python -B`.
5. Do not run an example that needs a GPU, `certify()`, an EP install or a webcam. Tell the user
   that it is "not run".
6. Never open a webcam.

## Language and MDX

1. Write each page in ASD-STE100 Simplified Technical English.
2. Write "system". Do not write "machine" or "PC".
3. Do not write a bare `{`, `}` or `<` outside code. MDX reads them as code.
4. Use relative links to pages, for example `../core-concepts/detectors`.
5. When a page gets a new name, delete the page with the old name in the same commit. Change each
   link to it.
6. Do not add an image of a camera frame
   ([Private Data](../../../AGENTS.md#8-private-data)).

## Checks

1. Run `uv run --no-sync python -B tools/check_docs_site.py`. It must print no finding. Its
   docstring gives its rules: each exported name is on the API reference page, each signature names
   an exported name, each page has a title, each relative link goes to a page file, and no page
   says "machine" or "PC".
2. If a name is exported but it is not public API, do not add it to the page. Add it to
   `UNDOCUMENTED` of the tool with its reason, and tell the user.
3. Build the site in `skellytracker-docs/`: run `npm ci --ignore-scripts`, then `npm run build`. A
   broken link or an MDX error fails the build. `npm ci` needs the network one time. Git ignores
   `node_modules/` and `build/`. If `node` is not installed, tell the user that the build did not
   run.

## Commit

1. Put the page changes in the same commit as the API change.
2. Load [`stack-commit`](../stack-commit/SKILL.md) before you commit.
