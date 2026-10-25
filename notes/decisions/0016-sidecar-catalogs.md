# 0016 — Sidecar catalogs: source, reference hashes, roots, discovery and the capability check

**Status:** absorbed into [`sidecar/README.md#section-map`](../../specs/sidecar/README.md#section-map), 2026-10-25 (user; the absorption review).

This decision is accepted before its spec text and its code exist. A later content change adds
the normative text to the spec. Implementer guidance follows that change. The code waits for the
implementation stage, in which skellytracker implements the spec ([0014](0014-spec-lifecycle.md)).
This decision changes no file under `skellytracker/`.

## Decision

### Goal

The goal: skellytracker must list its available models from one or more sidecar roots. A root is a
local folder (the package is one of them) or a Hugging Face repo. It must also list a model from a
sidecar and ONNX files that a user gives.

Today, each detector module loads one sidecar from a fixed path when Python imports the module. The
module then registers its detector class under a hand-chosen key. For example, the key `rtmpose`
selects the RTMW whole-body detector.

### Source

- A sidecar gets a new top-level `source` mapping with two fields:
  - `name` is the name of the library that wrote the sidecar. Examples: an exporter package such as
    `openmmlab-exporter`, or `skellytracker`.
  - `version` is the version of that library, for example `0.1.0`.
- `source` is required at `vNEXT`.
- A legacy sidecar (`schema_version < vNEXT`) has no `source`. Its default is
  `{name: skellytracker, version: <schema_version>}`.
- The catalog key is `<model_id>@<source.name>`, for example `rtmw-wholebody@openmmlab-exporter`.
- The catalog can find more than one version of one key. Then the newest `source.version` wins. The
  catalog compares versions in PEP 440 order. It lists the other versions as superseded.
- A config can pin a version with `<key>==<version>`. A pin wins over the newest version.
- Two sidecars can have the same key and the same version but different file bytes. Then that catalog
  entry is unavailable. The reason names the two paths.
- The name `skellytracker` is reserved for the package root. A sidecar in a different root with
  `source.name: skellytracker` is unavailable. Thus a user folder cannot silently replace a model that
  skellytracker ships.
- A legacy sidecar gets the name `skellytracker` by default. Thus **a legacy sidecar loads only from the
  package root**. In a local folder or a Hugging Face repo, the catalog lists it as unavailable with this
  reason:

  ```text
  schema_version <v> is older than vNEXT and has no `source`; legacy sidecars load only from the skellytracker package. Regenerate it at vNEXT with a `source` field.
  ```

- One key can be in more than one root. Then the catalog logs the root of the entry that it uses.
- Each run records three values in its output metadata: the chosen key, its `source.version` and the
  SHA-256 of the sidecar file. Thus a result names exactly the sidecar that made it.

### Reference hashes

- At `vNEXT`, a `$ref` mapping holds exactly two keys: `$ref` and `sha256`.
- `base` uses the same form: `base: {$ref: <path>, sha256: <hash>}`.
- `sha256` is the SHA-256 of the bytes of the target file. The host checks the hash before it parses the
  file.
- The hash covers the exact bytes. Sidecars and fragments must be UTF-8 without a BOM, with LF line
  endings. A file with CRLF line endings fails with an error that says so.
- Hashes are required on every `$ref` and every `base` at `vNEXT`. This rule applies in every root,
  also in the package root.
- A fragment that refers to a different fragment also holds the hash of that fragment. Thus the bytes of
  the top sidecar pin the full tree.
- A target path must stay inside the root of the file that refers to it.
- The host gets each fragment from that same root: a local folder, or the same Hugging Face repo
  snapshot.
- A tool fills in the hashes (see [Tools and line endings](#tools-and-line-endings)).
- Legacy sidecars keep references without hashes. The sidecars in the package are legacy today. They get
  hashes only when the implementation stage moves them to a release `schema_version`.

### Artifact hashes

- Every ONNX artifact has a SHA-256 at `vNEXT`:
  - A new field `sha256` goes with `filename`. It is the SHA-256 of the file that `filename` names.
    Every artifact has `filename`, so every artifact has `sha256`.
  - An artifact with `url` also has `url_sha256`, as today. When `url` points to an archive,
    `url_sha256` is the hash of the archive and `sha256` is the hash of the ONNX file in it.
- Thus the ONNX files next to a sidecar in a local folder or a Hugging Face repo also have a hash.
- The host verifies a hash when the file is present or when it downloads the file.
- The spec's reference examples name ONNX files that nobody can download. An example that comes from an
  exporter that writes real hashes keeps those hashes. All other examples use one reserved placeholder,
  64 zeros:

  ```text
  0000000000000000000000000000000000000000000000000000000000000000
  ```

- The placeholder is valid only in the spec's examples. A sidecar in any other location that holds the
  placeholder is invalid.

### Roots

- The spec's `{cache_dir}` gets the new name `{sidecar_root}`. A sidecar root is a folder that follows
  the [storage layout](../../specs/sidecar/format/file-layout.md#storage-layout).
- The roots are:
  - the package root, `skellytracker/core`;
  - each local folder that a user adds;
  - each Hugging Face repo snapshot.
- Hugging Face snapshots stay in the Hugging Face cache.
- The ONNX download cache for `url` artifacts stays at `~/.cache/skellytracker/models`
  ([0002](0002-sidecars-tracked-in-package.md)). It is not a sidecar root.
- The code keeps the name `cache_dir` until the implementation stage.

### Discovery

- In every root, a YAML file is a sidecar when its top level has `schema_version` and a `model_id`. The
  `model_id` must be equal to the file name without `.yaml`.
- Every other YAML file is not a sidecar. Examples: skeleton fragments, canonical mappings and MediaPipe
  point lists.
- This rule is true for every YAML file in the package today (see [Evidence](#evidence)).

### Remote roots

- A remote root is a Hugging Face model repo. Its file tree follows the storage layout.
- A remote root has no index file. The catalog lists the files through the Hugging Face API.
- The config names the repo id and a commit revision. This revision is the pin.
- An explicit refresh command moves the pin to the head of the default branch. The refresh downloads
  only the YAML files (`allow_patterns=["*.yaml"]`).
- The host downloads an ONNX file at the pinned revision when a run uses the file for the first time.
  Then the host checks the file against its hash.
- At startup, skellytracker reads only the Hugging Face cache. Thus offline use works, and the config
  records the exact commit.
- A configured repo can have no refresh yet. Then the catalog lists it as "not fetched".
- Do not publish a `vNEXT` sidecar to a shared or remote root. No release can load it. The release step
  that replaces `vNEXT` is in [0014](0014-spec-lifecycle.md#release-step). After that step, the
  exporters regenerate their sidecars with the release version. [Development builds](#development-builds)
  gives the one exception.

### Hugging Face cache paths

- In the Hugging Face cache, each file under `snapshots/<rev>/` is a symlink to a file in `blobs/`.
- Today `load_sidecar` calls `path.resolve()`. The resolver then resolves each `$ref` against the folder
  of the resolved file. It also checks that the result stays inside the root. When the host follows the
  symlinks, both steps fail. Two more steps in `load_sidecar` also fail: the default root, and the check
  of the file name against `{model_id}.yaml`. The resolved file is `blobs/<hash>`.
- The implementation stage must do one of these two things:
  - resolve paths inside the snapshot, and not follow symlinks;
  - download the snapshot to a plain folder (`snapshot_download(local_dir=...)`).
- On Windows without developer mode, Hugging Face copies the files and does not make symlinks. Thus the
  fault does not show on such a machine.

### Development builds

- A development build of skellytracker loads `vNEXT` sidecars. A development build has a version with a
  pre-release tag, or an explicit opt-in setting.
- A release does not load `vNEXT` sidecars.
- The implementation stage can use a private Hugging Face test repo.

### User models

- A user adds a local folder of sidecars. The catalog scans the folder as a root.
- A user can also give one sidecar and its ONNX files. They must be in one folder. The catalog scans
  that folder as a root that holds one sidecar.
- The ONNX files are next to their sidecar, with the names that `filename` gives.

### Capability check

- The catalog lists a sidecar as unavailable, with the reason, when one of these is true:
  - the sidecar uses a spec section that skellytracker does not implement;
  - its `schema_version` is newer than the installed release.
- An attempt to load an unavailable sidecar is an error. The error names the section or the version.
- The check uses the functions that normalize a resolved sidecar and match it to spec sections. The
  traceability tool `tools/sidecar_trace.py` (not written yet) gets these functions first. They are
  pure functions, so the implementation stage can move them into `skellytracker/core/sidecar/`
  unchanged. Then the traceability tool imports them from the package. Thus nobody writes a fourth copy
  of the rules (after the spec, `model.py` and the tool).
- A key that a hand-written detector claims (see [Detector dispatch](#detector-dispatch)) skips the
  section check. It is available exactly when that detector is installed.

### Detector dispatch

- A catalog entry maps to detector code by its role and its spec sections. A hand-chosen registry key
  does not select the code.
- The current `detector_type` keys of the sidecar detectors stay as aliases of
  `<model_id>@skellytracker`. Examples: `rtmpose` is an alias of `rtmw-wholebody@skellytracker`, and
  `yolox_person` is an alias of `yolox@skellytracker`.
- A hand-written detector can claim a catalog key. The generic path never handles a claimed key.
- YOLOX claims `yolox@skellytracker`. Its sidecar describes the native checkpoint
  ([0006](0006-yolox-native-contract.md)). But the YOLOX code does three things that its sidecar and the
  spec do not describe:
  - it changes the graph (`prepare_yolox_onnx`);
  - it selects its decode from the output shapes of the loaded graph;
  - it decodes a raw anchor grid.
- Without the claim, the YOLOX sidecar passes the capability check. The generic path then silently runs
  a different detector.
- Open work: export YOLOX again to a contract that the spec describes. That contract has a dynamic
  batch, no NMS in the graph and host `selection: nms`. Do a parity check. Then remove the claim.
- Sizes come from the `sizes` of the sidecar. An unknown size is an error, not a silent fallback.

### What goes where

- The spec text gets these parts: `source`; the reference hashes and the artifact hashes;
  `{sidecar_root}`; the layout of a root (local or Hugging Face); path containment for each root; the
  discovery rule; and the legacy behaviour.
- All other parts are skellytracker behaviour, not sidecar format. They go into implementer guidance
  ([0013](0013-spec-structure.md)) after the change that adds the spec text above. These parts are: the
  catalog key, the version order and the version pins; the Hugging Face pin, refresh and cache paths;
  development builds; root configuration; run metadata; the capability check; dispatch and aliases.
- The code waits for the implementation stage.
- Until the spec has the text above, the traceability tool `tools/sidecar_trace.py` uses the catalog
  key and the discovery rule as tool rules only.

### Tools and line endings

- The reference hash tool `tools/sidecar_refs.py` does not exist yet. A later change adds it to
  `tools/`, together with the traceability tool `tools/sidecar_trace.py`. The reference hash tool has
  two parts with different lives.
- The `--write <sidecar>` and `--check <sidecar>` commands are permanent. The implementation stage moves
  them into the package as a command and keeps a thin wrapper in `tools/`.
  - `--write` fills in `sha256` on every `$ref` and `base`. It works depth first, so the hashes inside a
    fragment are in place before the tool takes the hash of that fragment. It also fills in `sha256` on
    each `filename` artifact whose file is present.
  - `--write --placeholder` writes the reserved placeholder on an artifact that has no `sha256`. It
    never replaces a real hash.
  - `--write --source <name>==<version>` adds the `source` mapping when the file has none. It never
    changes a `source` that the file already has.
  - `--write` edits text. It inserts or updates only the `sha256` entries (in block mappings and in flow
    mappings) and the `source` block. It keeps every other byte, also comments and quotes. It never
    loads the YAML and writes it out again.
  - `--check` verifies every `$ref` and `base` hash. It verifies an ONNX hash only when the ONNX file is
    present. It reports a CRLF file or a BOM as a separate error. It accepts the placeholder only in a
    file under `specs/sidecar/examples/`, the examples folder after the spec is split into section files.
  - These commands use only the standard library and PyYAML. They do not import `skellytracker`. Thus an
    exporter can run them with its own Python.
- The `resolve(path, root)` function of the tool is a temporary work-around. Today the resolver refuses
  a key next to `$ref` and a `base` that is not a string. The work-around verifies the hashes. It copies
  the tree to a temporary folder, removes the hashes and changes each `base: {$ref, sha256}` back to
  `base: <path>`. Then it calls the unchanged `resolve_sidecar_composition` on the copy. It accepts files
  with hashes and files without hashes. The implementation stage adds hash checks to `resolution.py` and
  deletes the work-around.
- `.gitattributes` sets `*.yaml` and `*.yml` to `text eol=lf`. Thus a new Windows checkout has the same
  bytes as git, Linux CI and Hugging Face. A working copy from before this change keeps CRLF (see
  [Not repeated](#not-repeated)).
- `.gitattributes` also sets `specs/sidecar/TRACEABILITY.md` to `text eol=lf`. The traceability tool
  will generate this file, so the file must have the same bytes on every machine.

### Exporter impact

- Each exporter must write `source` with its package name and its version. For example, the values for
  OpenMMLab-Exporter are `name: openmmlab-exporter` and `version: 0.1.0` (from its `pyproject.toml` on
  2026-10-22). OpenMMLab-Exporter does not write `source` yet.
- Each exporter must write UTF-8 sidecars without a BOM, with LF line endings.
- Each exporter must fill in `sha256` on every `$ref`, every `base` and every `filename` artifact. It can
  use `tools/sidecar_refs.py --write` when that tool exists.
- Each exporter must regenerate its `vNEXT` sidecars after the spec gets the text for `source` and the
  hashes. Until then, sidecars without these fields are accepted.
- When the spec gets that text, the spec's examples get `source` and all hashes. Then each example
  differs from its exporter copy until that exporter regenerates. This difference is expected.
- This decision changes no file in an exporter repo. The rules for the exporters are in the exporter
  guide of this repo ([specs/exporter-guide/sidecars/README.md](../../specs/exporter-guide/sidecars/README.md)).

## Reason

- **Source.** `model_id` is not unique across sources, and the storage layout gives each `model_id` one
  path. A catalog that merges the package, a remote root and a user folder must keep two sidecars with
  one `model_id` apart. `source.name` does that. `source.version` puts the versions of one key in order.
- **Reserved name and log.** With the reserved name `skellytracker`, a user folder or a remote repo
  cannot silently replace a model that skellytracker ships. For each key, the log shows the root of the
  entry that the catalog uses.
- **Run metadata.** The key, the version and the sidecar hash let a user find the exact sidecar that made
  a result.
- **Reference hashes.** Today `$ref` and `base` must stay inside one `cache_dir`, and its default is the
  package folder `skellytracker/core`. A sidecar outside the package cannot use the shared fragments.
  When each root holds its own fragments, the hashes pin the exact bytes of each fragment. Thus a
  fragment cannot change the meaning of a sidecar without a change to the sidecar bytes.
- **UTF-8 and LF.** A hash of bytes needs the same bytes on every machine. A Windows checkout writes
  CRLF line endings, so the hash would be different on Windows, on Linux CI and on Hugging Face.
- **Artifact hashes.** An ONNX file next to a sidecar has no hash today. Only a downloaded file has one
  (`url_sha256`). The new `sha256` gives every artifact a hash.
- **Placeholder.** The placeholder lets the spec's examples obey the hash rule without real ONNX files.
  The "only in the examples" rule makes sure that the placeholder cannot hide an absent hash in a real
  sidecar.
- **Sidecar root.** "Cache dir" names two different folders today. The new name `{sidecar_root}`
  removes the double meaning.
- **Discovery.** Nothing defines which YAML files are sidecars, and the package tree also holds other
  YAML files. Every sidecar has `schema_version` and a `model_id` equal to its file name. No other YAML
  file in the package has `schema_version`.
- **Remote roots.** The Hugging Face API lists the files of a repo, so a remote root needs no index file.
  The pin records the exact commit in the config. Startup reads only the cache, so offline use works.
  The refresh downloads only YAML, and a run downloads only the ONNX files that it uses.
- **Cache paths.** `load_sidecar` follows symlinks today. In a Hugging Face snapshot, that breaks the
  `$ref` resolution and the root check.
- **Development builds.** The implementation stage must load and test `vNEXT` sidecars before the
  release that ships the spec. A release must not load them, because `vNEXT` is not a version.
- **Capability check.** The check tells a user why a model is not available before a run starts. It uses
  the same functions as the traceability tool, so the rules are not written a fourth time.
- **Dispatch and claims.** Dispatch by role and sections lets a new model run with no new Python. A
  claim keeps a hand-written detector out of the generic path when its code does things that no spec
  section describes.
- **Unknown size.** A silent fallback hides a wrong size name. An error shows it.
- **What goes where.** The spec defines the sidecar format. The catalog is skellytracker behaviour, so
  it goes into implementer guidance.
- **Text edits in `--write`.** The examples are copies of exporter sidecars. Only a small set of edits
  is allowed ([specs/sidecar-implementation-plan.md](../../specs/sidecar-implementation-plan.md#reference-examples),
  "Reference examples"). A text edit adds the hashes and `source` and keeps all other bytes.

## Evidence

Checked in the code on 2026-10-22.

- **`model_id` is not unique across sources.**
  - `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` has
    `model_id: rtmw-wholebody` (line 3). Its `url` values (line 74 and after) point to the rtmlib
    `onnx_sdk` archives on `download.openmmlab.com`. The spec says this under
    [RTMW WholeBody](../../specs/sidecar/examples/README.md#rtmw-wholebody-openmmlab-exporter-top-down-pose).
  - OpenMMLab-Exporter writes the same `model_id`: `rtmw/identity.py:26` has
    `FAMILY = "rtmw-wholebody"`, and `rtmw/sidecar.py:211` sets `"model_id": FAMILY`. The spec's RTMW
    reference example also has `model_id: rtmw-wholebody`.
- **The storage layout gives each `model_id` one path.** The file name is `{model_id}.yaml`
  ([File extension and naming](../../specs/sidecar/format/file-layout.md#file-extension-and-naming)). The family and
  the part set the leaf folder ([Storage layout](../../specs/sidecar/format/file-layout.md#storage-layout)).
  `loader.py::load_sidecar` rejects a file whose name is not `{model_id}.yaml` (lines 40-46). Thus two
  sidecars with one `model_id` cannot be in one root that follows the storage layout.
- **A sidecar cannot carry its source today.** `SidecarModel` extends `_StrictModel`, which sets
  `model_config = ConfigDict(extra="forbid")` (`skellytracker/core/sidecar/model.py:33`). A `source` key
  fails validation.
- **Detectors use fixed paths and hand-chosen keys.**
  `rtmw_wholebody_detector.py:31-32` loads `rtmw-wholebody.yaml` at import. Line 162 registers
  `KEYPOINT_DETECTOR_REGISTRY["rtmpose"] = RTMWWholebodyDetector`. `yolox_person_detector.py:48-49`
  loads `yolox.yaml`, and line 197 registers `OBJECT_DETECTOR_REGISTRY["yolox_person"]`.
  `detector_base_classes.py::build_object_detector` and `build_keypoint_detector` find the class by
  `config.detector_type`.
- **References must stay inside one `cache_dir`.**
  - `skellytracker/core/sidecar/resolution.py::_require_within_cache_dir` (lines 95-100) raises
    `SidecarRefError` ("Path ... escapes cache_dir ...") when a target is not under `cache_dir`.
    `_resolve_relative_path` (lines 89-92) calls it for every `$ref` and `base` target.
  - `skellytracker/core/sidecar/loader.py::_default_cache_dir` (lines 58-64) returns the first ancestor
    folder named `core`. It raises `ValueError` when there is none. For a package sidecar, the root is
    `skellytracker/core`.
  - The spec says that a `$ref` or `base` path must never escape above `{cache_dir}`
    ([File composition](../../specs/sidecar/format/composition.md)).
- **The resolver refuses the hashed form.** `resolution.py::_resolve_refs` (lines 71-77) raises when a
  `$ref` mapping has any key other than `$ref`. `_load_and_resolve` (lines 59-60) raises when `base` is
  not a string. Thus `{$ref, sha256}` needs a resolver change, and the tool needs a temporary
  work-around until then.
- **"Cache dir" names two folders.** The spec's `{cache_dir}` defaults to `skellytracker/core`
  ([Storage layout](../../specs/sidecar/format/file-layout.md#storage-layout)).
  `skellytracker/core/sessions/model_registry.py:26` sets
  `DEFAULT_CACHE_DIR = Path.home() / ".cache" / "skellytracker" / "models"`. `_resolve_from_url`
  (lines 151-155) keeps a downloaded ONNX file flat, as `cache / (expected_filename or filename)`. This
  folder does not follow the storage layout.
- **An ONNX file next to its sidecar has no hash.** `PrecisionArtifact` (`model.py:389-399`) requires
  `url_sha256` only when `url` is present. `runtime.py::sidecar_model_spec` builds a `local_path` source
  from `sidecar_dir / artifact.filename` when there is no `url`. `model_registry.py::resolve_model_path`
  does not verify a `local_path` source (docstring, lines 52-57).
- **Discovery.** The package tree has 22 tracked YAML files. 5 have `schema_version` and a `model_id`
  equal to the file name: `yolox`, `rtmw-wholebody`, `rtmpose-body`, `rtmpose-hand` and `rtmpose-face`.
  The other 17 have no `schema_version`: 8 skeleton fragments under `detectors/shared/skeletons/`, 6
  canonical mappings and 3 MediaPipe point lists. The spec says that fragments under `detectors/shared/`
  have no `schema_version` ([Storage layout](../../specs/sidecar/format/file-layout.md#storage-layout)). It does not
  give a rule that tells a sidecar from a different YAML file. Its storage layout does not show the
  canonical mappings and the MediaPipe point lists, which are in the leaf folders next to the sidecars
  (for example `rtmpose/body/rtmpose_body_to_canonical_mapping.yaml`).
- **`vNEXT` is not a version.** `skellytracker/core/sidecar/versioning.py:11` has
  `_VERSION_RE = re.compile(r"^v(\d{4})\.(\d{2})\.(\d+)(?:-([A-Za-z0-9.]+))?$")`.
  `SidecarModel._check_schema_version_pattern` (`model.py:476-486`) calls `parse_skellytracker_version`
  and `require_stable_version`. Thus validation rejects `"vNEXT"`, and also a `schema_version` with a
  pre-release tag. `load_sidecar` also rejects a `schema_version` that is newer than the installed
  `__version__` (`loader.py:48-53`). The installed version is `"v2024.09.1019"`
  (`skellytracker/__init__.py:4`).
- **The loader follows symlinks.** `loader.py:27` calls `Path(path).resolve()`.
  `resolve_sidecar_composition` resolves the path again and checks it against `cache_dir`
  (`resolution.py:40-42`). Each `$ref` and `base` resolves from the folder of the resolved file
  (`resolution.py:61`, `:81` and `:90`). For a symlink in a Hugging Face snapshot, the resolved file is
  in `blobs/`. Thus the first root check fails, and a relative `$ref` starts from the wrong folder.
  Also, `_default_cache_dir` finds no ancestor named `core` in the Hugging Face cache, and the basename
  check (`loader.py:40-46`) sees the blob name, not `{model_id}.yaml`.
- **Unknown sizes fall back silently.** `RTMWWholebodyDetectorConfig.input_size`
  (`rtmw_wholebody_detector.py:47-53`) returns `(256, 192)` when `model_name` is not a key of the
  sidecar's `sizes`. `RTMWWholebodyDetector.model_spec` (line 144) raises `ValueError` for the same name.
  The configs of RTMPose body, hand and face and of YOLOX have the same fallback, with their own values.
- **Windows checkouts get CRLF.** Before this decision, `.gitattributes` held only `* text=auto`. This
  checkout has `core.autocrlf=true`. `git ls-files --eol` shows `i/lf w/crlf` for the package
  sidecars: git stores LF, and the working copy has CRLF. In `yolox.yaml`, all 62 line ends in the
  working copy are CRLF. `parse_sidecar_file` opens the file in text mode (`open(path, "r")`,
  `resolution.py:26`), so the loader does not see the difference. A hash of the bytes does.
- **YOLOX needs its own code.** `YoloxPersonDetector.model_spec` passes `prepare=prepare_yolox_onnx`
  (`yolox_person_detector.py:193`). `_yolox_dynamic_batch.py::prepare_yolox_onnx` (line 366) makes the
  batch dimension dynamic and removes the NMS subgraph. `yolox_decode.py::yolox_detection_decode`
  (lines 93-141) selects the decode from the loaded graph: two outputs give `decode_prenms`, a last
  dimension of 5 gives `decode_nms_baked_in`, and a last dimension of 4 gives
  `_decode_yolox_raw_anchor_grid`. `yolox.yaml` declares one `detections` output and
  `requires_nms: false`. Every field of `yolox.yaml` is in a spec section, so a section check alone
  cannot find that YOLOX needs its own code. [0006](0006-yolox-native-contract.md) has the details.

## Alternatives rejected

- **A catalog key from `model_id` alone, for example `sidecar:{model_id}`.** The implementation plan
  suggested this key for the generic detector
  ([specs/sidecar-implementation-plan.md](../../specs/sidecar-implementation-plan.md#m6--generic-sidecar-driven-detector-drop-in-a-yaml--onnx-no-new-python),
  M6 Part A). `model_id` is not unique across sources, so two sources collide.
- **An index file in a remote root, or a hand-kept model list as the runtime catalog.** A scan of a
  root finds its sidecars, and the Hugging Face API lists the files of a repo. A second list can go out
  of date. The docs inventory of the spec's examples (`specs/sidecar/inventory.yaml`, which is added
  when the spec is split into section files) is not a runtime catalog. skellytracker never reads it.
- **The generic path for YOLOX.** The YOLOX sidecar passes a section check, but the generic path would
  run a different detector. The claim stops that.
- **A default size for an unknown size name.** The default hides the fault.
- **A `--write` that loads the YAML and writes it out again.** That changes comments, quotes and other
  bytes. An example must stay a copy of its exporter sidecar, with only the allowed edits.

## Not repeated

- Do not key the catalog by `model_id` alone.
- Do not take a hash after a text-mode read. `parse_sidecar_file` reads in text mode and does not see
  CR characters. Hash the bytes of the file.
- Do not call `Path.resolve()` on a path inside a Hugging Face snapshot. It goes to `blobs/`.
- Do not test Hugging Face cache paths only on Windows without developer mode. There the files are
  copies, and the symlink fault does not show.
- Do not treat `{sidecar_root}` as the ONNX download cache. They are different folders.
- Do not publish a `vNEXT` sidecar to a shared or remote root. [Development builds](#development-builds)
  gives the only exception.
- Do not put the placeholder hash in a sidecar outside the spec's examples.
- Do not download ONNX files in a refresh. A refresh gets only `*.yaml`.
- `url_sha256` is the hash of the bytes at `url`, which can be an archive. `sha256` is the hash of the
  file that `filename` names.
- A working copy from before the `.gitattributes` change keeps CRLF. `git checkout -- '*.yaml'` does not
  change it, because git sees no change in the files. On a clean tree, remove the YAML files from the
  index and check them out again (`git rm --cached -q -- '*.yaml'`, then `git checkout HEAD -- '*.yaml'`)
  before you take a hash. A test on 2026-10-22 (git 2.43.0, in a test repository) confirmed these
  commands.

_Edited 2026-10-24 (this PR): link repair._
