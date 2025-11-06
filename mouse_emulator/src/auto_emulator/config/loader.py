from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from auto_emulator.config.models import AutomationConfig
from auto_emulator.exceptions import ConfigurationError

SUPPORTED_SUFFIXES = {".yaml", ".yml", ".json"}


def _read_yaml(path: Path) -> object:
    with path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def load_config(path: Path) -> AutomationConfig:
    if not path.exists():
        msg = f"設定ファイルが見つかりません: {path}"
        raise ConfigurationError(msg)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        msg = f"未対応のファイル形式です: {suffix}"
        raise ConfigurationError(msg)
    try:
        raw = _read_yaml(path) if suffix in {".yaml", ".yml"} else _read_json(path)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        msg = f"設定ファイルの解析に失敗しました: {path}"
        raise ConfigurationError(msg) from exc
    try:
        config = AutomationConfig.model_validate(raw)
    except ValidationError as exc:
        msg = f"設定のバリデーションに失敗しました: {path}"
        raise ConfigurationError(msg) from exc
    config.metadata.setdefault("__base_dir__", str(path.parent.resolve()))
    return config
