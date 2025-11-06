from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from PIL import Image

from auto_emulator.config import (
    AutomationConfig,
    AutomationStep,
    RegionDefinition,
    WatchConfig,
)
from auto_emulator.exceptions import EngineRuntimeError
from auto_emulator.services import ScreenCaptureService
from mouse_core import PointerController, Region

if TYPE_CHECKING:
    from auto_emulator.detectors.base import DetectionResult


@dataclass(slots=True)
class AutomationContext:
    config: AutomationConfig
    pointer: PointerController
    capture_service: ScreenCaptureService
    calibration_region: Region | None = None
    shared_state: dict[str, Any] = field(default_factory=dict)
    _named_region_cache: dict[str, Region] = field(default_factory=dict, init=False)

    def require_region(self) -> Region:
        if self.calibration_region is None:
            raise EngineRuntimeError("キャリブレーションが未完了のまま参照されました")
        return self.calibration_region

    def reset_region_cache(self) -> None:
        self._named_region_cache.clear()

    def resolve_named_region(self, name: str) -> Region:
        if name in self._named_region_cache:
            return self._named_region_cache[name]
        base = self.require_region()
        definition = self._find_region_definition(name)
        region = base.subregion(
            left=definition.left,
            top=definition.top,
            right=definition.right,
            bottom=definition.bottom,
        )
        self._named_region_cache[name] = region
        return region

    def _find_region_definition(self, name: str) -> RegionDefinition:
        for definition in self.config.regions:
            if definition.name == name:
                return definition
        msg = f"定義されていない領域名です: {name}"
        raise EngineRuntimeError(msg)


@dataclass(slots=True)
class StepRuntimeContext:
    context: AutomationContext
    step: AutomationStep
    iteration: int = 0
    last_detection: DetectionResult | None = None

    @property
    def pointer(self) -> PointerController:
        return self.context.pointer

    @property
    def config(self) -> AutomationConfig:
        return self.context.config

    @property
    def region(self) -> Region:
        return self.context.require_region()

    def resolve_watch_region(self, watch: WatchConfig) -> Region:
        if watch.region is None:
            return self.region
        return self.context.resolve_named_region(watch.region)

    def capture(self, watch: WatchConfig) -> Image.Image:
        region = self.resolve_watch_region(watch)
        return self.context.capture_service.capture(region=region)
