"""`ProduceEngine` のユニットテスト。

実機を触らず、fake capture + fake pointer を注入してクリック列を検証する。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from auto_emulator.games.produce import (
    GameState,
    LessonOption,
    TurnDecision,
)
from auto_emulator.games.produce.engine import ProduceEngine
from mouse_core import Region


@dataclass
class FakePointer:
    clicks: list[tuple[float, float]] = field(default_factory=list)
    drags: list[tuple[tuple[float, float], tuple[float, float]]] = field(
        default_factory=list,
    )

    def click_relative(
        self,
        region: Region,  # noqa: ARG002
        relative: tuple[float, float],
        **_: object,
    ) -> None:
        self.clicks.append(relative)

    def drag_relative(
        self,
        region: Region,  # noqa: ARG002
        start: tuple[float, float],
        end: tuple[float, float],
        **_: object,
    ) -> None:
        self.drags.append((start, end))


@dataclass
class FakeCapture:
    image: Image.Image

    def capture(self, region: Region) -> Image.Image:  # noqa: ARG002
        return self.image


@dataclass
class FakeStrategy:
    fixed: TurnDecision

    def decide(self, state: GameState) -> TurnDecision:  # noqa: ARG002
        return self.fixed


def _engine(decision: TurnDecision) -> tuple[ProduceEngine, FakePointer]:
    pointer = FakePointer()
    capture = FakeCapture(Image.new("RGB", (3024, 1610)))
    region = Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0)
    engine = ProduceEngine(
        region=region,
        strategy=FakeStrategy(decision),
        capture=capture,
        pointer=pointer,
        click_settle=0.0,
        loop_interval=0.0,
        logger=lambda _: None,
    )
    return engine, pointer


class TestLessonExecution:
    def test_lesson_clicks_card_and_confirm(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="lesson", target_slot=2, rationale="t"),
        )
        state, decision = engine.step()
        assert decision.action_kind == "lesson"
        assert decision.target_slot == 2
        # 2 クリック: カード本体 + 決定ボタン
        assert len(pointer.clicks) == 2
        card_click_x, _ = pointer.clicks[0]
        # slot 2 は LessonRegions のデフォルトで x ~ 0.487
        assert 0.45 < card_click_x < 0.52
        # 決定ボタンは右下
        confirm_x, confirm_y = pointer.clicks[1]
        assert confirm_x > 0.7
        assert confirm_y > 0.8
        # tesseract 不在/フェイク画像でも lessons リストは 6 件のプレースホルダで埋まる
        assert len(state.lessons) == 6

    def test_lesson_invalid_slot_falls_back_to_zero(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="lesson", target_slot=99, rationale="t"),
        )
        engine.step()
        card_click_x, _ = pointer.clicks[0]
        # フォールバックで slot 0 -> x ~ 0.22
        assert 0.18 < card_click_x < 0.26


class TestAuditionExecution:
    def test_audition_taps_tab_then_swipes_then_confirms(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="audition", target_slot=2, rationale="t"),
        )
        engine.step()
        # クリック: タブ + 決定 (target_slot=2 なので 2 回スワイプ)
        assert len(pointer.clicks) == 2
        assert len(pointer.drags) == 2

    def test_audition_slot_zero_does_not_swipe(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="audition", target_slot=0, rationale="t"),
        )
        engine.step()
        assert len(pointer.drags) == 0


class TestUnimplementedActions:
    def test_rest_logs_but_does_not_click(self) -> None:
        messages: list[str] = []
        pointer = FakePointer()
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            strategy=FakeStrategy(
                TurnDecision(action_kind="rest", rationale="t"),
            ),
            capture=FakeCapture(Image.new("RGB", (3024, 1610))),
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=messages.append,
        )
        engine.step()
        assert len(pointer.clicks) == 0
        assert any("not yet implemented" in msg for msg in messages)


class TestRunLoop:
    def test_max_turns_caps_executions(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="lesson", target_slot=0, rationale="t"),
        )
        executed = engine.run(max_turns=3)
        assert executed == 3
        # 1 ターンで 2 クリック (カード + 決定) → 6 クリック
        assert len(pointer.clicks) == 6


class TestCaptureStateMergesLessons:
    def test_lessons_attached_to_state(self) -> None:
        # この test は OCR 失敗を許容するが、lessons リストが必ず付くことを検証
        engine, _ = _engine(
            TurnDecision(action_kind="noop", rationale="t"),
        )
        _, state = engine.capture_state()
        assert isinstance(state, GameState)
        assert isinstance(state.lessons, list)
        # フェイク画像なので 6 件のプレースホルダ (OCR 失敗時の挙動)
        assert len(state.lessons) == 6
        assert all(isinstance(lesson, LessonOption) for lesson in state.lessons)
