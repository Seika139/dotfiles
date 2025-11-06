from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from PIL import Image

from auto_emulator.config import DetectorSpec, WatchConfig
from auto_emulator.runtime.context import StepRuntimeContext
from mouse_core import Region


@dataclass(slots=True)
class DetectionResult:
    matched: bool
    score: float | None = None
    data: Mapping[str, Any] | None = None
    region: Region | None = None


class BaseDetector(ABC):
    def __init__(self, spec: DetectorSpec) -> None:
        self.spec = spec

    @abstractmethod
    def detect(self, watch: WatchConfig, ctx: StepRuntimeContext) -> DetectionResult:
        """観測対象を評価し DetectionResult を返却する。"""

    def capture(self, watch: WatchConfig, ctx: StepRuntimeContext) -> Image.Image:
        return ctx.capture(watch)
