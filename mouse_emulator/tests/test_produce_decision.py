"""`StrategyEngine.decide` のユニットテスト。

純関数なので画像なし。GameState を直接組み立てて期待される行動を検証する。
"""

from __future__ import annotations

from auto_emulator.games.produce import (
    AuditionOption,
    GameState,
    LessonOption,
    SeasonPlan,
    StrategyEngine,
    is_wing_audition,
)


def _state(**overrides: object) -> GameState:
    base: dict[str, object] = {
        "season": 1,
        "week_remaining": 5,
        "fans_to_target": 500,
        "hp_pct": 1.0,
        "trouble_pct": 0,
        "lessons": [],
    }
    base.update(overrides)
    return GameState.model_validate(base)


def _lessons(*names_with_levels: tuple[str, int]) -> list[LessonOption]:
    return [
        LessonOption(slot=i, name=name, level=lv)
        for i, (name, lv) in enumerate(names_with_levels)
    ]


class TestRestRule:
    def test_rests_when_trouble_high_and_hp_low(self) -> None:
        engine = StrategyEngine()
        state = _state(trouble_pct=10, hp_pct=0.3)
        decision = engine.decide(state)
        assert decision.action_kind == "rest"

    def test_does_not_rest_when_trouble_low(self) -> None:
        engine = StrategyEngine()
        state = _state(
            trouble_pct=2,
            hp_pct=0.3,
            lessons=_lessons(("ラジオの収録", 1)),
        )
        decision = engine.decide(state)
        assert decision.action_kind != "rest"

    def test_does_not_rest_when_hp_high(self) -> None:
        engine = StrategyEngine()
        state = _state(
            trouble_pct=10,
            hp_pct=0.9,
            lessons=_lessons(("ラジオの収録", 1)),
        )
        decision = engine.decide(state)
        assert decision.action_kind != "rest"

    def test_does_not_rest_when_hp_unknown(self) -> None:
        engine = StrategyEngine()
        state = _state(
            trouble_pct=10,
            hp_pct=None,
            lessons=_lessons(("ラジオの収録", 1)),
        )
        decision = engine.decide(state)
        # 体力が読めない時は安全側 (= rest しない)
        assert decision.action_kind != "rest"


class TestLessonPreference:
    def test_season_1_prefers_radio(self) -> None:
        engine = StrategyEngine()
        state = _state(
            season=1,
            lessons=_lessons(
                ("ボーカルレッスン", 3),
                ("ダンスレッスン", 1),
                ("ラジオの収録", 2),
            ),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "lesson"
        assert decision.target_slot == 2  # ラジオの収録 が slot 2

    def test_season_2_prefers_vocal_lesson(self) -> None:
        engine = StrategyEngine()
        state = _state(
            season=2,
            lessons=_lessons(
                ("ラジオの収録", 2),
                ("ボーカルレッスン", 3),
                ("ダンスレッスン", 1),
            ),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "lesson"
        assert decision.target_slot == 1  # ボーカルレッスン が slot 1

    def test_fallback_when_no_preference_matches(self) -> None:
        engine = StrategyEngine()
        state = _state(
            season=1,
            lessons=_lessons(("ボーカルレッスン", 3), ("ダンスレッスン", 1)),
        )
        decision = engine.decide(state)
        # S1 の好みリストにヒットしない -> fallback (slot 0)
        assert decision.action_kind == "lesson"
        assert decision.target_slot == 0
        assert "fallback" in decision.rationale


class TestAuditionRule:
    def test_takes_target_audition_when_available(self) -> None:
        engine = StrategyEngine()
        state = _state(
            season=2,
            audition_available=True,
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "audition"
        assert "夕方ワイド" in decision.rationale

    def test_skips_audition_in_season_1(self) -> None:
        # S1 は target_auditions が空 -> オーディション選ばない
        engine = StrategyEngine()
        state = _state(
            season=1,
            audition_available=True,
            lessons=_lessons(("ラジオの収録", 2)),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "lesson"

    def test_audition_picked_when_stats_sufficient(self) -> None:
        # S2 「夕方ワイド」推奨 Vi=150 / Vo=150 で stats が 200 -> ratio 1.33 > 0.6
        engine = StrategyEngine()
        state = _state(
            season=2,
            stats={"Vo": 200, "Da": 200, "Vi": 200, "Me": 100, "SP": 30, "Fans": 5000},
            available_auditions=[
                AuditionOption(
                    slot=2,
                    name="夕方ワイド アイドル一番",
                    difficulty=8,
                    recommended_stats={"Vo": 150, "Vi": 150},
                ),
            ],
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "audition"
        assert decision.target_slot == 2

    def test_audition_skipped_when_stats_insufficient(self) -> None:
        # ratio = 50/150 = 0.33 < 0.6 -> skip
        engine = StrategyEngine()
        state = _state(
            season=2,
            stats={"Vo": 50, "Da": 50, "Vi": 50, "Me": 50, "SP": 30, "Fans": 5000},
            available_auditions=[
                AuditionOption(
                    slot=0,
                    name="夕方ワイド アイドル一番",
                    difficulty=8,
                    recommended_stats={"Vo": 150, "Vi": 150},
                ),
            ],
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "lesson"

    def test_audition_picks_highest_stat_ratio(self) -> None:
        # 2 候補: A=ratio 1.0, B=ratio 2.0 -> B を選ぶ
        engine = StrategyEngine()
        state = _state(
            season=2,
            stats={"Vo": 300, "Da": 300, "Vi": 300, "Me": 100, "SP": 30, "Fans": 5000},
            available_auditions=[
                AuditionOption(
                    slot=0,
                    name="夕方ワイド A",
                    difficulty=10,
                    recommended_stats={"Vo": 300},
                ),
                AuditionOption(
                    slot=2,
                    name="夕方ワイド B",
                    difficulty=5,
                    recommended_stats={"Vo": 150},
                ),
            ],
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "audition"
        assert decision.target_slot == 2  # ratio 2.0 のほう

    def test_legacy_audition_available_flag_still_works(self) -> None:
        # available_auditions=[] でも audition_available=True なら旧挙動
        engine = StrategyEngine()
        state = _state(
            season=2,
            audition_available=True,
            available_auditions=[],
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "audition"
        assert decision.target_slot == 0


class TestWingAudition:
    def test_is_wing_audition_recognizes_legend(self) -> None:
        assert is_wing_audition("THE LEGEND") is True
        assert is_wing_audition("THE LEGEND FINALE") is True

    def test_is_wing_audition_recognizes_appreciation(self) -> None:
        assert is_wing_audition("オールアイドル感謝FESTIVAL") is True

    def test_is_wing_audition_rejects_regular(self) -> None:
        assert is_wing_audition("夕方ワイド アイドル一番") is False
        assert is_wing_audition("BE@T") is False

    def test_wing_audition_prioritized_over_regular(self) -> None:
        # S4 戦略で WING (THE LEGEND) と非 WING (オールアイドル感謝も WING 扱い
        # なので別キーワードで非 WING 候補を作る) - target_auditions に両方含める
        plan = SeasonPlan(
            primary_lesson_preference=("ボーカルレッスン",),
            target_auditions=("THE LEGEND", "夕方ワイド"),
            fan_target=500000,
            audition_min_stat_ratio=0.5,
        )
        engine = StrategyEngine(strategy_table={4: plan})
        state = GameState.model_validate(
            {
                "season": 4,
                "week_remaining": 5,
                "fans_to_target": 100000,
                "hp_pct": 1.0,
                "trouble_pct": 0,
                "stats": {
                    "Vo": 500,
                    "Da": 500,
                    "Vi": 500,
                    "Me": 100,
                    "SP": 30,
                    "Fans": 400000,
                },
                "available_auditions": [
                    AuditionOption(
                        slot=0,
                        name="夕方ワイド A",  # 非 WING、ratio 高い
                        difficulty=8,
                        recommended_stats={"Vo": 200},
                    ),
                    AuditionOption(
                        slot=3,
                        name="THE LEGEND",  # WING、ratio 普通
                        difficulty=20,
                        recommended_stats={"Vo": 400, "Da": 400, "Vi": 400},
                    ),
                ],
            },
        )
        decision = engine.decide(state)
        assert decision.action_kind == "audition"
        # WING 優先で slot=3 が選ばれる
        assert decision.target_slot == 3
        assert "THE LEGEND" in decision.rationale


class TestSeasonFallback:
    def test_unknown_season_returns_noop(self) -> None:
        engine = StrategyEngine(strategy_table={})
        state = _state(season=1)
        decision = engine.decide(state)
        assert decision.action_kind == "noop"

    def test_custom_strategy_overrides_default(self) -> None:
        custom = {
            1: SeasonPlan(
                primary_lesson_preference=("ダンスレッスン",),
                fan_target=1000,
            ),
        }
        engine = StrategyEngine(strategy_table=custom)
        state = _state(
            season=1,
            lessons=_lessons(("ラジオの収録", 2), ("ダンスレッスン", 1)),
        )
        decision = engine.decide(state)
        assert decision.target_slot == 1


class TestReflectionRule:
    def test_does_not_reflect_in_season_1(self) -> None:
        engine = StrategyEngine()
        state = _state(
            season=1,
            week_remaining=10,
            lessons=_lessons(("ラジオの収録", 2)),
        )
        decision = engine.decide(state)
        assert decision.action_kind != "reflection"

    def test_reflects_when_stat_cap_near(self) -> None:
        # S2 cap Vo=300 -> 260 (87%) で 0.85 閾値を超える
        engine = StrategyEngine()
        state = _state(
            season=2,
            week_remaining=5,
            stats={"Vo": 260, "Da": 100, "Vi": 100, "Me": 100, "SP": 30, "Fans": 5000},
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "reflection"
        assert "Vo" in decision.rationale

    def test_does_not_reflect_when_stats_below_proximity(self) -> None:
        engine = StrategyEngine()
        state = _state(
            season=2,
            week_remaining=5,
            stats={"Vo": 100, "Da": 100, "Vi": 100, "Me": 100, "SP": 30, "Fans": 5000},
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind != "reflection"

    def test_does_not_reflect_when_weeks_remaining_low(self) -> None:
        # week_remaining=1 -> 振り返りせず加速
        engine = StrategyEngine()
        state = _state(
            season=2,
            week_remaining=1,
            stats={"Vo": 290, "Da": 100, "Vi": 100, "Me": 100, "SP": 30, "Fans": 5000},
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind != "reflection"

    def test_does_not_reflect_when_stats_unknown(self) -> None:
        engine = StrategyEngine()
        state = _state(
            season=2,
            week_remaining=5,
            stats=None,
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind != "reflection"

    def test_custom_stat_caps_override(self) -> None:
        # Vo=100 でも cap=100 にすれば 100% 達成 -> 振り返り発動
        engine = StrategyEngine(
            stat_caps={2: {"Vo": 100}},
        )
        state = _state(
            season=2,
            week_remaining=5,
            stats={"Vo": 100, "Da": 100, "Vi": 100, "Me": 100, "SP": 30, "Fans": 5000},
            lessons=_lessons(("ボーカルレッスン", 3)),
        )
        decision = engine.decide(state)
        assert decision.action_kind == "reflection"
