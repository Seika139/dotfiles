"""アクション実装のレジストリとデフォルト実装群。"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar, cast

from pynput import mouse

from auto_emulator.actions.base import BaseAction
from auto_emulator.config import ActionSpec
from auto_emulator.exceptions import ConfigurationError
from auto_emulator.runtime.context import StepRuntimeContext

_ACTION_REGISTRY: dict[str, type[BaseAction]] = {}
T_Action = TypeVar("T_Action", bound=type[BaseAction])


def register_action(name: str) -> Callable[[T_Action], T_Action]:
    canonical = name.strip().lower()

    def decorator(cls: T_Action) -> T_Action:
        _ACTION_REGISTRY[canonical] = cls
        return cls

    return decorator


def create_action(spec: ActionSpec) -> BaseAction:
    action_type = spec.type.strip().lower()
    impl = _ACTION_REGISTRY.get(action_type)
    if impl is None:
        raise ConfigurationError(f"未登録の action.type が指定されました: {spec.type}")
    return impl(spec)


def _resolve_button(options: dict[str, object]) -> mouse.Button:
    button_name = cast("str | None", options.get("button"))
    if button_name is None:
        return mouse.Button.left
    normalized = button_name.lower()
    mapping = {
        "left": mouse.Button.left,
        "right": mouse.Button.right,
        "middle": mouse.Button.middle,
    }
    if normalized not in mapping:
        msg = f"未対応のボタン指定です: {button_name}"
        raise ConfigurationError(msg)
    return mapping[normalized]


def _resolve_relative_point(
    ctx: StepRuntimeContext,
    source: dict[str, object] | None,
    *,
    default_to_detection: bool = True,
) -> tuple[float, float]:
    if source is None:
        if default_to_detection:
            detection = ctx.last_detection
            if detection and detection.region is not None:
                region = detection.region
                center_x = region.left + region.width / 2
                center_y = region.top + region.height / 2
                rel_x, rel_y = ctx.region.to_relative(center_x, center_y)
                return rel_x, rel_y
        msg = "アクションのターゲット座標が指定されていません"
        raise ConfigurationError(msg)
    if "relative" in source:
        relative = source["relative"]
        if (
            not isinstance(relative, (list, tuple))
            or len(relative) != 2
            or not all(isinstance(value, (int, float)) for value in relative)
        ):
            msg = "relative は [x, y] 形式で指定してください"
            raise ConfigurationError(msg)
        return float(relative[0]), float(relative[1])
    if source.get("use_detection", False):
        detection = ctx.last_detection
        if detection and detection.region is not None:
            region = detection.region
            center_x = region.left + region.width / 2
            center_y = region.top + region.height / 2
            rel_x, rel_y = ctx.region.to_relative(center_x, center_y)
            return rel_x, rel_y
        msg = "検出結果が存在しないため、use_detection を利用できません"
        raise ConfigurationError(msg)
    msg = "サポートされていないターゲット指定方法です"
    raise ConfigurationError(msg)


def _apply_offset(
    point: tuple[float, float],
    offset: tuple[float, float] | None,
) -> tuple[float, float]:
    if offset is None:
        return point
    return point[0] + offset[0], point[1] + offset[1]


def _extract_offset(raw_offset: object) -> tuple[float, float] | None:
    if raw_offset is None:
        return None
    if (
        not isinstance(raw_offset, (list, tuple))
        or len(raw_offset) != 2
        or not all(isinstance(value, (int, float)) for value in raw_offset)
    ):
        msg = "offset は [x, y] 形式で指定してください"
        raise ConfigurationError(msg)
    return float(raw_offset[0]), float(raw_offset[1])


@register_action("noop")
class NoOpAction(BaseAction):
    def execute(self, ctx: StepRuntimeContext) -> None:  # noqa: ARG002
        """何もしないアクション。設定の動作検証用に利用する。"""
        return


@register_action("click")
class ClickAction(BaseAction):
    def execute(self, ctx: StepRuntimeContext) -> None:
        options = self.spec.options
        target_spec = cast("dict[str, object] | None", options.get("target"))
        offset = _extract_offset(options.get("offset"))
        relative = _apply_offset(
            _resolve_relative_point(ctx, target_spec),
            offset,
        )
        button = _resolve_button(options)
        pointer = ctx.pointer
        if self.spec.pointer_mode == "absolute":
            abs_x, abs_y = ctx.region.to_absolute(*relative)
            pointer.click_absolute(abs_x, abs_y, button=button)
        else:
            pointer.click_relative(ctx.region, relative, button=button)


@register_action("wait")
class WaitAction(BaseAction):
    def execute(self, ctx: StepRuntimeContext) -> None:  # noqa: ARG002
        duration = cast("float | None", self.spec.options.get("duration"))
        if duration is None or duration < 0:
            msg = "wait アクションには正の duration が必要です"
            raise ConfigurationError(msg)
        time.sleep(duration)


@register_action("drag")
class DragAction(BaseAction):
    def execute(self, ctx: StepRuntimeContext) -> None:
        options = self.spec.options
        start_spec = cast("dict[str, object] | None", options.get("start"))
        end_spec = cast("dict[str, object] | None", options.get("end"))
        if end_spec is None:
            msg = "drag アクションには end ターゲットが必要です"
            raise ConfigurationError(msg)
        start_offset = _extract_offset(
            options.get("start_offset") or options.get("offset")
        )
        end_offset = _extract_offset(options.get("end_offset") or options.get("offset"))
        start_relative = _apply_offset(
            _resolve_relative_point(ctx, start_spec, default_to_detection=True),
            start_offset,
        )
        end_relative = _apply_offset(
            _resolve_relative_point(ctx, end_spec, default_to_detection=False),
            end_offset,
        )
        button = _resolve_button(options)
        steps = int(options.get("steps", 12))
        step_delay = float(options.get("step_delay", 0.01))
        hold_duration = float(options.get("hold", 0.05))
        ctx.pointer.drag_relative(
            ctx.region,
            start_relative,
            end_relative,
            button=button,
            profile=(steps, step_delay, hold_duration),
        )


@register_action("set_state")
class SetStateAction(BaseAction):
    def execute(self, ctx: StepRuntimeContext) -> None:
        options = self.spec.options
        key = options.get("key")
        if not isinstance(key, str) or not key:
            msg = "set_state アクションには key が必要です"
            raise ConfigurationError(msg)
        if options.get("remove", False):
            ctx.context.shared_state.pop(key, None)
            return
        ctx.context.shared_state[key] = options.get("value")
