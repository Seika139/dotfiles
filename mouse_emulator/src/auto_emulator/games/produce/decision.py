"""GameState から 1 ターンの行動を決定する純関数エンジン。

副作用なし。テスト容易性を最優先する設計:
    decision = StrategyEngine().decide(state)

実機のクリック発行は呼び出し側 (action layer) が担当する。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from auto_emulator.games.produce.state import GameState
from auto_emulator.games.produce.strategy import (
    SEASON_STAT_CAPS,
    SEASON_STRATEGY,
    SeasonPlan,
)


class DialogChoiceRule(BaseModel):
    """3 択ダイアログのキーワードマッチング規則。

    `prompt` に `prompt_keywords` のいずれかが含まれるとき、選択肢から
    `option_keywords` を含む最初の候補を選ぶ。
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_keywords: tuple[str, ...]
    option_keywords: tuple[str, ...]
    description: str = ""


# 既定の文脈判定規則。先頭の規則ほど優先度が高い。
DEFAULT_DIALOG_RULES: tuple[DialogChoiceRule, ...] = (
    DialogChoiceRule(
        prompt_keywords=("緊張", "落ち着", "リラックス", "ほぐ"),
        option_keywords=("いつも通り", "落ち着", "リラックス"),
        description="緊張を解く -> いつも通り (テンション維持)",
    ),
    DialogChoiceRule(
        prompt_keywords=("練習", "上達", "頑張"),
        option_keywords=("頑張", "本気", "全力"),
        description="練習文脈 -> 全力 (ステータス重視)",
    ),
    DialogChoiceRule(
        prompt_keywords=("休", "リフレッシュ", "気分転換"),
        option_keywords=("休", "ゆっくり"),
        description="休む文脈 -> 休む (体力維持)",
    ),
)


def choose_dialog_option(
    prompt: str,
    options: tuple[str, ...],
    *,
    rules: tuple[DialogChoiceRule, ...] = DEFAULT_DIALOG_RULES,
    fallback_index: int = 2,
) -> int:
    """3 択ダイアログで選ぶインデックスを決める純関数。

    Args:
        prompt: プロデューサーの問いかけテキスト。
        options: 選択肢テキスト (1-3 個想定)。
        rules: 優先度順の規則タプル。
        fallback_index: マッチしないときの既定 (default は黄色: M11)。

    Returns:
        選択肢のインデックス (0-based)。`options` 長より小さい範囲に正規化。
    """
    if not options:
        return 0
    for rule in rules:
        if not any(kw in prompt for kw in rule.prompt_keywords):
            continue
        for idx, option in enumerate(options):
            if any(kw in option for kw in rule.option_keywords):
                return idx
    return min(fallback_index, len(options) - 1)


ActionKind = Literal["lesson", "rest", "audition", "reflection", "item", "noop"]

# WING 準決勝/決勝で出現することが多い特別オーディション名のキーワード。
# 名前に含まれていれば「WING 系」と判定する。
WING_AUDITION_KEYWORDS: tuple[str, ...] = (
    "THE LEGEND",
    "LEGEND",
    "オールアイドル感謝",
    "感謝FESTIVAL",
    "WING",
)


def is_wing_audition(name: str) -> bool:
    """オーディション名が WING 準決勝/決勝相当かを判定する。

    Args:
        name: OCR 等で取得したオーディション名。

    Returns:
        WING フローのオーディションなら True。
    """
    return any(keyword in name for keyword in WING_AUDITION_KEYWORDS)


def _stat_fulfillment_ratio(
    current: dict[str, int],
    recommended: dict[str, int],
) -> float:
    """全推奨ステに対する充足率の最低値を返す。

    Args:
        current: 現在のステータス辞書。
        recommended: 推奨能力値辞書。

    Returns:
        各推奨ステの (current / recommended) の最小値。
        recommended が空なら 1.0 (条件なしとみなして許可)。
    """
    if not recommended:
        return 1.0
    ratios: list[float] = []
    for stat_name, required in recommended.items():
        if required <= 0:
            continue
        have = current.get(stat_name, 0)
        ratios.append(have / required)
    if not ratios:
        return 1.0
    return min(ratios)


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
    target_audition_name: str | None = Field(
        default=None,
        description=(
            "G2: audition 実行時の目的カード名。Engine が swipe ループで "
            "OCR と前方一致 → 一致したら early break する。`None` なら "
            "従来通り `target_slot` 回固定 swipe にフォールバック"
        ),
    )


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
        stat_caps: dict[int, dict[str, int]] | None = None,
    ) -> None:
        self._strategy = (
            strategy_table if strategy_table is not None else SEASON_STRATEGY
        )
        self._stat_caps = stat_caps if stat_caps is not None else SEASON_STAT_CAPS

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

        audition_pick = self._pick_audition(state, plan)
        if audition_pick is not None:
            slot, name, ratio = audition_pick
            return TurnDecision(
                action_kind="audition",
                target_slot=slot,
                target_audition_name=name,
                rationale=(
                    f"season {season} audition '{name}' at slot {slot} "
                    f"(stat ratio {ratio:.0%})"
                ),
            )

        reflect_reason = self._should_reflect(state, plan)
        if reflect_reason is not None:
            return TurnDecision(
                action_kind="reflection",
                rationale=reflect_reason,
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

    def _should_reflect(self, state: GameState, plan: SeasonPlan) -> str | None:
        """振り返り発動可否を判定。

        Returns:
            発動するなら判定理由 (ログ用文字列)、しないなら `None`。
        """
        if not plan.skill_phase:
            return None
        if state.week_remaining is None or state.week_remaining < 2:
            return None
        season = state.season
        if season is None or state.stats is None:
            return None
        caps = self._stat_caps.get(season)
        if not caps:
            return None
        for stat_name, current in state.stats.items():
            cap = caps.get(stat_name)
            if cap is None or cap <= 0:
                continue
            ratio = current / cap
            if ratio >= plan.reflect_stat_proximity:
                return (
                    f"stat cap proximity: {stat_name}={current}/{cap} "
                    f"({ratio:.0%} >= {plan.reflect_stat_proximity:.0%})"
                )
        return None

    @staticmethod
    def _pick_audition(
        state: GameState,
        plan: SeasonPlan,
    ) -> tuple[int, str, float] | None:
        """戦略テーブルに合致するオーディションを推奨能力値で評価して選ぶ。

        WING 系オーディション (`is_wing_audition`) は同じ ratio でも優先する。
        S4 で THE LEGEND / オールアイドル感謝 を取りこぼさないため。

        Returns:
            (slot, name, stat_ratio) もしくは選ばないなら None。
            ratio はステ充足率 (1.0 = 推奨値ぴったり、>1.0 = 余裕あり)。
        """
        if not plan.target_auditions:
            return None
        if not state.available_auditions:
            if state.audition_available:
                return 0, plan.target_auditions[0], 1.0
            return None
        best: tuple[int, str, float] | None = None
        best_is_wing = False
        for option in state.available_auditions:
            if not any(target in option.name for target in plan.target_auditions):
                continue
            ratio = _stat_fulfillment_ratio(state.stats or {}, option.recommended_stats)
            if ratio < plan.audition_min_stat_ratio:
                continue
            this_is_wing = is_wing_audition(option.name)
            candidate = (option.slot, option.name, ratio)
            if best is None:
                best, best_is_wing = candidate, this_is_wing
                continue
            # WING vs 非 WING は WING 優先、同種なら ratio 比較
            if this_is_wing and not best_is_wing:
                best, best_is_wing = candidate, True
            elif this_is_wing == best_is_wing and ratio > best[2]:
                best = candidate
        return best

    @staticmethod
    def _pick_lesson_slot(
        state: GameState,
        plan: SeasonPlan,
    ) -> tuple[int, str] | None:
        """優先キーワードの 1 個目から順に、該当するレッスンを探して返す.

        `plan.prefer_fans_efficiency=True` なら同じ優先キーワード内で
        `preview_fans` 最大を選ぶが、#40 の知見により実機 UI では
        per-card の `preview_fans` は単一フレームで取れず常に None。
        そのため現状この分岐は常に「順序最先」にフォールバックする
        (graceful degradation)。将来 multi-frame 選択巡回で per-card
        fans を埋められれば自動的にこの分岐が活きる。優先順位を跨いだ
        比較はしない (M10 の S1 ラジオ最優先のような序列を壊さないため)。

        Returns:
            (slot, name) もしくは見つからなければ None。
        """
        if not state.lessons:
            return None
        for preferred in plan.primary_lesson_preference:
            matches = [
                lesson for lesson in state.lessons if preferred in lesson.name
            ]
            if not matches:
                continue
            if plan.prefer_fans_efficiency:
                with_fans = [m for m in matches if m.preview_fans is not None]
                if with_fans:
                    best = max(with_fans, key=lambda m: m.preview_fans or 0)
                    return best.slot, best.name
            return matches[0].slot, matches[0].name
        return None
