"""The `cuda` bridge of the old `OnnxSession` to `eps.build_session()` (ADR-92BE).

Stage 2.4 of the implementation plan deletes this bridge and these tests with the old run code.
"""

from unittest.mock import MagicMock, patch

import onnxruntime as ort
import pytest
from pydantic import ValidationError

from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.sessions.model_registry import ModelSource
from skellytracker.core.sessions.onnx_session import OnnxModelSpec, OnnxSession, OnnxSessionConfig

MODULE = "skellytracker.core.sessions.onnx_session"


def _config(tmp_path, execution_provider, batch_size=2):
    model = tmp_path / "model.onnx"
    model.write_bytes(b"not-a-real-onnx-model")
    spec = OnnxModelSpec(name="m", source=ModelSource(local_path=str(model)), input_size=(64, 48))
    return OnnxSessionConfig(batch_size=batch_size, models=[spec], execution_provider=execution_provider), model


def test_cuda_builds_each_model_with_eps_build_session(tmp_path):
    config, model = _config(tmp_path, "cuda")
    fake = MagicMock(spec=ort.InferenceSession)
    with (
        patch(f"{MODULE}.resolve_model_path", return_value=model),
        patch("skellytracker.core.eps.build_session", return_value=(fake, object())) as build,
        patch(f"{MODULE}.require_provider") as require,
        patch(f"{MODULE}.build_tuned_ort_session") as old_build,
    ):
        session = OnnxSession.create(config)

    build.assert_called_once_with(model, execution_provider="cuda")
    require.assert_not_called()
    old_build.assert_not_called()
    assert session.execution_provider == "cuda"
    assert session.get_session("m") is fake
    # The old warm-up runs at the batch size of the config, after the batch-1 warm-up of build_session.
    (_, feeds), _ = fake.run.call_args
    assert next(iter(feeds.values())).shape == (2, 3, 64, 48)


def test_an_ep_error_reaches_the_caller_unchanged(tmp_path):
    config, model = _config(tmp_path, "cuda")
    error = EpUnavailableError("The EP 'cuda' is not available: the pack cuda-cu13 is not installed.")
    with (
        patch(f"{MODULE}.resolve_model_path", return_value=model),
        patch("skellytracker.core.eps.build_session", side_effect=error),
        patch(f"{MODULE}.build_tuned_ort_session") as old_build,
        pytest.raises(EpUnavailableError) as raised,
    ):
        OnnxSession.create(config)
    assert raised.value is error
    old_build.assert_not_called()


@pytest.mark.parametrize("key", ["trt-rtx", "tensorrt", "CUDA", "gpu"])
def test_other_keys_are_refused(tmp_path, key):
    with pytest.raises(ValidationError):
        _config(tmp_path, key)


@pytest.mark.parametrize("key", ["cpu", "coreml"])
def test_cpu_and_coreml_take_the_old_path(tmp_path, key):
    config, model = _config(tmp_path, key, batch_size=1)
    fake = MagicMock(spec=ort.InferenceSession)
    with (
        patch(f"{MODULE}.resolve_model_path", return_value=model),
        patch("skellytracker.core.eps.build_session") as build,
        patch(f"{MODULE}.require_provider") as require,
        patch(f"{MODULE}.build_tuned_ort_session", return_value=fake) as old_build,
    ):
        OnnxSession.create(config)

    build.assert_not_called()
    require.assert_called_once_with(key)
    assert old_build.call_args.kwargs["provider"] == key
