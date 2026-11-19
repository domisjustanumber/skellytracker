"""The errors of `core.eps` and of the pipeline runtime, and the exit-code table of the CLIs.

The old `core/sessions/session_errors.py` is a different module. The old run code uses it.
"""

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
