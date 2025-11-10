# ruff: noqa: S101

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from auto_emulator.config import load_config
from auto_emulator.config.models import CalibrationPreset
from auto_emulator.exceptions import ConfigurationError

VALID_YAML = textwrap.dedent(
    """\
    version: "1.0"
    steps:
      - id: "step"
        watch:
          detector:
            type: "null"
        actions: []
    """,
)


def test_load_valid_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "workflow.yaml"
    config_path.write_text(VALID_YAML, encoding="utf-8")

    config = load_config(config_path)
    assert config.version == "1.0"
    assert config.steps[0].id == "step"
    assert config.metadata["__base_dir__"] == str(tmp_path)
    assert config.runtime.controls.pause_toggle == "ctrl+p"
    assert config.runtime.logging.file is None


def test_calibration_preset_loaded(tmp_path: Path) -> None:
    config_path = tmp_path / "workflow.yaml"
    config_path.write_text(
        """
        version: "1.0"
        runtime:
          calibration:
            enabled: false
            preset:
              left: 10
              top: 20
              right: 110
              bottom: 220
        steps:
          - id: "step"
            watch:
              detector:
                type: "null"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)
    preset = config.runtime.calibration.preset
    assert isinstance(preset, CalibrationPreset)
    region = preset.to_region()
    assert (region.left, region.top, region.right, region.bottom) == (10, 20, 110, 220)
    assert config.runtime.controls.pause_toggle == "ctrl+p"


def test_load_invalid_suffix(tmp_path: Path) -> None:
    config_path = tmp_path / "workflow.txt"
    config_path.write_text(VALID_YAML, encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_config(config_path)


def test_load_invalid_schema(tmp_path: Path) -> None:
    config_path = tmp_path / "workflow.yaml"
    config_path.write_text("version: ''", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_config(config_path)


def test_missing_file() -> None:
    with pytest.raises(ConfigurationError):
        load_config(Path("profiles/auto_emulator/missing.yaml"))
