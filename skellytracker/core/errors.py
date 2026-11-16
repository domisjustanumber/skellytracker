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
    """The EP pack is not installed, does not register, or lists no device. `hint` is the install command."""

    exit_code = EXIT_EP_UNAVAILABLE

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message if hint is None else f"{message} {hint}")
        self.message = message
        self.hint = hint

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
    """The GPU memory is exhausted at the build or the warm-up of a session. It is also a `MemoryError`."""

    exit_code = EXIT_VRAM_EXHAUSTED

    def __init__(self, message: str, report: object = None) -> None:
        super().__init__(message)
        self.message = message
        self.report = report

    def __reduce__(self):
        return (type(self), (self.message, self.report), self.__dict__)


def exit_code_of(error: BaseException) -> int:
    """The CLI exit code of `error`: its `exit_code`, else `EXIT_FAILURE`."""
    return getattr(error, "exit_code", EXIT_FAILURE)
