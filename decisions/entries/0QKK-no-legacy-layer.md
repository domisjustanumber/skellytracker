# 0QKK — No legacy layer in the sidecar spec

**Status:** accepted, 2026-11-02 (user; PR: pending).

## Decision

This entry supersedes [ADR-0012](../../specs/model-sidecar/decisions/entries/0012-fit-resize-for-rtmo.md)
and [ADR-0016](0016-sidecar-catalogs.md) in full. Items 1 to 6 are new. Item 7 restates the rules
that stay by links ([ADR-Z05A](Z05A-essential-decision-log-rules.md)).

1. **No backward compatibility.** Each sidecar has one reading: the current spec text. The spec has
   no legacy reading, `## Legacy behaviour` heading, **(vNEXT)** mark or version-aware compatibility
   table. A host loads only the versions that it implements. The rules for older sidecars go: the
   one-key `$ref` form, the default `source`, the `max_detections` default 300, the load from the
   package root only and the acceptance of a sidecar with no `source` or hashes. The package
   sidecars stay outside the spec until they migrate
   ([ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) item 1). The content commit
   deletes the legacy rows and clauses of the changelog summary, an exception to "Do not reword the
   existing rows" of `change-sidecar-spec`. The other rows keep their numbers: decided entries cite
   them.
2. **`input.normalization` is required.** It has no default, no fallback in the resolution order
   and no warning.
3. **Deleted keys and unknown keys.** `preserve_aspect_ratio`, `requires_nms` and
   `may_include_non_person_classes` go. Of `V-post.det.decode-4`, only the sentences on the last
   two go. A key that the spec does not define is invalid. A doc test checks each example.
4. **No `since` or `changed_in`.** The front matter of a section has neither key.
5. **Rule numbers.** Until revision `1.0`, a change that deletes a rule of a section
   numbers the other rules of the section again from 1, in their order. The same commit repairs
   each citation of a changed rule ID. The body of a decided entry and the implementation plan keep
   the old ID as history. From revision `1.0` on, a rule ID is stable.
6. **The workflow side.** This entry and the entries that follow it (one batch field, the minimal
   contract, one selection pipeline, the spec-owned version) each get their own content commit. A
   content commit changes only the spec, the examples, the vectors, the decision logs, and the
   tools, tests and links that the checks need. One non-spec commit after the last of them changes
   the skills, the templates, the workflow and the `AGENTS.md` files for all of them. No
   content commit comes between them. The bundle-process entry is accepted in that commit
   ([ADR-FADS](FADS-hand-over-bundles-in-intakes.md) item 6).
7. **The rules that stay.**
   - ADR-0012: [Behaviour](../../specs/model-sidecar/pre/resize-fit.md#behaviour) of
     `pre.resize.fit` (the algorithm, its inverse, the required `pad_value`, the forbidden keys,
     the RTMO match, why not `letterbox`),
     [`input.resize`](../../specs/model-sidecar/common/input.md#inputresize) for the form of
     `pad_value`, and the RTMO values in
     [Authoring guidance](../../specs/model-sidecar/pre/resize-fit.md#authoring-guidance). The
     sentence on older sidecars goes with item 1, `preserve_aspect_ratio` with item 3. The pitfall
     on the code default `0` goes: the field is required.
   - ADR-0016: [`source`](../../specs/model-sidecar/common/identity.md#fields),
     [roots](../../specs/model-sidecar/format/file-layout.md#sidecar-roots),
     [Discovery](../../specs/model-sidecar/format/file-layout.md#discovery),
     [Reference hashes](../../specs/model-sidecar/format/composition.md#reference-hashes),
     [artifact hashes](../../specs/model-sidecar/common/sizes-and-artifacts.md#fields),
     [publish ban](../../specs/model-sidecar/format/versioning.md#authoring-guidance) and the
     Implementer guidance of [identity](../../specs/model-sidecar/common/identity.md#implementer-guidance),
     [file layout](../../specs/model-sidecar/format/file-layout.md#implementer-guidance),
     [composition](../../specs/model-sidecar/format/composition.md#implementer-guidance) and
     [versioning](../../specs/model-sidecar/format/versioning.md#implementer-guidance). Its legacy
     rules go with item 1. The CRLF checkout pitfall goes: `--check` reports CRLF. "What goes
     where" is done.

## Reason

- The user, in words (2026-10-30): "I agree with 1 and do not want to keep or maintain any
  backwards compatibility. Nothing has shipped yet, and all exporters will be rebuilt on the new
  spec process once it is finalised here."
- No release, `main` or `development` shipped a sidecar with `schema_version`, so the legacy layer
  protected no user. It cost 16 `## Legacy behaviour` headings and a **(vNEXT)** mark on each new
  rule.
- A default normalization changes the model input with no error when an author forgets the key.
- The deleted keys exist only to read older sidecars. `preserve_aspect_ratio: true` gives no
  information. Without the unknown-key rule, a deleted or misspelt key passes with no error.
- `since` and `changed_in` copy the changelog.
- A gap in the rule numbers reads as a missing rule. Before revision `1.0`, no release cites a rule
  ID.
- One workflow commit for the content commits keeps one kind of change in each commit
  ([ADR-AB79](AB79-one-pr-for-the-spec-build-work.md)).

## Consequences

- Until the workflow commit, the skills and the workflow name the old text. Exporter agents must
  wait until then.
- An exporter that writes `preserve_aspect_ratio: true` must stop at its next export.
- The spec-owned version entry adds this entry to the re-export request. The
  frozen package reads the legacy fields until it migrates.

## Alternatives rejected

- **Keep the legacy rows until the first release.** Each content change must then state its
  legacy reading.
- **A default `imagenet_bgr` with a warning.** A warning does not stop a wrong input.
- **A non-spec commit after each content commit.** Each workflow file then changes many times.
