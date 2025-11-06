from __future__ import annotations

from typing import Any

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
