r"""TI2: 回帰用 snapshot テスト。

座標定義と `RunSummary.format_report()` の出力契約が意図せず変わって
いないかをスナップショットで検出する。

- `regions.json`: `tools/calibrate_produce.py dump-regions` の出力。
   座標が誤って変更されると失敗する。
- `RunSummary.format_report()`: CLI で表示される文字列の構造が
   崩れていないかを文字列比較で検出する。

スナップショットを意図的に更新したい場合 (機能追加で構造が変わった等)、
次の手順で再生成する:

    .venv/bin/python tools/calibrate_produce.py dump-regions \\
        --out tests/fixtures/produce/snapshots/regions.json

それと一緒に PR でレビュアが座標変更を確認できる。
"""

from __future__ import annotations

import json
from pathlib import Path

from auto_emulator.games.produce import (
    GameState,
    RunSummary,
    TurnDecision,
    TurnLogEntry,
)
from tools.calibrate_produce import collect_region_dump

SNAPSHOT_DIR = Path(__file__).resolve().parent / "fixtures" / "produce" / "snapshots"
REGIONS_GOLDEN = SNAPSHOT_DIR / "regions.json"


class TestRegionsSnapshot:
    def test_dump_regions_matches_golden(self) -> None:
        # 座標定義が意図せず変わっていないか
        current = collect_region_dump()
        golden = json.loads(REGIONS_GOLDEN.read_text(encoding="utf-8"))
        assert current == golden, (
            "座標スナップショットがズレています。意図的な変更なら "
            "`python tools/calibrate_produce.py dump-regions --out "
            "tests/fixtures/produce/snapshots/regions.json` で更新してください。"
        )

    def test_golden_has_expected_structure(self) -> None:
        # スナップショット自体が想定構造を保っていることをルートレベルで再確認
        golden = json.loads(REGIONS_GOLDEN.read_text(encoding="utf-8"))
        assert set(golden.keys()) == {"regions", "points"}
        assert set(golden["regions"].keys()) == {
            "header",
            "stats",
            "status",
            "lessons",
            "auditions",
        }
        assert set(golden["points"].keys()) == {
            "home",
            "schedule",
            "audition_battle",
            "dialog",
            "modal_dismiss",
            "item",
        }


class TestRunSummaryReportFormat:
    """`format_report()` の出力契約スナップショット.

    CLI 表示や `produce-analyze` のテキスト出力が依存する形式なので、
    変更はインターフェイス変更とみなす。
    """

    def _build(self) -> RunSummary:
        summary = RunSummary()
        for turn, action, fans, season, stop in [
            (0, "lesson", 10000, 1, None),
            (1, "lesson", 9500, 1, None),
            (2, "rest", 9000, 2, None),
            (3, "audition", 0, 2, "complete"),
        ]:
            state = GameState(season=season, fans_to_target=fans)
            decision = TurnDecision(action_kind=action, rationale="t")
            summary.record(
                TurnLogEntry.from_state_and_decision(
                    turn,
                    state,
                    decision,
                    stop_reason=stop,
                ),
            )
        return summary

    def test_format_report_layout(self) -> None:
        report = self._build().format_report()
        expected_lines = [
            "=== Produce Run Summary ===",
            "total turns: 4",
            "stop reason: complete",
            "season: 1 -> 2",
            "fans_to_target: 10000 -> 0 (delta=+10000)",
            "decisions:",
            "  lesson: 2",
            "  audition: 1",
            "  rest: 1",
        ]
        assert report == "\n".join(expected_lines)

    def test_empty_summary_report(self) -> None:
        # 何も record しない状態の最小出力
        summary = RunSummary()
        report = summary.format_report()
        assert report == "=== Produce Run Summary ===\ntotal turns: 0"
