"""The catalog of the `detectors` entry point: the models that this host can list.

    list_detectors()        # each sidecar of the sidecar roots, and the entries with no sidecar
    describe_detector(key)  # the sizes, the ports, the params and the point names of one entry

The sidecar roots are the package root `core/model_zoo/` and the user root. Each root has the
storage layout of the sidecar spec. Each folder name of the layout is lower case, also on a file
system that ignores the case. The catalog finds the sidecars of a root with the discovery rule of
the spec. It does not follow a symlink out of a root, so a Hugging Face snapshot folder is a root.

The key of a sidecar is `<model_id>@<source.name>`. A model with no sidecar has the key
`<detector_type>@skellytracker`. When a key has more than one `source.version`, the newest version
in PEP 440 order wins, and the other versions are superseded. `<key>==<version>` pins a version.

This module imports no detector module. A static table names the classes with no sidecar.
"""
from __future__ import annotations

import hashlib
import logging
import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Literal

import platformdirs
import yaml
from packaging.version import InvalidVersion, Version

from skellytracker.core.model_spec import artifacts
from skellytracker.core.model_spec.artifacts import HashCache, check_artifact_hash
from skellytracker.core.model_spec.errors import SidecarError
from skellytracker.core.model_spec.landmark_schemas import PACKAGE_SIDECAR_ROOT
from skellytracker.core.model_spec.loader import load_sidecar
from skellytracker.core.model_spec.model import SidecarModel
from skellytracker.core.model_spec.resolution import lexical_path, resolve_sidecar_composition
from skellytracker.core.model_spec.sections import applicable_sections, unimplemented_sections

logger = logging.getLogger(__name__)

USER_ROOT_VARIABLE = "SKELLYTRACKER_USER_ROOT"
RESERVED_SOURCE = "skellytracker"
"""The `source.name` of the package root. A sidecar with this name in another root is unavailable."""

Category = Literal["onnx", "mediapipe", "calibration"]


class DetectorNotFoundError(KeyError):
    """The catalog has no entry with this key, or no entry with the pinned version."""


class DetectorUnavailableError(RuntimeError):
    """The sidecar of the entry cannot load. The message names the section, the version or the rule."""


@dataclass(frozen=True)
class ArtifactEntry:
    """One ONNX file of a model: one size and one precision."""

    size: str
    precision: str
    filename: str
    sha256: str
    path: Path
    available: bool
    unavailable_reason: str | None = None


@dataclass(frozen=True)
class DetectorEntry:
    """One entry of the `detectors` list.

    An `onnx` entry is available when its sidecar loads, the package runs each spec section that it
    uses, and one or more of its ONNX files are present with the hash of the sidecar. `key`,
    `version` and `sidecar_sha256` are the three values that a run records in its output metadata.
    `role` and `sections` select the generic detector of the entry.
    """

    key: str
    category: Category
    display_name: str
    available: bool
    unavailable_reason: str | None = None
    version: str | None = None
    superseded: bool = False
    role: tuple[str, ...] = ()
    sections: tuple[str, ...] = ()
    sidecar_path: Path | None = None
    sidecar_root: Path | None = None
    sidecar_sha256: str | None = None
    artifacts: tuple[ArtifactEntry, ...] = ()

    def artifact(self, size: str, precision: str) -> ArtifactEntry:
        """Return the artifact of one size and one precision. An unknown size is an error, not a fallback."""
        for artifact in self.artifacts:
            if (artifact.size, artifact.precision) == (size, precision):
                return artifact
        found = [f"{artifact.size}/{artifact.precision}" for artifact in self.artifacts]
        raise ValueError(f"no artifact {size}/{precision} in {self.key!r}; it has {found}")


@dataclass(frozen=True)
class Port:
    name: str
    direction: Literal["input", "output"]
    port_type: str


@dataclass(frozen=True)
class DetectorDescription:
    """The details of one entry. An entry with no sidecar, or with a sidecar that does not load, has only `entry`.

    `sizes` maps each size to its precisions. The first size is the default. `ports` are the ports
    of an `onnx_model` node of this model. `params` holds the node params whose defaults come from
    the sidecar: `size`, and `object_decode` for an object detector.
    """

    entry: DetectorEntry
    sizes: dict[str, tuple[str, ...]] = field(default_factory=dict)
    ports: tuple[Port, ...] = ()
    params: dict[str, Any] = field(default_factory=dict)
    point_names: tuple[str, ...] = ()


# ---------------------------------------------------------------------------------------------
# The entries with no sidecar
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class StaticDetector:
    """A model with no sidecar. `module` and `class_name` name its class. The catalog does not import it."""

    detector_type: str
    category: Category
    display_name: str
    module: str
    class_name: str

    @property
    def key(self) -> str:
        return f"{self.detector_type}@{RESERVED_SOURCE}"


_MEDIAPIPE = "skellytracker.core.detectors.keypoint_detectors.mediapipe"
_CALIBRATION = "skellytracker.core.detectors.calibration_detectors"
STATIC_DETECTORS: tuple[StaticDetector, ...] = (
    StaticDetector("mediapipe_pose", "mediapipe", "MediaPipe Pose", f"{_MEDIAPIPE}.body.mediapipe_pose_detector", "MediapipePoseKeypointDetector"),
    StaticDetector("mediapipe_hand", "mediapipe", "MediaPipe Hands", f"{_MEDIAPIPE}.hands.mediapipe_hand_detector", "MediapipeHandKeypointDetector"),
    StaticDetector("mediapipe_face", "mediapipe", "MediaPipe Face", f"{_MEDIAPIPE}.face.mediapipe_face_detector", "MediapipeFaceKeypointDetector"),
    StaticDetector("charuco", "calibration", "Charuco board", f"{_CALIBRATION}.charuco.charuco_detector", "CharucoDetector"),
    StaticDetector("aruco", "calibration", "ArUco markers", f"{_CALIBRATION}.aruco.aruco_detector", "ArucoDetector"),
)


def _missing_extra(category: Category) -> str | None:
    """Return why the Python package of a category is not installed, else None.

    Each `find_spec` call has a literal name, so a frozen build finds the name.
    """
    if category == "mediapipe" and find_spec("mediapipe") is None:
        return "the extra `mediapipe` is not installed (`pip install skellytracker[mediapipe]`)"
    if category == "calibration" and find_spec("cv2") is None:
        return "the package `opencv-contrib-python` is not installed"
    if category == "onnx" and find_spec("onnxruntime") is None:
        return "the package `onnxruntime` is not installed"
    return None


def _static_entries() -> list[DetectorEntry]:
    entries = []
    for static in STATIC_DETECTORS:
        reason = _missing_extra(static.category)
        entries.append(DetectorEntry(static.key, static.category, static.display_name, reason is None, reason))
    return entries


# ---------------------------------------------------------------------------------------------
# Roots and discovery
# ---------------------------------------------------------------------------------------------


def resolve_user_root(user_root: Path | str | None = None) -> Path:
    """Return the user root: the argument, then `SKELLYTRACKER_USER_ROOT`, then the default.

    The default is `platformdirs.user_data_dir("skellytracker", appauthor=False)` + `/models`.
    """
    if user_root is not None:
        return lexical_path(user_root)
    if from_environment := os.environ.get(USER_ROOT_VARIABLE):
        return lexical_path(from_environment)
    return Path(platformdirs.user_data_dir("skellytracker", appauthor=False)) / "models"


def discover_sidecars(sidecar_root: Path) -> list[tuple[Path, dict[Any, Any], bytes]]:
    """Return the path, the top-level mapping and the bytes of each sidecar in a root.

    Implements: format.file_layout

    A `.yaml` file is a sidecar when its top level has `schema_version` and a `model_id` that is
    equal to the file name without `.yaml`. This function reads each file with a plain YAML parse,
    so the catalog also lists a sidecar that the loader refuses, with the reason.
    """
    found = []
    for path in sorted(sidecar_root.rglob("*.yaml")):
        try:
            data = path.read_bytes()
            top = yaml.safe_load(data)
        except (OSError, yaml.YAMLError):
            continue
        if isinstance(top, dict) and "schema_version" in top and top.get("model_id") == path.stem:
            found.append((path, top, data))
    return found


@dataclass
class _Sidecar:
    """One discovered sidecar file. `reason` tells why the sidecar itself is not usable."""

    path: Path
    root: Path
    key: str
    version: str
    display_name: str
    sha256: str
    model: SidecarModel | None = None
    sections: tuple[str, ...] = ()
    reason: str | None = None
    superseded: bool = False


def _text(value: Any, default: str) -> str:
    return value if isinstance(value, str) and value else default


def _read_sidecar(path: Path, top: dict[Any, Any], data: bytes, root: Path, user_root: Path, is_package_root: bool) -> _Sidecar:
    source = top.get("source") if isinstance(top.get("source"), dict) else {}
    source_name = _text(source.get("name"), "unknown")
    found = _Sidecar(
        path=path,
        root=root,
        key=f"{top['model_id']}@{source_name}",
        version=_text(source.get("version"), "unknown"),
        display_name=_text(top.get("display_name"), str(top["model_id"])),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    if source_name == RESERVED_SOURCE and not is_package_root:
        found.reason = f"the source name `{RESERVED_SOURCE}` is reserved for the package root; this sidecar is in {root}"
        return found
    try:
        found.model = load_sidecar(path, root, user_root)
    except SidecarError as exc:
        found.reason = str(exc)
        return found
    resolved = resolve_sidecar_composition(path, root)
    found.sections = applicable_sections(resolved)
    if missing := unimplemented_sections(resolved):
        found.reason = f"the sidecar uses spec sections that this release does not implement: {', '.join(missing)}"
    elif extra := _missing_extra("onnx"):
        found.reason = extra
    return found


def _version_order(found: _Sidecar) -> tuple[int, Version]:
    try:
        return 1, Version(found.version)
    except InvalidVersion:
        return 0, Version("0")


def scan_sidecar_roots(
    user_root: Path | str | None = None,
    *,
    package_root: Path = PACKAGE_SIDECAR_ROOT,
    other_roots: Sequence[Path] = (),
) -> list[_Sidecar]:
    """Return each sidecar of the roots, sorted by key, with the newest version of a key first.

    The root order is the package root, the user root, then `other_roots`. An item of `other_roots`
    is a local folder or the top folder of a Hugging Face snapshot.
    """
    user = resolve_user_root(user_root)
    by_version: dict[tuple[str, str], list[_Sidecar]] = {}
    for root in dict.fromkeys(lexical_path(root) for root in (package_root, user, *other_roots)):
        if not root.is_dir():
            continue
        for path, top, data in discover_sidecars(root):
            found = _read_sidecar(path, top, data, root, user, is_package_root=root == lexical_path(package_root))
            by_version.setdefault((found.key, found.version), []).append(found)

    by_key: dict[str, list[_Sidecar]] = {}
    for (key, version), group in by_version.items():
        first = group[0]
        if len({found.sha256 for found in group}) > 1:
            paths = " and ".join(str(found.path) for found in group)
            first.reason = f"two sidecars have the key {key} and the version {version}, with different bytes: {paths}"
        if first.reason is None and _version_order(first)[0] == 0:
            first.reason = f"source.version {version!r} is not a PEP 440 version"
        by_key.setdefault(key, []).append(first)

    result: list[_Sidecar] = []
    for key in sorted(by_key):
        versions = sorted(by_key[key], key=_version_order, reverse=True)
        for found in versions[1:]:
            found.superseded = True
        if len({found.root for group_key, group in by_version.items() if group_key[0] == key for found in group}) > 1:
            logger.info("the key %s is in more than one sidecar root; the catalog uses %s", key, versions[0].path)
        result.extend(versions)
    return result


# ---------------------------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------------------------


def _artifacts(found: _Sidecar, cache: HashCache) -> tuple[ArtifactEntry, ...]:
    """Return the capability of each artifact. A user can copy only some sizes or precisions.

    The file of an artifact is beside its sidecar. A `url` artifact with no file there can have a
    downloaded file in the download folder (`artifacts.download_path`).
    """
    entries = []
    for size, size_spec in found.model.sizes.items():
        for precision, artifact in size_spec.onnx.precision_artifacts.items():
            file, root = found.path.parent / artifact.filename, found.root
            if not file.is_file() and artifact.url is not None:
                downloaded = artifacts.download_path(found.key, found.version, artifact.filename)
                if downloaded.is_file():
                    file, root = downloaded, artifacts.download_root()
            if found.reason is not None:
                reason = found.reason
            elif not file.is_file() and artifact.url is not None:
                reason = f"the ONNX file {artifact.filename} is not downloaded; the sidecar gives its `url`"
            elif not file.is_file():
                reason = f"the ONNX file {artifact.filename} is not present, and the sidecar gives no `url`"
            else:
                failure = check_artifact_hash(file, root, artifact.sha256, cache)
                reason = None if failure is None else str(failure)
            entries.append(ArtifactEntry(size, precision, artifact.filename, artifact.sha256, file, reason is None, reason))
    return tuple(entries)


def _entry(found: _Sidecar, cache: HashCache) -> DetectorEntry:
    artifacts = () if found.model is None else _artifacts(found, cache)
    reason = found.reason
    if reason is None and not any(artifact.available for artifact in artifacts):
        first = artifacts[0]
        reason = f"no ONNX file of this model is available; {first.size}/{first.precision}: {first.unavailable_reason}"
    return DetectorEntry(
        key=found.key,
        category="onnx",
        display_name=found.display_name,
        available=reason is None,
        unavailable_reason=reason,
        version=found.version,
        superseded=found.superseded,
        role=() if found.model is None else tuple(found.model.role),
        sections=found.sections,
        sidecar_path=found.path,
        sidecar_root=found.root,
        sidecar_sha256=found.sha256,
        artifacts=artifacts,
    )


def list_detectors(user_root: Path | str | None = None, *, full_hash: bool = False) -> list[DetectorEntry]:
    """Return each entry of the catalog: the sidecars of the roots, then the entries with no sidecar.

    `user_root` is the user root. With None, the root is `SKELLYTRACKER_USER_ROOT`, else the
    default of `resolve_user_root`. `full_hash=True` hashes each ONNX file again and does not use
    the hash check cache. A superseded version of a key is in the list, with `superseded=True`.
    """
    cache = HashCache(full_hash=full_hash)
    entries = [_entry(found, cache) for found in scan_sidecar_roots(user_root)]
    cache.save()
    return entries + _static_entries()


def split_key(key: str) -> tuple[str, str | None]:
    """Split `<key>==<version>` into the key and the pinned version, or None with no pin."""
    name, separator, version = key.partition("==")
    return name, (version if separator else None)


def _same_version(left: str, right: str) -> bool:
    try:
        return Version(left) == Version(right)
    except InvalidVersion:
        return left == right


def _select(key: str, candidates: Sequence[Any]) -> Any:
    """Return the item of `candidates` (objects with `key`, `version` and `superseded`) that a key names."""
    name, pin = split_key(key)
    with_key = [item for item in candidates if item.key == name]
    if not with_key:
        raise DetectorNotFoundError(f"the catalog has no entry {name!r}; it has {sorted({item.key for item in candidates})}")
    if pin is None:
        return next(item for item in with_key if not item.superseded)
    for item in with_key:
        if item.version is not None and _same_version(item.version, pin):
            return item
    raise DetectorNotFoundError(f"the catalog has no version {pin!r} of {name!r}; it has {[item.version for item in with_key]}")


def get_detector(key: str, user_root: Path | str | None = None, *, full_hash: bool = False) -> DetectorEntry:
    """Return the entry of `<key>` (the newest version) or of the pin `<key>==<version>`.

    Raise `DetectorNotFoundError` when the catalog does not have it.
    """
    return _select(key, list_detectors(user_root, full_hash=full_hash))


def load_detector_sidecar(key: str, user_root: Path | str | None = None) -> SidecarModel:
    """Return the spec model of an `onnx` entry. This function does not read an ONNX file.

    Raise `DetectorUnavailableError` when the sidecar is not usable. The message names the section,
    the version or the rule. Raise `DetectorNotFoundError` when no sidecar has the key.
    """
    found = _select(key, scan_sidecar_roots(user_root))
    if found.reason is not None:
        raise DetectorUnavailableError(f"{found.key} is unavailable: {found.reason}")
    return found.model


# ---------------------------------------------------------------------------------------------
# describe_detector
# ---------------------------------------------------------------------------------------------

_IMAGE = Port("image", "input", "image")
_ROIS_IN = Port("rois", "input", "roi")
_DETECTIONS = Port("detections", "output", "detections")
_ROIS_OUT = Port("rois", "output", "roi")
_KEYPOINTS = Port("keypoints", "output", "keypoints")


def model_ports(model: SidecarModel) -> tuple[Port, ...]:
    """Return the ports that an `onnx_model` node of this model uses, from its `role`."""
    if "object_detector" in model.role:
        keypoints = (_KEYPOINTS,) if "keypoint_detector" in model.role else ()
        return (_IMAGE, _DETECTIONS, _ROIS_OUT, *keypoints)
    if model.keypoint.estimator_type == "bottom_up":
        return (_IMAGE, _KEYPOINTS)
    return (_IMAGE, _ROIS_IN, _KEYPOINTS)


def describe_detector(key: str, user_root: Path | str | None = None, *, full_hash: bool = False) -> DetectorDescription:
    """Return the sizes, the precisions, the ports, the params and the point names of one entry.

    `key` is `<key>` or the pin `<key>==<version>`. `entry.sidecar_sha256` is the SHA-256 of the
    sidecar file. Raise `DetectorNotFoundError` when the catalog does not have the key.
    """
    cache = HashCache(full_hash=full_hash)
    sidecars = scan_sidecar_roots(user_root)
    found = _select(key, [*sidecars, *_static_entries()])
    if isinstance(found, DetectorEntry):
        return DetectorDescription(found)
    entry = _entry(found, cache)
    cache.save()
    model = found.model
    if model is None:
        return DetectorDescription(entry)
    params: dict[str, Any] = {"size": model.default_size}
    if model.object is not None:
        params["object_decode"] = model.object.decode.model_dump(exclude_none=True)
    return DetectorDescription(
        entry=entry,
        sizes={size: tuple(spec.onnx.precision_artifacts) for size, spec in model.sizes.items()},
        ports=model_ports(model),
        params=params,
        point_names=() if model.keypoint is None else tuple(model.keypoint.point_names),
    )


__all__ = [
    "ArtifactEntry",
    "DetectorDescription",
    "DetectorEntry",
    "DetectorNotFoundError",
    "DetectorUnavailableError",
    "Port",
    "STATIC_DETECTORS",
    "StaticDetector",
    "describe_detector",
    "get_detector",
    "list_detectors",
    "load_detector_sidecar",
    "resolve_user_root",
    "scan_sidecar_roots",
]
