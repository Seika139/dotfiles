# ruff: noqa: S101

from __future__ import annotations

from typing import Any, cast

from PIL import Image

from auto_emulator.conditions import ConditionEvaluator
from auto_emulator.config import (
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


class DummyPointer:
    def click_relative(
        self,
        _region: Region,
        _relative: tuple[float, float],
        *,
        button: object | None = None,
        ensure_move: bool = True,
    ) -> None:
        del button, ensure_move

    def click_absolute(
        self,
        _x: int,
        _y: int,
        *,
        button: object | None = None,
        ensure_move: bool = True,
    ) -> None:
        del button, ensure_move

    def drag_relative(
        self,
        _region: Region,
        _start: tuple[float, float],
        _end: tuple[float, float],
        *,
        button: object | None = None,
        profile: tuple[int, float, float] | None = None,
    ) -> None:
        del button, profile


def _make_step_context(
    shared_state: dict[str, Any] | None = None,
) -> StepRuntimeContext:
    detector = DetectorSpec(type="null")
    watch = WatchConfig(detector=detector)
    step = AutomationStep(id="dummy", watch=watch)
    config = AutomationConfig(version="1.0", steps=[step])
    config.metadata["__base_dir__"] = "."
    image = Image.new("RGB", (10, 10), color="black")
    capture_service = FileSequenceCaptureService([image])
    context = AutomationContext(
        config=config,
        pointer=cast("PointerController", DummyPointer()),
        capture_service=capture_service,
        calibration_region=Region(left=0, top=0, right=10, bottom=10),
    )
    if shared_state:
        context.shared_state.update(shared_state)
    return StepRuntimeContext(context=context, step=step)


def make_result(
    *,
    matched: bool,
    score: float | None = None,
    data: dict[str, Any] | None = None,
) -> DetectionResult:
    return DetectionResult(
        matched=matched,
        score=score,
        data=data,
        region=None,
    )


def test_always_and_never() -> None:
    ctx = _make_step_context()
    evaluator = ConditionEvaluator(
        ConditionNode(op="all", conditions=[ConditionNode(op="always")]),
    )
    assert evaluator.evaluate(make_result(matched=False), ctx=ctx)

    evaluator = ConditionEvaluator(ConditionNode(op="never"))
    assert not evaluator.evaluate(make_result(matched=True), ctx=ctx)


def test_match_min_score() -> None:
    ctx = _make_step_context()
    evaluator = ConditionEvaluator(
        ConditionNode(op="match", options={"min_score": 0.8}),
    )
    assert evaluator.evaluate(make_result(matched=True, score=0.95), ctx=ctx)
    assert not evaluator.evaluate(make_result(matched=True, score=0.5), ctx=ctx)
    assert not evaluator.evaluate(make_result(matched=False, score=0.95), ctx=ctx)


def test_any_and_not_combination() -> None:
    ctx = _make_step_context()
    evaluator = ConditionEvaluator(
        ConditionNode(
            op="any",
            conditions=[
                ConditionNode(op="never"),
                ConditionNode(op="not", conditions=[ConditionNode(op="match")]),
            ],
        ),
    )
    assert evaluator.evaluate(make_result(matched=False), ctx=ctx)
    assert not evaluator.evaluate(make_result(matched=True), ctx=ctx)


def test_state_conditions() -> None:
    ctx = _make_step_context({"phase": "intro"})
    equals = ConditionEvaluator(
        ConditionNode(op="state_equals", options={"key": "phase", "value": "intro"}),
    )
    assert equals.evaluate(make_result(matched=True), ctx=ctx)
    not_equals = ConditionEvaluator(
        ConditionNode(
            op="state_not_equals", options={"key": "phase", "value": "battle"}
        ),
    )
    assert not_equals.evaluate(make_result(matched=True), ctx=ctx)


def test_text_conditions() -> None:
    ctx = _make_step_context()
    result = make_result(matched=True, data={"text": "Mission Complete"})
    contains = ConditionEvaluator(
        ConditionNode(
            op="text_contains",
            options={"value": "complete"},
        ),
    )
    assert contains.evaluate(result, ctx=ctx)
    equals = ConditionEvaluator(
        ConditionNode(
            op="text_equals",
            options={"value": "mission complete"},
        ),
    )
    assert equals.evaluate(result, ctx=ctx)
    matches = ConditionEvaluator(
        ConditionNode(
            op="text_matches",
            options={"value": r"mission\s+com"},
        ),
    )
    assert matches.evaluate(result, ctx=ctx)
