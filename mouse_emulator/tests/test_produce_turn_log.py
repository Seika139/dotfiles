"""`JsonlTurnLogger` と `TurnLogEntry` のユニットテスト。"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from auto_emulator.games.produce import (
    GameState,
    JsonlTurnLogger,
    LessonOption,
    TurnDecision,
    TurnLogEntry,
)
from auto_emulator.games.produce.engine import ProduceEngine
from mouse_core import Region


class TestTurnLogEntry:
    def test_from_state_and_decision_copies_fields(self) -> None:
        state = GameState(
            season=2,
            week_remaining=8,
            fans_to_target=6225,
            hp_pct=0.5,
            trouble_pct=8,
            tension_lv=1,
            stats={"Vo": 226, "Da": 128},
            lessons=[LessonOption(slot=0, name="ボーカルレッスン", level=3)],
        )
        decision = TurnDecision(
            action_kind="lesson",
            target_slot=2,
            rationale="preferred lesson",
        )
        entry = TurnLogEntry.from_state_and_decision(5, state, decision)
        assert entry.turn_number == 5
        assert entry.season == 2
        assert entry.week_remaining == 8
        assert entry.fans_to_target == 6225
        assert entry.hp_pct == 0.5
        assert entry.trouble_pct == 8
        assert entry.tension_lv == 1
        assert entry.stats == {"Vo": 226, "Da": 128}
        assert entry.decision_action_kind == "lesson"
        assert entry.decision_target_slot == 2
        assert entry.decision_rationale == "preferred lesson"
        assert entry.stop_reason is None

    def test_stop_reason_propagated(self) -> None:
        state = GameState(season=4)
        decision = TurnDecision(action_kind="lesson", rationale="x")
        entry = TurnLogEntry.from_state_and_decision(
            0, state, decision, stop_reason="complete",
        )
        assert entry.stop_reason == "complete"


class TestJsonlTurnLogger:
    def test_appends_entries_one_per_line(self, tmp_path: Path) -> None:
        log_path = tmp_path / "turns.jsonl"
        logger = JsonlTurnLogger(log_path)
        state = GameState(season=1, week_remaining=10)
        decision = TurnDecision(action_kind="noop", rationale="t")
        logger.log(TurnLogEntry.from_state_and_decision(0, state, decision))
        logger.log(
            TurnLogEntry.from_state_and_decision(
                1, state, decision, stop_reason="max_turns",
            ),
        )
        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        first = json.loads(lines[0])
        assert first["turn_number"] == 0
        assert first["stop_reason"] is None
        second = json.loads(lines[1])
        assert second["turn_number"] == 1
        assert second["stop_reason"] == "max_turns"

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        log_path = tmp_path / "nested" / "deep" / "turns.jsonl"
        JsonlTurnLogger(log_path)
        assert log_path.parent.is_dir()


class _FakeStrategy:
    def __init__(self, decision: TurnDecision) -> None:
        self._d = decision

    def decide(self, state: GameState) -> TurnDecision:  # noqa: ARG002
        return self._d


class _FakeCapture:
    def __init__(self, color: tuple[int, int, int]) -> None:
        img = Image.new("RGB", (3024, 1610), color=(200, 200, 200))
        block = Image.new("RGB", (212, 80), color=color)
        img.paste(block, (2449, 1465))
        self.image = img

    def capture(self, region: Region) -> Image.Image:  # noqa: ARG002
        return self.image


class _FakePointer:
    def click_relative(
        self,
        region: object,
        relative: tuple[float, float],
        **_: object,
    ) -> None:
        pass

    def drag_relative(
        self,
        region: object,
        start: tuple[float, float],
        end: tuple[float, float],
        **_: object,
    ) -> None:
        pass


class TestEngineIntegration:
    HOME_COLOR = (163, 214, 136)

    def test_run_full_produce_writes_log_per_turn(self, tmp_path: Path) -> None:
        log_path = tmp_path / "turns.jsonl"
        turn_logger = JsonlTurnLogger(log_path)
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            strategy=_FakeStrategy(  # type: ignore[arg-type]
                TurnDecision(action_kind="rest", rationale="t"),
            ),
            capture=_FakeCapture(self.HOME_COLOR),  # type: ignore[arg-type]
            pointer=_FakePointer(),  # type: ignore[arg-type]
            turn_logger=turn_logger,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        result = engine.run_full_produce(
            max_turns=3,
            consume_poll_interval=0.0,
            require_fields=(),
            no_progress_threshold=0,
        )
        assert result == "max_turns"
        lines = log_path.read_text(encoding="utf-8").splitlines()
        # 3 ターン + 最終 max_turns エントリ = 4
        assert len(lines) == 4
        # 最後の行が stop_reason を持つ
        last = json.loads(lines[-1])
        assert last["stop_reason"] == "max_turns"
        # 中間 3 行は stop_reason=None
        for line in lines[:3]:
            entry = json.loads(line)
            assert entry["stop_reason"] is None
            assert entry["decision_action_kind"] == "rest"
