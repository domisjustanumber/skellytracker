"""The package copy of the pipeline spec agrees with the spec (ADR-3SF2 item 3; ADR-V7GZ item 9).

- The JSON Schema of `PipelineConfig` of the package module `skellytracker/core/pipelines/config.py`
  is the committed `specs/pipeline/pipeline.schema.json`.
- The schema file of the package is a byte copy of that file.
- `IMPLEMENTED_VERSIONS` of the pipeline loader holds the version headings and the pre-release
  lines of `specs/pipeline/changelog.md` (`V-pipeline.file-1`).
"""

from __future__ import annotations

import re
from pathlib import Path

import make_pipeline_schema as mps

from skellytracker.core.pipelines import config, loading

PACKAGE_SCHEMA = Path(config.__file__).with_name("pipeline.schema.json")
SPEC_SCHEMA = mps.PIPELINE_DIR / "pipeline.schema.json"


def test_the_schema_of_the_package_model_is_the_committed_schema() -> None:
    assert mps.schema_text(config) == SPEC_SCHEMA.read_text(encoding="utf-8")


def test_the_schema_file_of_the_package_is_a_copy_of_the_committed_schema() -> None:
    assert PACKAGE_SCHEMA.read_bytes() == SPEC_SCHEMA.read_bytes(), "copy specs/pipeline/pipeline.schema.json to the package"


def test_the_implemented_versions_are_the_versions_of_the_changelog() -> None:
    revisions = (mps.PIPELINE_DIR / "changelog.md").read_text(encoding="utf-8").split("\n## Revisions\n")[1]
    versions = re.findall(r"^### (\d+\.\d+\.\d+)$", revisions, re.M) + re.findall(r"^- Pre-release (\S+):", revisions, re.M)
    assert versions and sorted(loading.IMPLEMENTED_VERSIONS) == sorted(versions)
