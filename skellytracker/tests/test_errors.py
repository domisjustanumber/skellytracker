import pickle

import pytest

from skellytracker.core import errors


def test_classes_and_exit_codes():
    assert issubclass(errors.EpRequestError, ValueError)
    assert issubclass(errors.VRAMExhaustionError, MemoryError)
    assert errors.exit_code_of(errors.EpRequestError("x")) == 2
    assert errors.exit_code_of(errors.EpUnavailableError("x")) == 3
    assert errors.exit_code_of(errors.SessionCreationError("x")) == 4
    assert errors.exit_code_of(errors.VRAMExhaustionError("x")) == 5
    assert errors.exit_code_of(RuntimeError("x")) == 1
    assert errors.EXIT_CANCELLED == 6


@pytest.mark.parametrize(
    "error",
    [
        errors.EpRequestError("bad key"),
        errors.EpUnavailableError("no pack.", "Run `skellytracker-eps install cuda`."),
        errors.SessionCreationError("no node", ("report",)),
        errors.VRAMExhaustionError("out of memory", ("report",)),
    ],
)
def test_each_error_pickles(error):
    error.add_note("a note")
    copy = pickle.loads(pickle.dumps(error))  # noqa: S301
    assert type(copy) is type(error) and str(copy) == str(error)
    assert copy.__notes__ == ["a note"]
    assert getattr(copy, "report", None) == getattr(error, "report", None)
    assert getattr(copy, "hint", None) == getattr(error, "hint", None)
