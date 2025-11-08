# ruff: noqa: S101

from __future__ import annotations

import importlib
from typing import cast

from PIL import Image
from pynput import keyboard

from auto_emulator import actions as action_module, detectors as detector_module
from auto_emulator.actions import base as action_base, register_action
from auto_emulator.config import (
    ActionSpec,
    AutomationConfig,
    AutomationStep,
    ConditionNode,
    DetectorSpec,
    StepControl,
    TransitionMapping,
    WatchConfig,
)
from auto_emulator.detectors import base as detector_base, register_detector
from auto_emulator.runtime.context import AutomationContext, StepRuntimeContext
from auto_emulator.runtime.engine import AutomationEngine
from auto_emulator.runtime.termination import TerminationMonitor
from auto_emulator.services.capture import FileSequenceCaptureService
from mouse_core.pointer import PointerController
from mouse_core.region import Region


class RecordingPointer:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def click_relative(
        self,
        region: Region,
        relative: tuple[float, float],
        *,
        button: object | None = None,
        ensure_move: bool = True,
    ) -> None:
        self.calls.append(
            {
                "region": region,
                "relative": relative,
                "button": button,
                "ensure_move": ensure_move,
            },
        )


def test_engine_executes_registered_action_once() -> None:
    try:

        @register_action("record")
        class RecordAction(action_base.BaseAction):
            def execute(self, ctx: StepRuntimeContext) -> None:
                ctx.pointer.click_relative(ctx.region, (0.5, 0.5))

        @register_detector("always-match")
        class AlwaysMatchDetector(detector_base.BaseDetector):
            def detect(
                self,
                _watch: WatchConfig,
                _ctx: StepRuntimeContext,
            ) -> detector_base.DetectionResult:
                return detector_base.DetectionResult(matched=True, score=0.99)

        pointer = RecordingPointer()
        config = AutomationConfig(
            version="1.0",
            steps=[
                AutomationStep(
                    id="step1",
                    watch=WatchConfig(detector=DetectorSpec(type="always-match")),
                    conditions=ConditionNode(op="always"),
                    actions=[ActionSpec(type="record")],
                ),
            ],
        )
        engine = AutomationEngine(
            config=config,
            pointer=cast("PointerController", pointer),
            region=Region(left=0, top=0, right=100, bottom=100),
        )

        engine.run()

        assert len(pointer.calls) == 1
        recorded = pointer.calls[0]
        assert cast("tuple[float, float]", recorded["relative"]) == (0.5, 0.5)

    finally:
        importlib.reload(action_module)
        importlib.reload(detector_module)


def test_engine_state_transitions_with_shared_state() -> None:
    pointer = RecordingPointer()
    capture_service = FileSequenceCaptureService([Image.new("RGB", (20, 20), "black")])
    config = AutomationConfig(
        version="1.0",
        steps=[
            AutomationStep(
                id="initialize",
                watch=WatchConfig(detector=DetectorSpec(type="null")),
                conditions=ConditionNode(op="always"),
                actions=[
                    ActionSpec(
                        type="set_state", options={"key": "phase", "value": "phase1"}
                    ),
                ],
                transitions=TransitionMapping(success="loop_phase"),
            ),
            AutomationStep(
                id="loop_phase",
                watch=WatchConfig(detector=DetectorSpec(type="null")),
                conditions=ConditionNode(
                    op="state_equals", options={"key": "phase", "value": "phase1"}
                ),
                actions=[
                    ActionSpec(type="wait", options={"duration": 0.0}),
                ],
                control=StepControl(repeat=2),
                transitions=TransitionMapping(success="finalize"),
            ),
            AutomationStep(
                id="finalize",
                watch=WatchConfig(detector=DetectorSpec(type="null")),
                conditions=ConditionNode(
                    op="state_equals", options={"key": "phase", "value": "phase1"}
                ),
                actions=[
                    ActionSpec(
                        type="set_state", options={"key": "phase", "value": "complete"}
                    ),
                ],
            ),
        ],
    )
    region = Region(left=0, top=0, right=20, bottom=20)
    engine = AutomationEngine(
        config=config,
        pointer=cast("PointerController", pointer),
        region=region,
        capture_service=capture_service,
    )
    context = AutomationContext(
        config=config,
        pointer=cast("PointerController", pointer),
        capture_service=capture_service,
        calibration_region=region,
    )
    context.reset_region_cache()
    current_id: str | None = config.steps[0].id
    while current_id is not None:
        executor = engine._executors[current_id]  # noqa: SLF001
        current_id = executor.run(context)
    assert context.shared_state["phase"] == "complete"


def test_engine_stops_when_monitor_requests_stop() -> None:
    pointer = RecordingPointer()
    capture_service = FileSequenceCaptureService([Image.new("RGB", (20, 20), "black")])
    config = AutomationConfig(
        version="1.0",
        steps=[
            AutomationStep(
                id="loop",
                watch=WatchConfig(detector=DetectorSpec(type="null")),
                conditions=ConditionNode(op="always"),
                actions=[ActionSpec(type="log", options={"message": "should not run"})],
                control=StepControl(repeat=3),
            ),
        ],
    )
    engine = AutomationEngine(
        config=config,
        pointer=cast("PointerController", pointer),
        region=Region(left=0, top=0, right=20, bottom=20),
        capture_service=capture_service,
    )
    monitor = TerminationMonitor()
    monitor._on_press(keyboard.Key.esc)  # noqa: SLF001
    engine.run(stop_monitor=monitor)
    monitor.stop()


def test_run_watch_returns_failure_when_stop_requested() -> None:
    pointer = RecordingPointer()
    capture_service = FileSequenceCaptureService([Image.new("RGB", (20, 20), "black")])
    config = AutomationConfig(
        version="1.0",
        steps=[
            AutomationStep(
                id="loop",
                watch=WatchConfig(detector=DetectorSpec(type="null")),
                conditions=ConditionNode(op="always"),
                actions=[],
            ),
        ],
    )
    engine = AutomationEngine(
        config=config,
        pointer=cast("PointerController", pointer),
        region=Region(left=0, top=0, right=20, bottom=20),
        capture_service=capture_service,
    )
    executor = engine._executors["loop"]  # noqa: SLF001
    context = AutomationContext(
        config=config,
        pointer=cast("PointerController", pointer),
        capture_service=capture_service,
        calibration_region=Region(left=0, top=0, right=20, bottom=20),
    )
    step_ctx = StepRuntimeContext(context=context, step=config.steps[0])
    monitor = TerminationMonitor()
    monitor._on_press(keyboard.Key.esc)  # noqa: SLF001
    result_key, detection = executor._run_watch(  # noqa: SLF001
        step_ctx,
        stop_monitor=monitor,
    )
    monitor.stop()
    assert result_key == "failure"
    assert detection.data is not None
    assert detection.data["reason"] == "user_stop"
