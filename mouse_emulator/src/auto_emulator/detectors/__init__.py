"""検出器のレジストリとデフォルト実装。"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from auto_emulator.config import DetectorSpec, WatchConfig
from auto_emulator.detectors.base import BaseDetector, DetectionResult
from auto_emulator.exceptions import ConfigurationError
from auto_emulator.runtime.context import StepRuntimeContext

__all__ = [
    "BaseDetector",
    "DetectionResult",
    "NullDetector",
    "create_detector",
    "register_detector",
]

_DETECTOR_REGISTRY: dict[str, type[BaseDetector]] = {}
T_Detector = TypeVar("T_Detector", bound=type[BaseDetector])


def register_detector(name: str) -> Callable[[T_Detector], T_Detector]:
    canonical = name.strip().lower()

    def decorator(cls: T_Detector) -> T_Detector:
        _DETECTOR_REGISTRY[canonical] = cls
        return cls

    return decorator


def create_detector(spec: DetectorSpec) -> BaseDetector:
    detector_type = spec.type.strip().lower()
    impl = _DETECTOR_REGISTRY.get(detector_type)
    if impl is None:
        raise ConfigurationError(
            f"未登録の detector.type が指定されました: {spec.type}",
        )
    return impl(spec)


@register_detector("null")
class NullDetector(BaseDetector):
    """テスト用途の検出器。常に未検出を返す。"""

    def detect(self, watch: WatchConfig, ctx: StepRuntimeContext) -> DetectionResult:  # noqa: ARG002
        return DetectionResult(matched=False, score=None, data=None, region=None)


# 標準検出器をインポートしてレジストリへ登録
import auto_emulator.detectors.ocr  # noqa: F401,E402
import auto_emulator.detectors.template  # noqa: F401,E402
