"""設定モデルとローダーの公開インターフェース。"""

from __future__ import annotations

from auto_emulator.config.loader import load_config
from auto_emulator.config.models import (
    ActionSpec,
    AutomationConfig,
    AutomationStep,
    CalibrationSettings,
    ConditionNode,
    ControlSettings,
    DetectorSpec,
    LoggingSettings,
    RegionDefinition,
    RuntimeSettings,
    StepControl,
    TransitionMapping,
    WatchConfig,
)

__all__ = [
    "ActionSpec",
    "AutomationConfig",
    "AutomationStep",
    "CalibrationSettings",
    "ConditionNode",
    "ControlSettings",
    "DetectorSpec",
    "LoggingSettings",
    "RegionDefinition",
    "RuntimeSettings",
    "StepControl",
    "TransitionMapping",
    "WatchConfig",
    "load_config",
]
