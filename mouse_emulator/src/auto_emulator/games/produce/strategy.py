"""シーズン別のプロデュース戦略テーブル。

各シーズンで「優先するレッスン」「目標オーディション」「ファン目標」
「休息判定の閾値」を持つ。決定エンジンはこのテーブルを引いて分岐する。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SeasonPlan(BaseModel):
    """1 シーズンの戦略プラン。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    primary_lesson_preference: tuple[str, ...] = Field(
        description="優先するレッスン名 (前方一致)。先頭ほど優先度高",
    )
    target_auditions: tuple[str, ...] = Field(
        default=(),
        description="このシーズンで挑戦するオーディション名 (前方一致)",
    )
    skill_phase: bool = Field(
        default=False,
        description="振り返りでスキル取得を行うフェーズか",
    )
    fan_target: int = Field(
        gt=0,
        description="True End に必要なファン数",
    )
    rest_trouble_threshold: int = Field(
        default=5,
        ge=0,
        le=100,
        description="この%以上のトラブル率で休息候補に上げる",
    )
    rest_hp_threshold: float = Field(
        default=0.5,
        gt=0.0,
        le=1.0,
        description="この HP 比率を下回り、かつトラブル率が閾値超なら休む",
    )


# シャニマス WING True End ルートのデフォルト戦略。
SEASON_STRATEGY: dict[int, SeasonPlan] = {
    1: SeasonPlan(
        primary_lesson_preference=("ラジオの収録", "雑誌の撮影", "トークイベント"),
        target_auditions=(),
        skill_phase=False,
        fan_target=1000,
    ),
    2: SeasonPlan(
        primary_lesson_preference=(
            "ボーカルレッスン",
            "ダンスレッスン",
            "ビジュアルレッスン",
            "ラジオの収録",
        ),
        target_auditions=("夕方ワイド",),
        skill_phase=True,
        fan_target=10000,
    ),
    3: SeasonPlan(
        primary_lesson_preference=(
            "ボーカルレッスン",
            "ダンスレッスン",
            "ビジュアルレッスン",
        ),
        target_auditions=("SPOT LIGHT", "踊っていいとも"),
        skill_phase=True,
        fan_target=200000,
    ),
    4: SeasonPlan(
        primary_lesson_preference=(
            "ボーカルレッスン",
            "ダンスレッスン",
            "ビジュアルレッスン",
        ),
        target_auditions=("THE LEGEND", "オールアイドル感謝"),
        skill_phase=True,
        fan_target=500000,
    ),
}
