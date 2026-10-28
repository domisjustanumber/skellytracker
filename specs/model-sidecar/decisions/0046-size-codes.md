# 0046 — Spec change: size-codes

**Status:** proposed, 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `size-codes`. The eight parts
are in [`specs/model-sidecar/proposals/size-codes/proposal.md`](../proposals/size-codes/proposal.md).

- **Section:** a new section `common.sizes` ("Size keys", file `specs/model-sidecar/common/size-keys.md`,
  kind `common`). The change also edits `common.sizes_and_artifacts`, `common.identity`,
  `format.file_layout`, `format.composition`, `format.versioning`, the section map, the changelog
  and two guidance files. Part 8 gives the other choice: a change to `common.sizes_and_artifacts`.
- **Change:** An alias table joins the spellings of one size into one code: `n`, `t`, `s`, `m`, `b`,
  `l`, `x`, `2xl`, `h`. A key of `sizes` writes the code, not the alias (`m`, not `medium`). A word
  that is not in the table is a free word, and it stays valid (`lite`). A key can add input dims
  (`l-256`, `m-256x256`), be dims alone (`192`), or be the reserved key `default`. Rules
  `V-common.sizes-1` to `-4` check the grammar, the dims against `input.shape`, one form for each
  word in one sidecar, and `default` only as the one key.
- **Version:** `vNEXT`. A sidecar with `schema_version < vNEXT` keeps the old rule: any lowercase
  token, with hyphens. The new section has a "Legacy behaviour" heading.
- **Models:** all sizes of all exporters. OpenMMLab-Exporter `rtmdet-person` renames `nano` and
  `medium` to `n` and `m`. Roboflow-Exporter `rfdetr` writes `vNEXT`, so it must rename. The keys of
  `rtmw-wholebody133` and `rtmo-coco17-body7` stay valid. Ultralytics-Exporter and Qualcomm-Exporter
  write a legacy version, so they do not change now. The reference examples `rtmdet-person.yaml`,
  `yolo26.yaml` and `yolo26-body.yaml` become invalid. The five package sidecars do not change.
- **On acceptance:** this entry supersedes no entry.
- **Related:** `model-id-suffix` ([0025](0025-model-id-suffix.md)) is a soft dependency: the
  file-layout examples use its `model_id` form, but this proposal can land first with the current
  names. These proposals edit the same spec text, and the second content PR rebases on the first:
  `roi-transform-and-source` ([0020](0020-roi-transform-and-source.md)), `roi-refiner-role`
  ([0047](0047-roi-refiner-role.md)), `simcc-score-rule` ([0024](0024-simcc-score-rule.md)),
  `heatmap-decode-refinement` ([0038](0038-heatmap-decode-refinement.md)),
  `affine-crop-arithmetic` ([0037](0037-affine-crop-arithmetic.md)), `normalize-arithmetic`
  ([0043](0043-normalize-arithmetic.md)), `keypoint-visibility`
  ([0039](0039-keypoint-visibility.md)), `pose-decode-flip-test`
  ([0045](0045-pose-decode-flip-test.md)), `landmark-extra-outputs`
  ([0021](0021-landmark-extra-outputs.md)) and `landmark-depth-divisor`
  ([0022](0022-landmark-depth-divisor.md)).

## Reason

- The spec gives no spelling for a size. It allows any lowercase token
  (`common/sizes-and-artifacts.md:33`), and the guide tells the exporter to use the upstream name.
  Upstream libraries use letters (`yolo26n.pt`, `rtmo-m`) and words (`rtmdet_nano`,
  `ViTPose_base`).
- Thus one size has two keys. Six shipped families have a medium size. Four write `medium` and two
  write `m`. The proposal cites the exporter code of each key at a named commit. These code lines
  are primary evidence.
- An exporter CLI that filters by key shows the effect. In OpenMMLab-Exporter, `--sizes m` selects 2
  of its 3 medium-size families today.
- The hyphen examples `l-m` and `x-l` of the current text are not sizes of the end model. They come
  from the distilled RTMW checkpoints (teacher `l`, student `m`). The spec also gives no form for a
  key that holds an input size.

## Evidence

- Parity (part 5): none. A size key changes no tensor, no preprocessing and no decoded output, so no
  model run can show a difference. The proposal names an OpenMMLab-Exporter test that checks each
  identity `size_key` against the table. That test is planned. It is not written, and it has no
  commit.
- Vectors (part 4): 191 cases, written by hand from part 2, `unverified: no host implementation in
  an exporter or in skellytracker`. A run against the reference code gave 191 of 191 pass. The
  runner is a scratch script that is not committed. The result is not evidence.
- The reference code (part 3) uses only the Python standard library. Its source commit is none (no
  host code).

## Open work

See [Open work](README.md#open-work).
