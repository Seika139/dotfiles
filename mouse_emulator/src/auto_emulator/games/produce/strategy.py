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
        description="この%以上のトラブル率なら休む (休息はトラブル率のみで判定)",
    )
    rest_hp_threshold: float = Field(
        default=0.5,
        gt=0.0,
        le=1.0,
        description=(
            "この HP 比率を下回ったら体力回復コマンドの選択優先度を上げる"
            " 閾値 (休息判定には使わない)"
        ),
    )
    reflect_stat_proximity: float = Field(
        default=0.85,
        gt=0.0,
        le=1.0,
        description="シーズン上限のこの比率以上に到達したステがあれば振り返り発動",
    )
    audition_min_stat_ratio: float = Field(
        default=0.6,
        gt=0.0,
        le=2.0,
        description=(
            "推奨能力値に対する充足率の最低ライン。"
            "全ステがこの比率未満ならオーディションを skip"
        ),
    )
    prefer_fans_efficiency: bool = Field(
        default=False,
        description=(
            "G3: 同じ優先順位のレッスンが複数あったときに preview_fans が"
            "高いものを優先する。preview_fans が None のカードは比較対象外"
        ),
    )


# シーズンごとのステ上限 (Vo/Da/Vi)。実機計測値の概数で初期値とする。
# 実機データで補正することが前提のため `STAT_CAPS` は const ではなく公開定数。
SEASON_STAT_CAPS: dict[int, dict[str, int]] = {
    1: {"Vo": 150, "Da": 150, "Vi": 150, "Me": 200},
    2: {"Vo": 300, "Da": 300, "Vi": 300, "Me": 400},
    3: {"Vo": 500, "Da": 500, "Vi": 500, "Me": 600},
    4: {"Vo": 800, "Da": 800, "Vi": 800, "Me": 900},
}


# シャニマス WING True End ルートのデフォルト戦略。
SEASON_STRATEGY: dict[int, SeasonPlan] = {
    1: SeasonPlan(
        primary_lesson_preference=("ラジオの収録", "雑誌の撮影", "トークイベント"),
        target_auditions=(),
        skill_phase=False,
        fan_target=1000,
        # M10: S1 はファン稼ぎ最重視。同優先順位なら fans 効率高を選ぶ
        prefer_fans_efficiency=True,
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
