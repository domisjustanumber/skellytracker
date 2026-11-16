"""From a catalog entry to a running generic detector: the ONNX file, the session and the dispatch."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from skellytracker.core.detectors.catalog import (
    DetectorEntry,
    DetectorUnavailableError,
    get_detector,
    load_detector_sidecar,
)
from skellytracker.core.detectors.generic.batch_conversion import model_batch_convert
from skellytracker.core.detectors.generic.download import download_artifact
from skellytracker.core.detectors.generic.keypoint_detector import GenericKeypointDetector
from skellytracker.core.detectors.generic.object_detector import GenericObjectDetector
from skellytracker.core.eps.records import ModelRef, SessionReport
from skellytracker.core.eps.session import build_session
from skellytracker.core.model_spec import artifacts
from skellytracker.core.model_spec.model import ObjectDecodeSpec, SidecarModel


def ensure_artifact(entry: DetectorEntry, sidecar: SidecarModel, size: str, precision: str) -> Path:
    """Return the ONNX file of one size and one precision. Download it when it is a `url` artifact with no file.

    Implements: common.sizes_and_artifacts

    The catalog checked the hash of a present file. A file that is not present and has no `url`,
    and a file beside the sidecar with a wrong hash, raise `DetectorUnavailableError`.
    """
    found = entry.artifact(size, precision)
    if found.available:
        return found.path
    spec = sidecar.artifact(size, precision)
    downloaded = artifacts.download_path(entry.key, str(entry.version), spec.filename)
    if spec.url is None or (found.path.is_file() and found.path != downloaded):
        raise DetectorUnavailableError(f"{entry.key} {size}/{precision} is unavailable: {found.unavailable_reason}")
    downloaded.parent.mkdir(parents=True, exist_ok=True)
    return download_artifact(spec, downloaded)


def open_session(
    entry: DetectorEntry,
    sidecar: SidecarModel,
    size: str,
    precision: str,
    *,
    execution_provider: str,
    batch: int | None = None,
    ep_options: Mapping[str, str] | None = None,
    device_key: str | None = None,
) -> tuple[Any, SessionReport]:
    """Build the session of one artifact on `execution_provider`. Return it with its `SessionReport`.

    Implements: common.batch_conversion

    `batch` is the batch `T` of the session. With None, or with `T` equal to `batching.batch`, the
    session runs the artifact of the sidecar. For any other `T`, a sidecar with
    `batching.batch_conversion` gets a generated artifact from `model_batch_convert`, in memory,
    and a sidecar with no conversion profile raises `ValueError`. A `dynamic` artifact runs each
    batch, so `batch` does not change its session. The errors of `eps.build_session` apply.
    """
    path = ensure_artifact(entry, sidecar, size, precision)
    native = sidecar.batching.batch
    model: Path | bytes = path
    if batch is not None and native != "dynamic" and batch != native:
        if sidecar.batching.batch_conversion is None:
            raise ValueError(f"{entry.key} has only the batch {native}: its sidecar has no batching.batch_conversion")
        model = model_batch_convert(
            path, source_batch=native, target_batch=batch, profile_id=sidecar.batching.batch_conversion.profile_id
        )
    reference = ModelRef(
        family=sidecar.model_id,
        artifact_sha256=sidecar.artifact(size, precision).sha256,
        precisions=(precision,),
        batch=batch if batch is not None else (None if native == "dynamic" else native),
    )
    return build_session(
        model, execution_provider=execution_provider, ep_options=ep_options, device_key=device_key, model_ref=reference
    )


def create_detector(
    key: str,
    *,
    execution_provider: str,
    size: str | None = None,
    precision: str = "fp32",
    batch: int | None = None,
    ep_options: Mapping[str, str] | None = None,
    device_key: str | None = None,
    object_decode: ObjectDecodeSpec | None = None,
    user_root: Path | str | None = None,
) -> GenericObjectDetector | GenericKeypointDetector:
    """Return the generic detector of the catalog entry `<key>` or `<key>==<version>`, with its session.

    Implements: format.versioning

    The `role` of the entry selects the detector. The capability check of the catalog refuses a
    sidecar that uses a spec section that the package does not run: `DetectorUnavailableError`
    names the sections. With no `size`, the size is the first size of the sidecar. `batch`,
    `ep_options` and `device_key` are the arguments of `open_session`. `object_decode` replaces
    `object.decode` of an object detector.
    """
    sidecar = load_detector_sidecar(key, user_root)
    entry = get_detector(key, user_root)
    size = sidecar.default_size if size is None else size
    if entry.role == ("object_detector",):
        make: Any = lambda session: GenericObjectDetector(sidecar, size, precision, session, object_decode)  # noqa: E731
    elif entry.role == ("keypoint_detector",):
        make = lambda session: GenericKeypointDetector(sidecar, size, precision, session)  # noqa: E731
    else:
        raise DetectorUnavailableError(f"{entry.key} is unavailable: this release has no generic detector for the role {list(entry.role)}")
    make(None)  # the checks of the detector, before the download and the session
    session, _ = open_session(
        entry, sidecar, size, precision,
        execution_provider=execution_provider, batch=batch, ep_options=ep_options, device_key=device_key,
    )
    return make(session)
