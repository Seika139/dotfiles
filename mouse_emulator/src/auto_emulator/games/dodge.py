"""障害物回避ゲーム用エンジン。

3レーン構成の画面で上から降ってくる障害物を検出し、
安全なレーンをタップして回避する。
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pytesseract  # type: ignore[import-untyped]
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
        default=30,
        ge=0,
        le=255,
        description="各チャンネルの許容誤差",
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
        default=0.03,
        gt=0.0,
        description="スキャン間隔 (秒)",
    )
    min_obstacle_pixels: int = Field(
        default=50,
        gt=0,
        description="障害物判定の最小ピクセル数",
    )
    start_lane: int = Field(
        default=1,
        ge=0,
        description="初期レーン (0-indexed)",
    )
    calibration: CalibrationSettings = Field(default_factory=CalibrationSettings)
    controls: ControlSettings = Field(default_factory=ControlSettings)


class ScoreRegion(BaseModel):
    """スコア表示領域の相対座標。"""

    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0.0, le=1.0, description="スコア領域の左端 (相対)")
    y: float = Field(ge=0.0, le=1.0, description="スコア領域の上端 (相対)")
    width: float = Field(gt=0.0, le=1.0, description="スコア領域の幅 (相対)")
    height: float = Field(gt=0.0, le=1.0, description="スコア領域の高さ (相対)")
    interval: float = Field(
        default=1.0,
        gt=0.0,
        description="スコア読取り間隔 (秒)",
    )
    threshold: int | None = Field(
        default=180,
        ge=0,
        le=255,
        description="二値化閾値 (None=無効)",
    )
    tesseract_config: str = Field(
        default="--psm 7 -c tessedit_char_whitelist=0123456789",
        description="tesseract オプション",
    )


class Phase(BaseModel):
    """スコア閾値に応じたパラメータ変更。"""

    model_config = ConfigDict(extra="forbid")

    min_score: int = Field(ge=0, description="このフェーズが有効になる最低スコア")
    detection_zone: DetectionZone | None = None
    scan_interval: float | None = Field(default=None, gt=0.0)
    min_obstacle_pixels: int | None = Field(default=None, gt=0)


class DodgeConfig(BaseModel):
    """障害物回避ゲームの設定。"""

    model_config = ConfigDict(extra="forbid")

    version: str = "1.0"
    name: str | None = None
    obstacle: ObstacleColor
    detection_zone: DetectionZone
    lanes: list[LaneConfig]
    runtime: DodgeRuntimeSettings = Field(default_factory=DodgeRuntimeSettings)
    score_region: ScoreRegion | None = None
    phases: list[Phase] | None = None
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

    @model_validator(mode="after")
    def _validate_phases(self) -> DodgeConfig:
        if self.phases and not self.score_region:
            msg = "phases を指定する場合は score_region も必要です"
            raise ValueError(msg)
        return self


def load_dodge_config(path: Path) -> DodgeConfig:
    text = path.read_text(encoding="utf-8")
    raw = yaml.safe_load(text) if path.suffix in {".yaml", ".yml"} else json.loads(text)
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

        # フェーズ管理
        self._current_phase: Phase | None = None
        self._active_detection_zone: DetectionZone = config.detection_zone
        self._active_scan_interval: float = config.runtime.scan_interval
        self._active_threshold: int = config.runtime.min_obstacle_pixels
        self._last_score: int = 0
        self._sorted_phases: list[Phase] = []
        if config.phases:
            self._sorted_phases = sorted(
                config.phases,
                key=lambda p: p.min_score,
                reverse=True,
            )

    @property
    def current_phase(self) -> Phase | None:
        return self._current_phase

    @property
    def last_score(self) -> int:
        return self._last_score

    def run(self, stop_monitor: TerminationMonitor | None = None) -> None:
        cfg = self._config
        self._log(f"[dodge] 開始: {len(cfg.lanes)} レーン監視")
        ob = cfg.obstacle
        self._log(
            f"[dodge] 障害物色: RGB({ob.r}, {ob.g}, {ob.b}) ±{ob.tolerance}",
        )
        dz = cfg.detection_zone
        self._log(
            f"[dodge] 検出ゾーン: Y={dz.top:.2f}-{dz.bottom:.2f}",
        )
        self._log(f"[dodge] 初期レーン: {cfg.lanes[self._current_lane].name}")
        if self._sorted_phases:
            self._log(
                f"[dodge] フェーズ数: {len(self._sorted_phases)}"
                " (スコアに応じて動的切替)",
            )

        target_color = np.array(
            [cfg.obstacle.r, cfg.obstacle.g, cfg.obstacle.b],
            dtype=np.int16,
        )
        tol = cfg.obstacle.tolerance
        last_score_check = 0.0
        score_interval = cfg.score_region.interval if cfg.score_region else float("inf")

        while True:
            if stop_monitor and stop_monitor.stop_requested():
                break
            if stop_monitor:
                stop_monitor.wait_if_paused()

            frame = self._capture.capture(region=self._region)

            # 定期的なスコア読取り & フェーズ切替
            now = time.monotonic()
            if (
                cfg.score_region
                and self._sorted_phases
                and (now - last_score_check) >= score_interval
            ):
                self._update_score(frame)
                last_score_check = now

            lane_states = self._scan_lanes(
                frame,
                target_color,
                tol,
                self._active_threshold,
            )
            self._decide_and_tap(lane_states)
            time.sleep(self._active_scan_interval)

        self._log("[dodge] 終了")

    def _read_score(self, frame: Image.Image) -> int | None:
        sr = self._config.score_region
        if sr is None:
            return None
        w, h = frame.size
        left = int(w * sr.x)
        upper = int(h * sr.y)
        right = int(w * (sr.x + sr.width))
        lower = int(h * (sr.y + sr.height))
        crop = frame.crop((left, upper, right, lower)).convert("L")
        if sr.threshold is not None:
            crop = crop.point(lambda v: 255 if v > sr.threshold else 0)
        try:
            text = pytesseract.image_to_string(
                crop,
                config=sr.tesseract_config,
            )
        except Exception:  # noqa: BLE001
            return None
        digits = re.sub(r"\D", "", text)
        if not digits:
            return None
        return int(digits)

    def _update_score(self, frame: Image.Image) -> None:
        score = self._read_score(frame)
        if score is None:
            return
        self._last_score = score
        new_phase: Phase | None = None
        for phase in self._sorted_phases:
            if score >= phase.min_score:
                new_phase = phase
                break
        if new_phase is self._current_phase:
            return
        self._current_phase = new_phase
        if new_phase is None:
            self._active_detection_zone = self._config.detection_zone
            self._active_scan_interval = self._config.runtime.scan_interval
            self._active_threshold = self._config.runtime.min_obstacle_pixels
            self._log(f"[dodge] スコア {score}: デフォルトフェーズに復帰")
            return
        if new_phase.detection_zone is not None:
            self._active_detection_zone = new_phase.detection_zone
        else:
            self._active_detection_zone = self._config.detection_zone
        if new_phase.scan_interval is not None:
            self._active_scan_interval = new_phase.scan_interval
        else:
            self._active_scan_interval = self._config.runtime.scan_interval
        if new_phase.min_obstacle_pixels is not None:
            self._active_threshold = new_phase.min_obstacle_pixels
        else:
            self._active_threshold = self._config.runtime.min_obstacle_pixels
        self._log(
            f"[dodge] スコア {score}: フェーズ変更"
            f" (min_score={new_phase.min_score},"
            f" zone={self._active_detection_zone.top:.2f}"
            f"-{self._active_detection_zone.bottom:.2f},"
            f" interval={self._active_scan_interval})",
        )

    def _scan_lanes(
        self,
        frame: Image.Image,
        target_color: np.ndarray[Any, np.dtype[np.int16]],
        tolerance: int,
        threshold: int,
    ) -> list[LaneState]:
        arr = np.asarray(frame, dtype=np.int16)
        h, w = arr.shape[:2]
        zone = self._active_detection_zone
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

            states.append(
                LaneState(
                    name=lane.name,
                    obstacle_pixels=count,
                    has_obstacle=count >= threshold,
                )
            )
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
