from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from auto_emulator.actions import create_action
from auto_emulator.actions.base import BaseAction
from auto_emulator.conditions import ConditionEvaluator
from auto_emulator.config import (
    AutomationConfig,
    AutomationStep,
    StepControl,
    TransitionMapping,
    WatchConfig,
)
from auto_emulator.detectors import BaseDetector, DetectionResult, create_detector
from auto_emulator.exceptions import ConfigurationError, EngineRuntimeError
from auto_emulator.runtime.context import AutomationContext, StepRuntimeContext
from auto_emulator.runtime.termination import TerminationMonitor
from auto_emulator.services.capture import PILScreenCaptureService, ScreenCaptureService
from mouse_core import PointerController, Region


@dataclass(slots=True)
class StepExecutor:
    step: AutomationStep
    detector: BaseDetector
    actions: list[BaseAction]
    transitions: TransitionMapping | None
    control: StepControl | None
    evaluator: ConditionEvaluator
    log: Callable[[str], None]

    def run(
        self,
        ctx: AutomationContext,
        stop_monitor: TerminationMonitor | None = None,
    ) -> str | None:
        step_ctx = StepRuntimeContext(context=ctx, step=self.step)
        max_repeat = self._resolve_repeat()
        iteration = 0
        target_duration = self.control.max_duration if self.control else None
        start_time = time.monotonic()
        while True:
            if stop_monitor and stop_monitor.stop_requested():
                return None
            if stop_monitor:
                stop_monitor.wait_if_paused()
            step_ctx.iteration = iteration
            step_ctx.last_detection = None
            self._emit_step_header(step_ctx)
            result_key, detection = self._run_watch(step_ctx, stop_monitor)
            step_ctx.last_detection = detection
            self._emit_detection_summary(result_key, detection)
            next_step = self._handle_result(result_key, step_ctx)
            iteration += 1
            if self._should_break(
                iteration,
                max_repeat,
                result_key,
                start_time,
                target_duration,
            ):
                return next_step

    def _resolve_repeat(self) -> int | None:
        if self.control is None or self.control.repeat is None:
            return 1
        if isinstance(self.control.repeat, int):
            return self.control.repeat
        if self.control.repeat == "infinite":
            return None
        message = f"未対応の repeat 指定です: {self.control.repeat}"
        raise ConfigurationError(message)

    def _should_break(
        self,
        iteration: int,
        max_repeat: int | None,
        result_key: str,
        start_time: float,
        target_duration: float | None,
    ) -> bool:
        if (
            target_duration is not None
            and (time.monotonic() - start_time) >= target_duration
        ):
            return True
        if (
            self.control
            and self.control.break_on
            and self.control.break_on == result_key
        ):
            return True
        if max_repeat is None:
            return False
        return iteration >= max_repeat

    def _handle_result(
        self,
        result_key: str,
        step_ctx: StepRuntimeContext,
    ) -> str | None:
        if result_key == "success":
            for action in self.actions:
                action.execute(step_ctx)
        transitions = self.transitions or TransitionMapping()
        if result_key == "success":
            return transitions.success or transitions.default
        if result_key == "failure":
            return transitions.failure or transitions.default
        if result_key == "timeout":
            return transitions.timeout or transitions.default
        return transitions.default

    def _run_watch(
        self,
        step_ctx: StepRuntimeContext,
        stop_monitor: TerminationMonitor | None,
    ) -> tuple[str, DetectionResult]:
        watch = self.step.watch
        attempts_remaining = self._resolve_attempts(watch)
        interval = watch.interval or step_ctx.config.runtime.capture_interval
        start_time = time.monotonic()
        while True:
            if stop_monitor and stop_monitor.stop_requested():
                fallback = DetectionResult(
                    matched=False,
                    score=None,
                    data={"reason": "user_stop"},
                    region=None,
                )
                return "failure", fallback
            if stop_monitor:
                stop_monitor.wait_if_paused()
            detection = self.detector.detect(watch, step_ctx)
            if self.evaluator.evaluate(detection, step_ctx):
                return "success", detection
            if watch.stop_on_failure:
                return "failure", detection
            if attempts_remaining is not None:
                attempts_remaining -= 1
                if attempts_remaining <= 0:
                    return "failure", detection
            if (
                watch.timeout is not None
                and (time.monotonic() - start_time) >= watch.timeout
            ):
                return "timeout", detection
            time.sleep(interval)

    @staticmethod
    def _resolve_attempts(watch: WatchConfig) -> int | None:
        attempts = watch.max_attempts
        if attempts is None or attempts == "infinite":
            return None
        return attempts

    def _emit_step_header(self, step_ctx: StepRuntimeContext) -> None:
        attempt = step_ctx.iteration + 1
        self.log(f"[auto] step={step_ctx.step.id} attempt={attempt}")

    def _emit_detection_summary(
        self,
        result_key: str,
        detection: DetectionResult,
    ) -> None:
        score_repr = f"{detection.score:.3f}" if detection.score is not None else "n/a"
        self.log(f"[auto] result={result_key} score={score_repr}")


class AutomationEngine:
    def __init__(
        self,
        config: AutomationConfig,
        pointer: PointerController | None = None,
        region: Region | None = None,
        capture_service: ScreenCaptureService | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self._config = config
        self._pointer = pointer or PointerController()
        self._region = region
        self._capture_service = capture_service or PILScreenCaptureService()
        self._logger = logger or (lambda message: print(message, flush=True))
        self._executors: dict[str, StepExecutor] = {}
        self._prepare()

    def _prepare(self) -> None:
        for step in self._config.steps:
            detector = create_detector(step.watch.detector)
            actions = [create_action(spec) for spec in step.actions] or []
            evaluator = ConditionEvaluator(step.conditions)
            executor = StepExecutor(
                step=step,
                detector=detector,
                actions=actions,
                transitions=step.transitions,
                control=step.control,
                evaluator=evaluator,
                log=self._logger,
            )
            self._executors[step.id] = executor

    def run(self, stop_monitor: TerminationMonitor | None = None) -> None:
        if not self._config.steps:
            raise EngineRuntimeError("実行可能なステップが設定されていません")
        context = AutomationContext(
            config=self._config,
            pointer=self._pointer,
            capture_service=self._capture_service,
            calibration_region=self._region,
        )
        context.reset_region_cache()
        current_id: str | None = self._config.steps[0].id
        executed_steps = 0
        iteration_limit = self._config.runtime.max_iterations
        while current_id is not None:
            if stop_monitor and stop_monitor.stop_requested():
                break
            if stop_monitor:
                stop_monitor.wait_if_paused()
            executor = self._executors.get(current_id)
            if executor is None:
                raise EngineRuntimeError(
                    f"未知のステップIDが参照されました: {current_id}",
                )
            current_id = executor.run(context, stop_monitor=stop_monitor)
            executed_steps += 1
            if iteration_limit is not None and executed_steps >= iteration_limit:
                break
