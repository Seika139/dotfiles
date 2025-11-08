from __future__ import annotations

import re
from typing import Any, Literal

from auto_emulator.config import ConditionNode
from auto_emulator.detectors import DetectionResult
from auto_emulator.exceptions import ConfigurationError
from auto_emulator.runtime.context import StepRuntimeContext


class ConditionEvaluator:
    def __init__(self, root: ConditionNode | None) -> None:
        self._root = root

    def evaluate(
        self,
        result: DetectionResult,
        ctx: StepRuntimeContext,
    ) -> bool:
        if self._root is None:
            return True
        return self._evaluate_node(self._root, result, ctx)

    def _evaluate_node(
        self,
        node: ConditionNode,
        result: DetectionResult,
        ctx: StepRuntimeContext,
    ) -> bool:
        op = node.op
        if op == "always":
            return True
        if op == "never":
            return False
        if op == "match":
            return self._evaluate_match(node.options, result)
        if op == "not":
            return not self._evaluate_node(node.conditions[0], result, ctx)
        if op == "all":
            return all(
                self._evaluate_node(child, result, ctx) for child in node.conditions
            )
        if op == "any":
            return any(
                self._evaluate_node(child, result, ctx) for child in node.conditions
            )
        if op == "state_equals":
            return self._evaluate_state(node.options, ctx, negate=False)
        if op == "state_not_equals":
            return self._evaluate_state(node.options, ctx, negate=True)
        if op == "text_contains":
            return self._evaluate_text_condition(node.options, result, mode="contains")
        if op == "text_equals":
            return self._evaluate_text_condition(node.options, result, mode="equals")
        if op == "text_matches":
            return self._evaluate_text_condition(node.options, result, mode="matches")
        message = f"未対応の条件演算子が指定されました: {op}"
        raise ConfigurationError(message)

    @staticmethod
    def _evaluate_match(options: dict[str, Any], result: DetectionResult) -> bool:
        if not result.matched:
            return False
        min_score = options.get("min_score")
        if min_score is None or result.score is None:
            return True
        return result.score >= float(min_score)

    @staticmethod
    def _evaluate_state(
        options: dict[str, Any],
        ctx: StepRuntimeContext,
        *,
        negate: bool,
    ) -> bool:
        key = options.get("key")
        if not isinstance(key, str) or not key:
            raise ConfigurationError("state 条件には key が必要です")
        expected = options.get("value")
        actual = ctx.context.shared_state.get(key)
        result = actual == expected
        return not result if negate else result

    @staticmethod
    def _evaluate_text_condition(
        options: dict[str, Any],
        result: DetectionResult,
        *,
        mode: Literal["contains", "equals", "matches"],
    ) -> bool:
        data = result.data or {}
        text_obj = data.get("text")
        if not isinstance(text_obj, str):
            return False
        target = options.get("value")
        if target is None:
            raise ConfigurationError("text 条件には value が必要です")
        ignore_case = bool(options.get("ignore_case", True))
        source = text_obj.lower() if ignore_case else text_obj
        if mode == "contains":
            expected = str(target).lower() if ignore_case else str(target)
            return expected in source
        if mode == "equals":
            expected = str(target).lower() if ignore_case else str(target)
            return source == expected
        pattern = str(target)
        flags = re.IGNORECASE if ignore_case else 0
        return re.search(pattern, source, flags) is not None
