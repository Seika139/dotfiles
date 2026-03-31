from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from PIL import Image

from auto_emulator.games.dodge import (
    DodgeConfig,
    DodgeEngine,
    LaneConfig,
    ObstacleColor,
    TapPosition,
    load_dodge_config,
)
from mouse_core import Region

TAP_LEFT = TapPosition(x=0.17, y=0.9)
TAP_CENTER = TapPosition(x=0.5, y=0.9)
TAP_RIGHT = TapPosition(x=0.83, y=0.9)

LANES = [
    LaneConfig(name="left", x_min=0.0, x_max=0.33, tap=TAP_LEFT),
    LaneConfig(name="center", x_min=0.33, x_max=0.66, tap=TAP_CENTER),
    LaneConfig(name="right", x_min=0.66, x_max=1.0, tap=TAP_RIGHT),
]

LANE_BOUNDARIES = [(0.0, 0.33), (0.33, 0.66), (0.66, 1.0)]


def _make_config(
    *,
    min_pixels: int = 10,
    start_lane: int = 1,
) -> DodgeConfig:
    return DodgeConfig(
        version="1.0",
        obstacle=ObstacleColor(r=255, g=0, b=0),
        detection_zone={"top": 0.4, "bottom": 0.6},
        lanes=LANES,
        runtime={
            "min_obstacle_pixels": min_pixels,
            "start_lane": start_lane,
            "calibration": {"enabled": False},
        },
    )


def _make_frame(
    width: int = 300,
    height: int = 100,
    obstacle_lanes: list[int] | None = None,
    color: tuple[int, int, int] = (255, 0, 0),
) -> Image.Image:
    arr = np.full((height, width, 3), 128, dtype=np.uint8)
    zone_top = int(height * 0.4)
    zone_bottom = int(height * 0.6)
    if obstacle_lanes:
        for lane_idx in obstacle_lanes:
            x_min, x_max = LANE_BOUNDARIES[lane_idx]
            x_start = int(width * x_min) + 2
            x_end = int(width * x_max) - 2
            arr[zone_top:zone_bottom, x_start:x_end] = color
    return Image.fromarray(arr, "RGB")


def _make_stop_monitor(*, max_iterations: int = 1) -> MagicMock:
    call_count = 0

    def stop_check() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > max_iterations

    return MagicMock(
        stop_requested=stop_check,
        wait_if_paused=lambda: None,
    )


class TestDodgeConfig:
    def test_valid_config(self) -> None:
        config = _make_config()
        assert len(config.lanes) == 3
        assert config.obstacle.r == 255

    def test_too_few_lanes(self) -> None:
        with pytest.raises(Exception, match="最低 2 レーン"):
            DodgeConfig(
                obstacle=ObstacleColor(r=255, g=0, b=0),
                detection_zone={"top": 0.4, "bottom": 0.6},
                lanes=[
                    LaneConfig(
                        name="only",
                        x_min=0.0,
                        x_max=1.0,
                        tap=TAP_CENTER,
                    ),
                ],
            )

    def test_invalid_start_lane(self) -> None:
        with pytest.raises(Exception, match="start_lane"):
            _make_config(start_lane=5)

    def test_detection_zone_invalid(self) -> None:
        with pytest.raises(Exception, match="bottom"):
            DodgeConfig(
                obstacle=ObstacleColor(r=255, g=0, b=0),
                detection_zone={"top": 0.8, "bottom": 0.2},
                lanes=[
                    LaneConfig(
                        name="a",
                        x_min=0.0,
                        x_max=0.5,
                        tap=TapPosition(x=0.25, y=0.5),
                    ),
                    LaneConfig(
                        name="b",
                        x_min=0.5,
                        x_max=1.0,
                        tap=TapPosition(x=0.75, y=0.5),
                    ),
                ],
            )


class TestDodgeEngine:
    def _build_engine(
        self,
        config: DodgeConfig | None = None,
        frames: list[Image.Image] | None = None,
    ) -> tuple[DodgeEngine, MagicMock, list[str]]:
        cfg = config or _make_config()
        region = Region(left=0, top=0, right=300, bottom=100)
        capture = MagicMock()
        if frames:
            capture.capture.side_effect = frames
        else:
            capture.capture.return_value = _make_frame()
        pointer = MagicMock()
        logs: list[str] = []
        engine = DodgeEngine(
            config=cfg,
            region=region,
            capture_service=capture,
            pointer=pointer,
            logger=logs.append,
        )
        return engine, pointer, logs

    def test_stays_in_safe_lane(self) -> None:
        frame = _make_frame(obstacle_lanes=[])
        engine, pointer, _logs = self._build_engine(frames=[frame])
        engine.run(stop_monitor=_make_stop_monitor())
        pointer.click_relative.assert_not_called()

    def test_moves_to_safe_lane(self) -> None:
        frame = _make_frame(obstacle_lanes=[1, 2])
        engine, pointer, _logs = self._build_engine(frames=[frame])
        engine.run(stop_monitor=_make_stop_monitor())
        pointer.click_relative.assert_called_once()
        tap_pos = pointer.click_relative.call_args[0][1]
        assert tap_pos == (0.17, 0.9)

    def test_prefers_current_lane(self) -> None:
        config = _make_config(start_lane=0)
        frame = _make_frame(obstacle_lanes=[2])
        engine, pointer, _logs = self._build_engine(
            config=config, frames=[frame],
        )
        engine.run(stop_monitor=_make_stop_monitor())
        pointer.click_relative.assert_not_called()

    def test_moves_to_closest_safe_lane(self) -> None:
        config = _make_config(start_lane=2)
        frame = _make_frame(obstacle_lanes=[0, 2])
        engine, pointer, _logs = self._build_engine(
            config=config, frames=[frame],
        )
        engine.run(stop_monitor=_make_stop_monitor())
        pointer.click_relative.assert_called_once()
        tap_pos = pointer.click_relative.call_args[0][1]
        assert tap_pos == (0.5, 0.9)


class TestScanLanes:
    def test_detects_obstacle_in_lane(self) -> None:
        config = _make_config(min_pixels=5)
        region = Region(left=0, top=0, right=300, bottom=100)
        engine = DodgeEngine(
            config=config,
            region=region,
            capture_service=MagicMock(),
            pointer=MagicMock(),
        )
        frame = _make_frame(obstacle_lanes=[0, 2])
        target = np.array([255, 0, 0], dtype=np.int16)
        states = engine._scan_lanes(frame, target, 30, 5)

        assert states[0].has_obstacle is True
        assert states[1].has_obstacle is False
        assert states[2].has_obstacle is True

    def test_no_obstacle_detected(self) -> None:
        config = _make_config(min_pixels=5)
        region = Region(left=0, top=0, right=300, bottom=100)
        engine = DodgeEngine(
            config=config,
            region=region,
            capture_service=MagicMock(),
            pointer=MagicMock(),
        )
        frame = _make_frame(obstacle_lanes=[])
        target = np.array([255, 0, 0], dtype=np.int16)
        states = engine._scan_lanes(frame, target, 30, 5)

        assert all(not s.has_obstacle for s in states)


class TestLoadDodgeConfig:
    def test_load_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "test.yml"
        config_file.write_text(
            """\
version: "1.0"
obstacle:
  r: 200
  g: 50
  b: 50
  tolerance: 20
detection_zone:
  top: 0.3
  bottom: 0.5
lanes:
  - name: left
    x_min: 0.0
    x_max: 0.5
    tap: {x: 0.25, y: 0.9}
  - name: right
    x_min: 0.5
    x_max: 1.0
    tap: {x: 0.75, y: 0.9}
runtime:
  start_lane: 0
  calibration:
    enabled: false
""",
            encoding="utf-8",
        )
        config = load_dodge_config(config_file)
        assert config.obstacle.r == 200
        assert len(config.lanes) == 2
        assert config.runtime.start_lane == 0
