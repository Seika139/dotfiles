"""`StrategyEngine.decide` のユニットテスト。

純関数なので画像なし。GameState を直接組み立てて期待される行動を検証する。
"""

from __future__ import annotations

import pytest

from auto_emulator.games.produce import (
    GameState,
    LessonOption,
    SeasonPlan,
    StrategyEngine,
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

    @pytest.mark.skip(reason="Phase 4: 上限近接判定実装後にテスト追加")
    def test_reflects_when_stat_cap_near(self) -> None:
        pass
