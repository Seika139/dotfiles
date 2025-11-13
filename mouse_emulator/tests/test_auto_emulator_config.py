from __future__ import annotations

from pathlib import Path

from auto_emulator.config import load_config


def test_example_profile_loads() -> None:
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "profiles" / "auto_emulator" / "example.yml"
    config = load_config(config_path)
    assert config.steps, "example.yml は少なくとも1つのステップを含む必要があります"
