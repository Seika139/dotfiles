from __future__ import annotations

from typing import cast

import pytest
from PIL import Image

from auto_emulator.actions import create_action
from auto_emulator.config import (
    ActionSpec,
    AutomationConfig,
    AutomationStep,
    ConditionNode,
    DetectorSpec,
    WatchConfig,
)
from auto_emulator.detectors.base import DetectionResult
from auto_emulator.runtime.context import AutomationContext, StepRuntimeContext
from auto_emulator.services.capture import FileSequenceCaptureService
from mouse_core.pointer import PointerController
from mouse_core.region import Region


class RecordingPointer:
    def __init__(self) -> None:
        self.clicks: list[tuple[float, float]] = []
        self.drags: list[tuple[tuple[float, float], tuple[float, float]]] = []

    def click_relative(
        self,
        _region: Region,
        relative: tuple[float, float],
        *,
        button: object | None = None,
        ensure_move: bool = True,
    ) -> None:
        del button, ensure_move
        self.clicks.append(relative)

    def click_absolute(
        self,
        x: int,
        y: int,
        *,
        button: object | None = None,
        ensure_move: bool = True,
    ) -> None:
        del button, ensure_move
        self.clicks.append((float(x), float(y)))

    def drag_relative(
        self,
        _region: Region,
        start: tuple[float, float],
        end: tuple[float, float],
        *,
        button: object | None = None,
        profile: tuple[int, float, float] | None = None,
    ) -> None:
        del button, profile
        self.drags.append((start, end))


def _make_context(pointer: RecordingPointer) -> StepRuntimeContext:
    detector = DetectorSpec(type="null")
    watch = WatchConfig(detector=detector)
    step = AutomationStep(id="step", watch=watch, conditions=ConditionNode(op="always"))
    config = AutomationConfig(version="1.0", steps=[step])
    image = Image.new("RGB", (20, 20), color="black")
    capture = FileSequenceCaptureService([image])
    context = AutomationContext(
        config=config,
        pointer=cast("PointerController", pointer),
        capture_service=capture,
        calibration_region=Region(left=0, top=0, right=20, bottom=20),
    )
    return StepRuntimeContext(context=context, step=step)


def test_set_state_action_updates_context() -> None:
    pointer = RecordingPointer()
    ctx = _make_context(pointer)
    action = create_action(
        ActionSpec(type="set_state", options={"key": "phase", "value": "main"}),
    )
    action.execute(ctx)
    assert ctx.context.shared_state["phase"] == "main"


def test_click_action_uses_detection_center() -> None:
    pointer = RecordingPointer()
    ctx = _make_context(pointer)
    ctx.last_detection = DetectionResult(
        matched=True,
        score=0.9,
        data=None,
        region=Region(left=5, top=5, right=15, bottom=15),
    )
    action = create_action(ActionSpec(type="click"))
    action.execute(ctx)
    assert pointer.clicks[-1] == pytest.approx((0.5, 0.5), abs=0.05)


def test_drag_action_executes() -> None:
    pointer = RecordingPointer()
    ctx = _make_context(pointer)
    ctx.last_detection = DetectionResult(
        matched=True,
        score=0.9,
        data=None,
        region=Region(left=5, top=5, right=15, bottom=15),
    )
    action = create_action(
        ActionSpec(
            type="drag",
            options={
                "end": {"relative": [0.8, 0.5]},
            },
        ),
    )
    action.execute(ctx)
    assert pointer.drags[-1][0] == pytest.approx((0.5, 0.5), abs=0.05)


def test_log_action_prints_message(capsys: pytest.CaptureFixture[str]) -> None:
    pointer = RecordingPointer()
    ctx = _make_context(pointer)
    action = create_action(
        ActionSpec(type="log", options={"message": "Hello automation!"}),
    )
    action.execute(ctx)
    captured = capsys.readouterr()
    assert "Hello automation!" in captured.out
