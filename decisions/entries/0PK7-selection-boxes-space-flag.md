# 0PK7 — Each selection vector case names the space of its boxes

**Status:** absorbed into [`README.md`](../../specs/model-sidecar/README.md), [`implement-sidecar-section/SKILL.md`](../../.claude/skills/implement-sidecar-section/SKILL.md), [`tools/vector_formulas/post_det_decode.py`](../../tools/vector_formulas/post_det_decode.py), [`tools/tests/test_vectors.py`](../../tools/tests/test_vectors.py), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes no entry. It adds one key to the selection case form of
[ADR-8DSW](8DSW-vector-files-are-the-case-source.md) item 2. Each rule of
[ADR-8DSW](8DSW-vector-files-are-the-case-source.md) stays.

1. **The flag.** Each case of `specs/model-sidecar/vectors/post.det.selection.nms.yaml`,
   `post.det.selection.top_k.yaml` and `post.det.selection.none.yaml` must give
   `expect.boxes_xyxy`, then `expect.boxes_space`. `published` of
   `tools/vector_formulas/post_det_decode.py` sets both keys, and `make_vectors.py` writes them.
   `tools/vector_form.py` does not check the two keys. `test_box_key_follows_resize` of
   `tools/tests/test_vectors.py` checks the key order and the value of `boxes_space` in each landed
   case.
2. **The two values.** A `model_input` case gives no `params.resize`. It does not do shared steps 3
   to 5 of
   [Selection behaviour](../../specs/model-sidecar/post/detection-decode.md#selection-behaviour).
   It still does step 6, the confidence threshold. Its `boxes_xyxy` holds the kept boxes in
   model-input pixels. A `source` case gives `params.resize`. It also does shared steps 3 to 5: the
   unprojection, the clamp and the size filter. Its `boxes_xyxy` holds the final boxes in
   source-image pixels. Each box is the `output_xyxy` of `post.unprojection`, not its
   `source_xyxy`.
3. **A host reads the flag.** A host that runs these vectors must compare `boxes_xyxy` in the space
   that `boxes_space` names. It must not infer the space from the other keys.
4. **The case keys.** A `source` case must give `input_size` and `resize` in `params`, and `src_w`
   and `src_h` in `input`. These keys, and `box_scale` (as `scale`), `clamp_boxes` and
   `min_box_size`, have the same meaning as in section `post.unprojection`. A `model_input` case
   must not give `input_size`, `min_box_size`, `clamp_boxes`, `src_w`, `src_h` or a `box_scale`
   other than `pixel`. `unproject_clamp_and_filter` of `tools/vector_formulas/post_det_decode.py`
   calls `vector_form.defect` on such a case. It also calls it on a `source` case with
   `resize.method: affine_person_crop`, because a selection case gives no `bbox_xyxy`. On each
   `source` case, it runs the check `input-size-follows-resize` of `post.unprojection`.

## Reason

- The user decided on 2026-11-04: "[Keep] boxes_xyxy as-is and add another flag to signify
  model-input vs source". The user chose the option "In every selection case". The user saw this
  example: a 1920x1080 frame, a 512x512 model input and a centered letterbox. The model gives
  `[100, 150, 200, 250]` in model-input pixels. After the unprojection and the clamp, the box is
  `[375, 142.5, 750, 517.5]` in source pixels.
- The end-to-end cases pin the order of [ADR-17KN](17KN-one-selection-pipeline.md): NMS,
  `post_nms_top_k` and `top_k` come before the clamp and the size filter. Only a case that does
  steps 3 to 5 can show this order. Its boxes are in source pixels.
- Each shared step and each mode step is a host step. The model gives only the candidate rows, in
  `box_format` and `box_scale`. A `model_input` case does not do steps 3 to 5, and a `source` case
  does them. Thus, one `boxes_xyxy` key has two possible stop points. The flag names the stop
  point, so a host never compares boxes in the wrong space.
- `boxes_xyxy` stays in each case. Thus the sentence "A selection case always gives `boxes_xyxy`"
  of [ADR-8DSW](8DSW-vector-files-are-the-case-source.md) item 2 stays true.

## Consequences

- A host vector runner reads `boxes_space` in each selection case.
- An exporter agent that adds a selection case to its bundle runs `fill` before `pack`. `fill`
  writes the flag when the producer is the formula module of this checkout. A reference module for
  a selection section must return `boxes_space`, and it must do steps 3 to 5 for a case with
  `resize`. `fill` does not cross-check a bundle reference, so `land` and
  `test_box_key_follows_resize` find a missing flag.

## Evidence

- `tools/vector_formulas/post_det_decode.py`: `unproject_clamp_and_filter` (steps 3 to 5 through
  `post_unprojection.run`, and the guards) and `published` (`boxes_space`).
- `tools/tests/test_vectors.py`: `test_box_key_follows_resize`, the three guard tests and the
  `ANCHORS` of `size-filter-uses-source-pixels` and `nms-comes-before-the-clamp`.

## Alternatives rejected

- A separate key `boxes_source_xyxy` in the `source` cases: it breaks
  [ADR-8DSW](8DSW-vector-files-are-the-case-source.md) item 2, so it needs an entry that supersedes
  [ADR-8DSW](8DSW-vector-files-are-the-case-source.md) in full. The user first chose this key, then
  rejected it for this reason.
- The flag only in the `source` cases, with `model_input` as the default: a host must then know the
  default. The user chose the flag in every case.
- No boxes in the end-to-end cases: the case `nms-comes-before-the-clamp` then cannot show that the
  clamp gives the two kept rows the same box. It also breaks
  [ADR-8DSW](8DSW-vector-files-are-the-case-source.md) item 2.
