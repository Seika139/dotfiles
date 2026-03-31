"""障害物回避ゲーム用エンジン。

3レーン構成の画面で上から降ってくる障害物を検出し、
安全なレーンをタップして回避する。
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from auto_emulator.config.models import (
    CalibrationSettings,
    ControlSettings,
)
from auto_emulator.runtime.termination import TerminationMonitor
from auto_emulator.services.capture import MSSScreenCaptureService, ScreenCaptureService
from mouse_core import PointerController, Region

# ---------------------------------------------------------------------------
# Configuration models
# ---------------------------------------------------------------------------


class ObstacleColor(BaseModel):
    """障害物の色定義。RGB + 許容範囲。"""

    model_config = ConfigDict(extra="forbid")

    r: int = Field(ge=0, le=255)
    g: int = Field(ge=0, le=255)
    b: int = Field(ge=0, le=255)
    tolerance: int = Field(
        default=30, ge=0, le=255, description="各チャンネルの許容誤差",
    )


class DetectionZone(BaseModel):
    """障害物をスキャンする縦方向の範囲 (相対座標 0.0-1.0)。"""

    model_config = ConfigDict(extra="forbid")

    top: float = Field(ge=0.0, le=1.0)
    bottom: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_bounds(self) -> DetectionZone:
        if self.bottom <= self.top:
            msg = "detection_zone.bottom は top より大きな値でなければなりません"
            raise ValueError(msg)
        return self


class TapPosition(BaseModel):
    """タップ先の相対座標。"""

    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


class LaneConfig(BaseModel):
    """1レーンの定義: スキャン範囲 + タップ位置。"""

    model_config = ConfigDict(extra="forbid")

    name: str
    x_min: float = Field(ge=0.0, le=1.0, description="スキャン範囲の左端 (相対)")
    x_max: float = Field(ge=0.0, le=1.0, description="スキャン範囲の右端 (相対)")
    tap: TapPosition

    @model_validator(mode="after")
    def _validate_x_range(self) -> LaneConfig:
        if self.x_max <= self.x_min:
            msg = f"lane '{self.name}': x_max は x_min より大きな値でなければなりません"
            raise ValueError(msg)
        return self


class DodgeRuntimeSettings(BaseModel):
    """dodge エンジンのランタイム設定。"""

    model_config = ConfigDict(extra="forbid")

    scan_interval: float = Field(
        default=0.03, gt=0.0, description="スキャン間隔 (秒)",
    )
    min_obstacle_pixels: int = Field(
        default=50, gt=0, description="障害物判定の最小ピクセル数",
    )
    start_lane: int = Field(
        default=1, ge=0, description="初期レーン (0-indexed)",
    )
    calibration: CalibrationSettings = Field(default_factory=CalibrationSettings)
    controls: ControlSettings = Field(default_factory=ControlSettings)


class DodgeConfig(BaseModel):
    """障害物回避ゲームの設定。"""

    model_config = ConfigDict(extra="forbid")

    version: str = "1.0"
    name: str | None = None
    obstacle: ObstacleColor
    detection_zone: DetectionZone
    lanes: list[LaneConfig]
    runtime: DodgeRuntimeSettings = Field(default_factory=DodgeRuntimeSettings)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("lanes")
    @classmethod
    def _validate_lanes(cls, value: list[LaneConfig]) -> list[LaneConfig]:
        if len(value) < 2:
            msg = "最低 2 レーンが必要です"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_start_lane(self) -> DodgeConfig:
        if self.runtime.start_lane >= len(self.lanes):
            lane_count = len(self.lanes)
            msg = (
                f"start_lane ({self.runtime.start_lane})"
                f" がレーン数 ({lane_count}) を超えています"
            )
            raise ValueError(msg)
        return self


def load_dodge_config(path: Path) -> DodgeConfig:
    text = path.read_text(encoding="utf-8")
    raw = (
        yaml.safe_load(text)
        if path.suffix in {".yaml", ".yml"}
        else json.loads(text)
    )
    if not isinstance(raw, dict):
        msg = "設定ファイルのルートは辞書形式である必要があります"
        raise TypeError(msg)
    raw.setdefault("metadata", {})["__base_dir__"] = str(path.parent)
    return DodgeConfig.model_validate(raw)


# ---------------------------------------------------------------------------
# Lane scan result
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class LaneState:
    """各レーンのスキャン結果。"""

    name: str
    obstacle_pixels: int
    has_obstacle: bool


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class DodgeEngine:
    """3レーン障害物回避のリアルタイムエンジン。"""

    def __init__(
        self,
        config: DodgeConfig,
        region: Region,
        capture_service: ScreenCaptureService | None = None,
        pointer: PointerController | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self._config = config
        self._region = region
        self._capture = capture_service or MSSScreenCaptureService()
        self._pointer = pointer or PointerController()
        self._log = logger or (lambda msg: print(msg, flush=True))
        self._current_lane: int = config.runtime.start_lane

    def run(self, stop_monitor: TerminationMonitor | None = None) -> None:
        cfg = self._config
        self._log(f"[dodge] 開始: {len(cfg.lanes)} レーン監視")
        ob = cfg.obstacle
        self._log(
            f"[dodge] 障害物色: RGB({ob.r}, {ob.g}, {ob.b})"
            f" ±{ob.tolerance}",
        )
        dz = cfg.detection_zone
        self._log(
            f"[dodge] 検出ゾーン: Y={dz.top:.2f}-{dz.bottom:.2f}",
        )
        self._log(f"[dodge] 初期レーン: {cfg.lanes[self._current_lane].name}")

        target_color = np.array(
            [cfg.obstacle.r, cfg.obstacle.g, cfg.obstacle.b],
            dtype=np.int16,
        )
        tol = cfg.obstacle.tolerance
        threshold = cfg.runtime.min_obstacle_pixels
        interval = cfg.runtime.scan_interval

        while True:
            if stop_monitor and stop_monitor.stop_requested():
                break
            if stop_monitor:
                stop_monitor.wait_if_paused()

            frame = self._capture.capture(region=self._region)
            lane_states = self._scan_lanes(frame, target_color, tol, threshold)
            self._decide_and_tap(lane_states)
            time.sleep(interval)

        self._log("[dodge] 終了")

    def _scan_lanes(
        self,
        frame: Image.Image,
        target_color: np.ndarray[Any, np.dtype[np.int16]],
        tolerance: int,
        threshold: int,
    ) -> list[LaneState]:
        arr = np.asarray(frame, dtype=np.int16)
        h, w = arr.shape[:2]
        zone = self._config.detection_zone
        y_top = int(h * zone.top)
        y_bottom = int(h * zone.bottom)
        zone_arr = arr[y_top:y_bottom, :, :3]

        states: list[LaneState] = []
        for lane in self._config.lanes:
            x_start = int(w * lane.x_min)
            x_end = int(w * lane.x_max)
            lane_pixels = zone_arr[:, x_start:x_end]

            diff = np.abs(lane_pixels - target_color)
            mask = np.all(diff <= tolerance, axis=2)
            count = int(mask.sum())

            states.append(LaneState(
                name=lane.name,
                obstacle_pixels=count,
                has_obstacle=count >= threshold,
            ))
        return states

    def _decide_and_tap(self, lane_states: list[LaneState]) -> None:
        safe_indices = [i for i, ls in enumerate(lane_states) if not ls.has_obstacle]
        if not safe_indices:
            return

        if self._current_lane in safe_indices:
            return

        target = min(safe_indices, key=lambda i: abs(i - self._current_lane))
        lane_cfg = self._config.lanes[target]
        prev_name = self._config.lanes[self._current_lane].name

        self._pointer.click_relative(
            self._region,
            (lane_cfg.tap.x, lane_cfg.tap.y),
        )
        self._log(f"[dodge] {prev_name} → {lane_cfg.name}")
        self._current_lane = target
