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


def test_the_errors_of_the_pipeline_runtime():
    missing = errors.MissingDependencyError("mediapipe", ["holistic"])
    assert (missing.extra, missing.node_ids, missing.files) == ("mediapipe", ("holistic",), ())
    assert "V-pipeline.running-3" in str(missing) and "holistic" in str(missing) and "`mediapipe`" in str(missing)
    file = errors.MissingDependencyError(None, ("person", "body"), ("a.onnx",), "the file is absent")
    assert "person, body" in str(file) and "a.onnx" in str(file) and "the file is absent" in str(file)
    refused = errors.CallRefusedError("V-pipeline.running-6: no timestamp_ms", "V-pipeline.running-6")
    assert isinstance(refused, ValueError) and refused.rule == "V-pipeline.running-6" and errors.exit_code_of(refused) == 2
    assert issubclass(errors.SetParamsRefusedError, ValueError) and errors.exit_code_of(errors.SetParamsRefusedError("x")) == 2
    assert issubclass(errors.RunClosedError, RuntimeError) and errors.exit_code_of(errors.RunClosedError("x")) == 1
    assert errors.exit_code_of(missing) == 1


@pytest.mark.parametrize(
    "error",
    [
        errors.MissingDependencyError("mediapipe", ["holistic"]),
        errors.MissingDependencyError(None, ("person",), ("a.onnx",), "the file is absent"),
        errors.CallRefusedError("V-pipeline.running-7: mixed", "V-pipeline.running-7"),
        errors.SetParamsRefusedError("V-pipeline.running-10: no"),
        errors.RunClosedError("the pipeline run is closed"),
    ],
)
def test_each_error_of_the_pipeline_runtime_pickles(error):
    error.add_note("a note")
    copy = pickle.loads(pickle.dumps(error))  # noqa: S301
    assert type(copy) is type(error) and str(copy) == str(error) and copy.__notes__ == ["a note"]
    for name in ("extra", "node_ids", "files", "rule"):
        assert getattr(copy, name, None) == getattr(error, name, None)
