"""`JsonlTurnLogger` と `TurnLogEntry` のユニットテスト。"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from auto_emulator.games.produce import (
    GameState,
    JsonlTurnLogger,
    LessonOption,
    RunSummary,
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


class TestRunSummary:
    def _entry(
        self,
        turn: int,
        action: str,
        *,
        fans: int | None = None,
        season: int | None = None,
        stop: str | None = None,
    ) -> TurnLogEntry:
        state = GameState(season=season, fans_to_target=fans)
        decision = TurnDecision(action_kind=action, rationale="t")
        return TurnLogEntry.from_state_and_decision(
            turn, state, decision, stop_reason=stop,
        )

    def test_records_total_and_decision_counts(self) -> None:
        s = RunSummary()
        s.record(self._entry(0, "lesson"))
        s.record(self._entry(1, "lesson"))
        s.record(self._entry(2, "rest"))
        assert s.total_turns == 3
        assert s.decision_counts["lesson"] == 2
        assert s.decision_counts["rest"] == 1

    def test_tracks_fans_delta(self) -> None:
        s = RunSummary()
        s.record(self._entry(0, "lesson", fans=10000))
        s.record(self._entry(1, "lesson", fans=8000))
        s.record(self._entry(2, "lesson", fans=5000))
        assert s.first_fans_left == 10000
        assert s.last_fans_left == 5000
        assert s.fans_gained() == 5000

    def test_tracks_season_range(self) -> None:
        s = RunSummary()
        s.record(self._entry(0, "lesson", season=1))
        s.record(self._entry(1, "lesson", season=2))
        s.record(self._entry(2, "lesson", season=4))
        assert s.first_season == 1
        assert s.last_season == 4

    def test_captures_stop_reason(self) -> None:
        s = RunSummary()
        s.record(self._entry(0, "lesson"))
        s.record(self._entry(1, "lesson", stop="complete"))
        assert s.stop_reason == "complete"

    def test_format_report_includes_decisions_sorted_by_count(self) -> None:
        s = RunSummary()
        s.record(self._entry(0, "rest"))
        s.record(self._entry(1, "lesson"))
        s.record(self._entry(2, "lesson"))
        report = s.format_report()
        # decision の出力は降順なので lesson が rest より先に出る
        assert "lesson: 2" in report
        assert "rest: 1" in report
        assert report.index("lesson") < report.index("rest")
        assert "total turns: 3" in report

    def test_format_report_empty(self) -> None:
        s = RunSummary()
        report = s.format_report()
        # 空でもクラッシュせずヘッダと total が出る
        assert "total turns: 0" in report

    def test_from_jsonl_replays_entries(self, tmp_path: Path) -> None:
        log_path = tmp_path / "turns.jsonl"
        logger = JsonlTurnLogger(log_path)
        logger.log(self._entry(0, "lesson", fans=10000, season=1))
        logger.log(self._entry(1, "rest", fans=9500, season=1))
        logger.log(self._entry(2, "lesson", fans=8000, season=2, stop="complete"))
        summary = RunSummary.from_jsonl(log_path)
        assert summary.total_turns == 3
        assert summary.decision_counts["lesson"] == 2
        assert summary.decision_counts["rest"] == 1
        assert summary.first_fans_left == 10000
        assert summary.last_fans_left == 8000
        assert summary.fans_gained() == 2000
        assert summary.first_season == 1
        assert summary.last_season == 2
        assert summary.stop_reason == "complete"

    def test_from_jsonl_skips_blank_lines(self, tmp_path: Path) -> None:
        log_path = tmp_path / "turns.jsonl"
        logger = JsonlTurnLogger(log_path)
        logger.log(self._entry(0, "lesson"))
        # 末尾の改行や空行が混入してもパース可
        with log_path.open("a", encoding="utf-8") as f:
            f.write("\n  \n")
        logger.log(self._entry(1, "rest"))
        summary = RunSummary.from_jsonl(log_path)
        assert summary.total_turns == 2


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

    def test_run_full_produce_records_summary(self, tmp_path: Path) -> None:
        # D6: Engine に注入した RunSummary が自動的に集計される
        summary = RunSummary()
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            strategy=_FakeStrategy(  # type: ignore[arg-type]
                TurnDecision(action_kind="rest", rationale="t"),
            ),
            capture=_FakeCapture(self.HOME_COLOR),  # type: ignore[arg-type]
            pointer=_FakePointer(),  # type: ignore[arg-type]
            summary=summary,
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
        # 3 通常ターン + 1 max_turns エントリ = 4 record
        assert summary.total_turns == 4
        assert summary.decision_counts["rest"] == 4
        assert summary.stop_reason == "max_turns"
        assert "rest: 4" in summary.format_report()
        # tmp_path は将来の拡張のためのフィクスチャ、現テストでは未使用
        assert tmp_path.is_dir()
