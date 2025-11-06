# ruff: noqa: S101

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from auto_emulator.config import load_config
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
