"""Tests for skellytracker-gpus CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from skellytracker.scripts import gpus_cli


def test_cli_prints_gpu_and_ep_guidance(capsys) -> None:
  with patch("skellytracker.scripts.gpus_cli.list_installed_gpus", return_value=[]):
    with patch(
      "skellytracker.scripts.gpus_cli.list_execution_providers",
      return_value=MagicMock(
        optimal_provider_id="cpu",
        recommended_provider_id="cpu",
        install_recommended_provider_id=None,
      ),
    ):
      assert gpus_cli.main([]) == 0
  out = capsys.readouterr().out
  assert "Optimal EP:" in out
  assert "Installed best EP:" in out


def test_install_dry_run_does_not_subprocess(tmp_path: Path, monkeypatch) -> None:
  pyproject = tmp_path / "pyproject.toml"
  pyproject.write_text('[project]\nname = "skellytracker"\n', encoding="utf-8")
  monkeypatch.chdir(tmp_path)

  with patch("skellytracker.scripts.gpus_cli.list_installed_gpus", return_value=[]):
    with patch(
      "skellytracker.scripts.gpus_cli.list_execution_providers",
      return_value=MagicMock(
        optimal_provider_id="cpu",
        recommended_provider_id="cpu",
        install_recommended_provider_id=None,
      ),
    ):
      with patch("shutil.which", return_value="/usr/bin/uv"):
        with patch("subprocess.run") as run_mock:
          assert gpus_cli.main(["--install", "--dry-run"]) == 0
          run_mock.assert_not_called()


def test_missing_pyproject_returns_error(capsys) -> None:
  with patch("skellytracker.scripts.gpus_cli.list_installed_gpus", return_value=[]):
    with patch(
      "skellytracker.scripts.gpus_cli.list_execution_providers",
      return_value=MagicMock(
        optimal_provider_id="cpu",
        recommended_provider_id="cpu",
        install_recommended_provider_id=None,
      ),
    ):
      with patch("skellytracker.scripts.gpus_cli.find_skellytracker_project_root", return_value=None):
        assert gpus_cli.main(["--install"]) == 1
  assert "rtmpose-nvidia" in capsys.readouterr().err
