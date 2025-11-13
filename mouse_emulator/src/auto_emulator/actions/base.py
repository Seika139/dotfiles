from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, cast

from auto_emulator.config import ActionSpec
from auto_emulator.runtime.context import StepRuntimeContext

T_Option = TypeVar("T_Option")


class BaseAction(ABC):
    """アクション実装の抽象基底クラス。"""

    def __init__(self, spec: ActionSpec) -> None:
        self.spec = spec

    @abstractmethod
    def execute(self, ctx: StepRuntimeContext) -> None:
        """ステップの実行コンテキストでアクションを実行する。"""

    def resolve_option(
        self,
        name: str,
        default: T_Option | None = None,
    ) -> T_Option | None:
        value = self.spec.options.get(name, default)
        return cast("T_Option | None", value)
