"""プロデュース自走ループのターン別観測ログ。

`ProduceEngine.run_full_produce` の各ターンで state + decision を JSONL
形式で永続化する。長時間稼働後の分析、回帰検出、戦略チューニングの
入力データとして使う。
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from auto_emulator.games.produce.decision import TurnDecision
    from auto_emulator.games.produce.state import GameState


class TurnLogEntry(BaseModel):
    """1 ターン分の観測+決定の永続化形式。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: str = Field(description="ISO 8601 UTC")
    turn_number: int = Field(ge=0)
    season: int | None = None
    week_remaining: int | None = None
    fans_to_target: int | None = None
    hp_pct: float | None = None
    trouble_pct: int | None = None
    tension_lv: int | None = None
    stats: dict[str, int] | None = None
    decision_action_kind: str
    decision_target_slot: int
    decision_rationale: str
    stop_reason: str | None = Field(
        default=None,
        description="最終エントリの場合の停止理由 (例: complete, stuck:home)",
    )

    @classmethod
    def from_state_and_decision(
        cls,
        turn_number: int,
        state: GameState,
        decision: TurnDecision,
        *,
        stop_reason: str | None = None,
    ) -> TurnLogEntry:
        return cls(
            timestamp=datetime.now(tz=UTC).isoformat(),
            turn_number=turn_number,
            season=state.season,
            week_remaining=state.week_remaining,
            fans_to_target=state.fans_to_target,
            hp_pct=state.hp_pct,
            trouble_pct=state.trouble_pct,
            tension_lv=state.tension_lv,
            stats=state.stats,
            decision_action_kind=decision.action_kind,
            decision_target_slot=decision.target_slot,
            decision_rationale=decision.rationale,
            stop_reason=stop_reason,
        )


class JsonlTurnLogger:
    """ターン毎の `TurnLogEntry` を JSONL に追記する軽量ロガー。

    1 行 = 1 JSON エントリ。書き込みは追記のみで、長時間稼働でも
    途中までのログが残る (途中クラッシュ時の障害解析に有用)。
    """

    def __init__(self, path: Path) -> None:
        """Constructor.

        Args:
            path: 書き込み先 JSONL ファイル。親ディレクトリが無ければ作成。
        """
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def log(self, entry: TurnLogEntry) -> None:
        """1 エントリを 1 行として追記する。"""
        with self._path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")


@dataclass
class RunSummary:
    """In-memory run 集計: ターン数 / decision 分布 / fans 推移などを追跡。

    `ProduceEngine.run_full_produce` 実行中に `record()` で 1 ターン
    ずつフィードし、終了時に `format_report()` で人間可読サマリを得る。
    既存 JSONL ファイルから集計するには `from_jsonl()` を使う。
    """

    total_turns: int = 0
    decision_counts: Counter[str] = field(default_factory=Counter)
    stop_reason: str | None = None
    first_fans_left: int | None = None
    last_fans_left: int | None = None
    first_season: int | None = None
    last_season: int | None = None

    def record(self, entry: TurnLogEntry) -> None:
        """1 エントリ分の集計を反映する。"""
        self.decision_counts[entry.decision_action_kind] += 1
        self.total_turns += 1
        if entry.fans_to_target is not None:
            if self.first_fans_left is None:
                self.first_fans_left = entry.fans_to_target
            self.last_fans_left = entry.fans_to_target
        if entry.season is not None:
            if self.first_season is None:
                self.first_season = entry.season
            self.last_season = entry.season
        if entry.stop_reason is not None:
            self.stop_reason = entry.stop_reason

    def fans_gained(self) -> int | None:
        """初観測〜最終観測のファン獲得数 (目標までの残数の減少)。

        Returns:
            `first_fans_left - last_fans_left`、観測が無ければ None。
        """
        if self.first_fans_left is None or self.last_fans_left is None:
            return None
        return self.first_fans_left - self.last_fans_left

    def format_report(self) -> str:
        """人間可読のサマリ文字列を返す (CLI 表示用)。

        Returns:
            複数行のサマリ文字列。
        """
        lines = ["=== Produce Run Summary ==="]
        lines.append(f"total turns: {self.total_turns}")
        if self.stop_reason is not None:
            lines.append(f"stop reason: {self.stop_reason}")
        if self.first_season is not None or self.last_season is not None:
            lines.append(
                f"season: {self.first_season} -> {self.last_season}",
            )
        gained = self.fans_gained()
        if gained is not None:
            lines.append(
                f"fans_to_target: {self.first_fans_left} -> "
                f"{self.last_fans_left} (delta={gained:+d})",
            )
        if self.decision_counts:
            lines.append("decisions:")
            for kind, count in sorted(
                self.decision_counts.items(),
                key=lambda kv: (-kv[1], kv[0]),
            ):
                lines.append(f"  {kind}: {count}")
        return "\n".join(lines)

    @classmethod
    def from_jsonl(cls, path: Path) -> RunSummary:
        """JSONL ファイルを読んで集計を組み立てる (D7 analyze 用)。

        Args:
            path: JSONL ログファイル。

        Returns:
            集計済み `RunSummary`。
        """
        summary = cls()
        with path.open(encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                data = json.loads(line)
                entry = TurnLogEntry.model_validate(data)
                summary.record(entry)
        return summary
