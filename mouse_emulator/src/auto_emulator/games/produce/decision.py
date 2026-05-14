"""GameState から 1 ターンの行動を決定する純関数エンジン。

副作用なし。テスト容易性を最優先する設計:
    decision = StrategyEngine().decide(state)

実機のクリック発行は呼び出し側 (action layer) が担当する。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from auto_emulator.games.produce.state import GameState
from auto_emulator.games.produce.strategy import SEASON_STRATEGY, SeasonPlan

ActionKind = Literal["lesson", "rest", "audition", "reflection", "item", "noop"]


class TurnDecision(BaseModel):
    """1 ターンに実行すべき行動。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action_kind: ActionKind
    target_slot: int = Field(
        default=0,
        ge=0,
        description="lesson カード番号 / audition カード番号。それ以外は 0",
    )
    rationale: str = Field(description="決定理由 (ログ用)")


class StrategyEngine:
    """シーズン戦略に基づき GameState → TurnDecision を返す。

    決定の優先順位 (上から早期 return):
    1. 強制チュートリアル: `audition_available=True` で WING フローの
       「ちょっと待ってください」相当のときは audition 必須 (M6)
    2. 体力 + トラブル率による休息判定 (M5)
    3. シーズン戦略の特別オーディション (M4)
    4. 振り返り (M7) - skill_phase かつ十分な余裕があるとき
    5. 戦略レッスン (M11)
    """

    def __init__(
        self,
        strategy_table: dict[int, SeasonPlan] | None = None,
    ) -> None:
        self._strategy = (
            strategy_table if strategy_table is not None else SEASON_STRATEGY
        )

    def decide(self, state: GameState) -> TurnDecision:
        season = state.season or 1
        plan = self._strategy.get(season)
        if plan is None:
            return TurnDecision(
                action_kind="noop",
                rationale=f"unknown season={season}",
            )

        if self._should_rest(state, plan):
            return TurnDecision(
                action_kind="rest",
                rationale=(
                    f"trouble={state.trouble_pct}% hp={state.hp_pct or 0.0:.0%} "
                    f"(thresholds {plan.rest_trouble_threshold}% / "
                    f"{plan.rest_hp_threshold:.0%})"
                ),
            )

        if state.audition_available and plan.target_auditions:
            return TurnDecision(
                action_kind="audition",
                target_slot=0,
                rationale=(
                    f"season {season} target audition: {plan.target_auditions[0]}"
                ),
            )

        if self._should_reflect(state, plan):
            return TurnDecision(
                action_kind="reflection",
                rationale=(
                    f"skill_phase season={season} "
                    f"weeks_remaining={state.week_remaining}"
                ),
            )

        chosen = self._pick_lesson_slot(state, plan)
        if chosen is None:
            return TurnDecision(
                action_kind="lesson",
                target_slot=0,
                rationale="no preference match; fallback slot 0",
            )
        slot, name = chosen
        return TurnDecision(
            action_kind="lesson",
            target_slot=slot,
            rationale=f"preferred lesson '{name}' at slot {slot}",
        )

    @staticmethod
    def _should_rest(state: GameState, plan: SeasonPlan) -> bool:
        trouble = state.trouble_pct or 0
        if trouble < plan.rest_trouble_threshold:
            return False
        hp = state.hp_pct
        if hp is None:
            # 体力が読めない場合は安全側 (休まない)。リーダー側で要対応
            return False
        return hp < plan.rest_hp_threshold

    @staticmethod
    def _should_reflect(state: GameState, plan: SeasonPlan) -> bool:
        if not plan.skill_phase:
            return False
        # 週数が十分残っていない (ファン目標まで遠い) ときは振り返りせず加速
        if state.week_remaining is None or state.week_remaining < 2:
            return False
        # まだ細かな発動条件 (スキルポイント有無、上限突破可能か) を入れていない。
        # Phase 4 で「上限近接判定」を加えて確度を上げる。
        return False

    @staticmethod
    def _pick_lesson_slot(
        state: GameState,
        plan: SeasonPlan,
    ) -> tuple[int, str] | None:
        if not state.lessons:
            return None
        for preferred in plan.primary_lesson_preference:
            for lesson in state.lessons:
                if preferred in lesson.name:
                    return lesson.slot, lesson.name
        return None
