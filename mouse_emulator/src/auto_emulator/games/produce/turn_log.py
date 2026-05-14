"""プロデュース自走ループのターン別観測ログ。

`ProduceEngine.run_full_produce` の各ターンで state + decision を JSONL
形式で永続化する。長時間稼働後の分析、回帰検出、戦略チューニングの
入力データとして使う。
"""

from __future__ import annotations

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
