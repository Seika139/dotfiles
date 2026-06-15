"""`auto-emulator produce-run` / `produce-analyze` CLI のテスト。

実機キャリブが必要な正常系は単体テストでは扱わず、template ディレクトリ
未存在等のエラー終了経路と `produce-analyze` の集計表示を検証する。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from typer.testing import CliRunner

from auto_emulator.cli import _default_produce_log_path, app  # noqa: PLC2701
from auto_emulator.games.produce import (
    GameState,
    JsonlTurnLogger,
    TurnDecision,
    TurnLogEntry,
)

runner = CliRunner()


def test_command_registered() -> None:
    result = runner.invoke(app, ["produce-run", "--help"])
    assert result.exit_code == 0
    assert "produce" in result.stdout.lower()


def test_missing_templates_dir_exits_with_error(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_dir"
    result = runner.invoke(
        app,
        ["produce-run", "--templates-dir", str(missing), "--no-calibrate"],
    )
    assert result.exit_code == 1
    assert "テンプレディレクトリが見つかりません" in result.stdout


def test_empty_templates_dir_exits_with_error(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = runner.invoke(
        app,
        ["produce-run", "--templates-dir", str(empty), "--no-calibrate"],
    )
    assert result.exit_code == 1
    assert "1 件もロードできませんでした" in result.stdout


class TestDefaultLogPath:
    def test_includes_timestamp_in_filename(self) -> None:
        fixed = datetime(2026, 5, 15, 9, 30, 0).astimezone()
        path = _default_produce_log_path(now=fixed)
        assert path.name == "produce-20260515-0930.jsonl"

    def test_lives_under_cache_dir(self) -> None:
        path = _default_produce_log_path()
        assert ".cache" in path.parts
        assert "auto-emulator" in path.parts


class TestProduceAnalyze:
    def _write_sample_log(self, path: Path) -> None:
        logger = JsonlTurnLogger(path)
        for turn, action, fans, stop in [
            (0, "lesson", 10000, None),
            (1, "lesson", 9000, None),
            (2, "rest", 8500, None),
            (3, "lesson", 7000, "complete"),
        ]:
            state = GameState(season=2, fans_to_target=fans)
            decision = TurnDecision(action_kind=action, rationale="t")
            logger.log(
                TurnLogEntry.from_state_and_decision(
                    turn,
                    state,
                    decision,
                    stop_reason=stop,
                ),
            )

    def test_summarizes_existing_jsonl(self, tmp_path: Path) -> None:
        log_path = tmp_path / "run.jsonl"
        self._write_sample_log(log_path)
        result = runner.invoke(app, ["produce-analyze", str(log_path)])
        assert result.exit_code == 0
        assert "total turns: 4" in result.stdout
        assert "lesson: 3" in result.stdout
        assert "rest: 1" in result.stdout
        assert "complete" in result.stdout
        assert "delta=+3000" in result.stdout

    def test_missing_file_returns_error(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["produce-analyze", str(tmp_path / "no_such.jsonl")],
        )
        assert result.exit_code == 1
        assert "見つかりません" in result.stdout

    def test_invalid_json_returns_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.jsonl"
        bad.write_text("not json at all\n", encoding="utf-8")
        result = runner.invoke(app, ["produce-analyze", str(bad)])
        assert result.exit_code == 1
        assert "ログ解析に失敗" in result.stdout

    def test_help_is_available(self) -> None:
        result = runner.invoke(app, ["produce-analyze", "--help"])
        assert result.exit_code == 0
        # tmp_path 由来でなく純粋な help 起動
        assert "JSONL" in result.stdout or "ログ" in result.stdout
        # json は import を確認するために参照
        assert json.dumps({"k": 1}) == '{"k": 1}'
