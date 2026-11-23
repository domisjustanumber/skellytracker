"""The errors of `core.eps` and of the pipeline runtime, and the exit-code table of the CLIs.

The old `core/sessions/session_errors.py` is a different module. The old run code uses it.
"""

import re
import sys

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_EP_UNAVAILABLE = 3
EXIT_SESSION_NOT_CREATED = 4
EXIT_VRAM_EXHAUSTED = 5
EXIT_CANCELLED = 6


class EpRequestError(ValueError):
    """A reserved EP key, an unknown EP key, or an EP option that the EP catalog refuses."""

    exit_code = EXIT_USAGE


class EpUnavailableError(RuntimeError):
    """The EP pack is not installed, does not register, or lists no device. `hint` is the install command.

    A refusal of the check rule (`core/eps/gate.py`) also gives `execution_provider`, `device_key` and
    `reason_code`: the EP key, the device key of the GPU, and `quick-check-needed`, `quick-check-failed` or
    `unclean-exits`. `device_key` is None for `coreml`. Each other refusal leaves the three as None.
    """

    exit_code = EXIT_EP_UNAVAILABLE

    def __init__(self, message: str, hint: str | None = None, *, execution_provider: str | None = None,
                 device_key: str | None = None, reason_code: str | None = None) -> None:
        super().__init__(message if hint is None else f"{message} {hint}")
        self.message = message
        self.hint = hint
        self.execution_provider = execution_provider
        self.device_key = device_key
        self.reason_code = reason_code

    def __reduce__(self):
        return (type(self), (self.message, self.hint), self.__dict__)


class SessionCreationError(RuntimeError):
    """The EP does not start, has no node, or is not the first provider. `report` is the failed `SessionReport`."""

    exit_code = EXIT_SESSION_NOT_CREATED

    def __init__(self, message: str, report: object = None) -> None:
        super().__init__(message)
        self.message = message
        self.report = report

    def __reduce__(self):
        return (type(self), (self.message, self.report), self.__dict__)


class VRAMExhaustionError(RuntimeError, MemoryError):
    """The GPU memory is exhausted at the build or the warm-up of a session, or during a call. It is also a `MemoryError`.

    `report` is the `SessionReport` of a build, or None for a call. A pipeline run that raises it
    during a call is closed: each later call raises `RunClosedError`.
    """

    exit_code = EXIT_VRAM_EXHAUSTED

    def __init__(self, message: str, report: object = None) -> None:
        super().__init__(message)
        self.message = message
        self.report = report

    def __reduce__(self):
        return (type(self), (self.message, self.report), self.__dict__)


class MissingDependencyError(RuntimeError):
    """A node that runs needs an optional extra that is not installed, or an ONNX file that is absent (`V-pipeline.running-3`).

    `extra` is the name of the extra, or None for a missing file. `node_ids` are the nodes that
    need it. `files` are the names of the missing ONNX files.
    """

    def __init__(self, extra: str | None, node_ids: tuple[str, ...] | list[str], files: tuple[str, ...] | list[str] = (), reason: str | None = None) -> None:
        self.extra, self.node_ids, self.files, self.reason = extra, tuple(node_ids), tuple(files), reason
        nodes = ", ".join(self.node_ids)
        if extra is not None:
            message = f"V-pipeline.running-3: the nodes {nodes} need the extra `{extra}`, which is not installed (`pip install skellytracker[{extra}]`)."
        else:
            message = f"V-pipeline.running-3: the nodes {nodes} need the ONNX files {', '.join(self.files)}: {reason}."
        super().__init__(message)

    def __reduce__(self):
        return (type(self), (self.extra, self.node_ids, self.files, self.reason), self.__dict__)


class CallRefusedError(ValueError):
    """A `process` or `process_batch` call that the run refuses. The call changes no state. `rule` is the rule ID."""

    exit_code = EXIT_USAGE

    def __init__(self, message: str, rule: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.rule = rule

    def __reduce__(self):
        return (type(self), (self.message, self.rule), self.__dict__)


class SetParamsRefusedError(ValueError):
    """A `set_params` call that breaks `V-pipeline.running-10`. The call changes no param."""

    exit_code = EXIT_USAGE


class RunClosedError(RuntimeError):
    """A call on a run after its `close()`."""


def exit_code_of(error: BaseException) -> int:
    """The CLI exit code of `error`: its `exit_code`, else `EXIT_FAILURE`."""
    return getattr(error, "exit_code", EXIT_FAILURE)


# An HRESULT of a failure in an error text: `0x` and 8 hex digits, or 8 upper-case hex digits that start with 8 to F, as
# DirectML writes it (for example `887A0005`). A 64-bit address has 16 digits, so it does not match.
_HRESULT = re.compile(r"(?<![0-9A-Za-z])(?:0[xX]([0-9A-Fa-f]{8})|([89A-F][0-9A-F]{7}))(?![0-9A-Za-z])")


def error_code(error: BaseException) -> str:
    """The class name of `error` with no module path, as a reason code: `-` for each character that a reason code cannot
    hold, no `_` or `-` at the start, at most 80 characters, for example `RuntimeError`."""
    return re.sub(r"[^A-Za-z0-9_-]", "-", type(error).__name__).lstrip("_-")[:80] or "Exception"


def error_numbers(error: BaseException) -> dict:
    """The facts of a caught exception that a certify report can hold: never its message text, a path or an address.

    `error` is the class name of the exception with no module path, in the form of a reason code (rule 3 of
    section 5.8 of the format of `skellycertify`): `error_code()`. The error number is an integer, when the
    exception has one: `hresult` on Windows (the attribute `hresult`, `winerror` of an `OSError` as
    `HRESULT_FROM_WIN32`, or the first HRESULT of a failure in the text, as the unsigned 32-bit value, for example
    2289696773 for `0x887A0005`), `errno` of an `OSError` on Linux and macOS, and `code`, the return code of the
    library (an integer attribute `returncode` or `code`). With no number, only `error`.
    """
    found: dict = {"error": error_code(error)}
    if sys.platform == "win32":
        hresult = getattr(error, "hresult", None)
        winerror = getattr(error, "winerror", None) if isinstance(error, OSError) else None
        if isinstance(hresult, int) and not isinstance(hresult, bool):
            found["hresult"] = hresult & 0xFFFFFFFF
        elif isinstance(winerror, int) and winerror:
            found["hresult"] = winerror & 0xFFFFFFFF if winerror < 0 else 0x80070000 | (winerror & 0xFFFF)
        elif match := _HRESULT.search(str(error)):
            value = int(match.group(1) or match.group(2), 16)
            if value & 0x80000000:  # a failure; a success code is no error number
                found["hresult"] = value
    elif isinstance(error, OSError) and isinstance(error.errno, int):
        found["errno"] = error.errno
    code = next((value for value in (getattr(error, name, None) for name in ("returncode", "code"))
                 if isinstance(value, int) and not isinstance(value, bool)), None)
    if code is not None:
        found["code"] = code
    return found
