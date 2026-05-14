"""TI1: プロデュース自走の E2E シミュレータテスト。

実機を触らず、`FakeCapture` の image queue を実際の状態遷移
(home → schedule → battle → home → ...) に沿って組み上げ、
`run_full_produce` が完走する代表シナリオを 1 ループ流す。

ターン単位の細かい挙動は `test_produce_engine.py` で検証済みなので、
ここは「画面遷移の連結が成立する」「最終的に意図した停止理由に到達する」
「`RunSummary` が想定値になる」のフロー検証に焦点を当てる。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from auto_emulator.games.produce import (
    GameState,
    RunSummary,
    TurnDecision,
)
from auto_emulator.games.produce.engine import ProduceEngine
from mouse_core import Region


@dataclass
class _ScriptedCapture:
    """事前に決めたシーケンスで画面を返す capture フェイク。

    `script` が空になったら `default` を繰り返し返す。これで「ホーム
    検出 → 中間消化 → ホーム再到達」のような有限プレフィックス +
    無限テールパターンを表現できる。
    """

    script: list[Image.Image] = field(default_factory=list)
    default: Image.Image | None = None

    def capture(self, region: Region) -> Image.Image:  # noqa: ARG002
        if self.script:
            return self.script.pop(0)
        if self.default is not None:
            return self.default
        raise AssertionError("script exhausted and no default provided")


@dataclass
class _NoopPointer:
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
class _FakeStrategy:
    """常に同じ decision を返すスタブ戦略。"""

    fixed: TurnDecision

    def decide(self, state: GameState) -> TurnDecision:  # noqa: ARG002
        return self.fixed


def _br_image(color: tuple[int, int, int]) -> Image.Image:
    """右下に signature 色を塗った 3024x1610 画像を返す.

    Returns:
        ベースが灰色で右下 (2449, 1465) に 212x80 の `color` ブロックを
        貼った PIL Image。`detect_screen_kind` がこの右下色を見るので、
        画面種別シミュレーションに使う。
    """
    img = Image.new("RGB", (3024, 1610), color=(200, 200, 200))
    block = Image.new("RGB", (212, 80), color=color)
    img.paste(block, (2449, 1465))
    return img


# 既存テストと整合する画面 signature 色
HOME = _br_image((163, 214, 136))
SCHEDULE = _br_image((220, 149, 191))
UNKNOWN = Image.new("RGB", (3024, 1610), color=(180, 195, 220))


class TestE2EFlowOneLoop:
    """ホーム検出 → 1 ターン消化 → max_turns で停止のフロー検証。"""

    def _build(self) -> tuple[ProduceEngine, _NoopPointer, RunSummary]:
        pointer = _NoopPointer()
        summary = RunSummary()
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            strategy=_FakeStrategy(  # type: ignore[arg-type]
                TurnDecision(action_kind="rest", rationale="t"),
            ),
            capture=_ScriptedCapture(default=HOME),  # type: ignore[arg-type]
            pointer=pointer,  # type: ignore[arg-type]
            summary=summary,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        return engine, pointer, summary

    def test_max_turns_records_summary(self) -> None:
        engine, pointer, summary = self._build()
        result = engine.run_full_produce(
            max_turns=3,
            consume_poll_interval=0.0,
            require_fields=(),
            no_progress_threshold=0,
        )
        assert result == "max_turns"
        # 通常 3 ターン + 1 max_turns エントリ = 4 record
        assert summary.total_turns == 4
        assert summary.decision_counts["rest"] == 4
        assert summary.stop_reason == "max_turns"
        # 各ターンで rest_card + rest_confirm = 2 クリック (3 ターン分 = 6)
        assert len(pointer.clicks) == 6


class TestE2EFlowConsumeIntermediate:
    """中間 unknown 画面を 2 回経由してホームに辿り着くシナリオ.

    旧 sample2.yml の「3 ステップ消化してホーム再到達」を Engine 単独で
    再現できることを示す。
    """

    def test_intermediate_unknowns_then_home(self) -> None:
        # 序盤: 中間画面 2 回 → ホーム検出 → 戦略実行 → max_turns で停止
        capture = _ScriptedCapture(
            script=[UNKNOWN, UNKNOWN, HOME],
            default=HOME,
        )
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            strategy=_FakeStrategy(  # type: ignore[arg-type]
                TurnDecision(action_kind="rest", rationale="t"),
            ),
            capture=capture,  # type: ignore[arg-type]
            pointer=_NoopPointer(),  # type: ignore[arg-type]
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        result = engine.run_full_produce(
            max_turns=2,
            consume_poll_interval=0.0,
            require_fields=(),
            no_progress_threshold=0,
        )
        # 中間消化を経て max_turns に到達できる (stuck:home に落ちない)
        assert result == "max_turns"


class TestE2EFlowFanCompletion:
    """fans_to_target が 0 を観測したら complete で停止することを E2E で検証。"""

    def test_fans_zero_triggers_complete(self) -> None:
        # 1 ターン目で fans=1000、2 ターン目で fans=0 を観測する reader
        from auto_emulator.games.produce.reader import (  # noqa: PLC0415
            ProduceStateReader,
        )

        class _DecreasingFansReader(ProduceStateReader):
            def __init__(self) -> None:
                super().__init__()
                self._fans_queue = [1000, 1000, 0]

            def read(self, image: Image.Image) -> GameState:  # noqa: ARG002
                fans = (
                    self._fans_queue.pop(0)
                    if self._fans_queue
                    else 0
                )
                return GameState(
                    season=4,
                    week_remaining=1,
                    fans_to_target=fans,
                    stats={"Vo": 800},
                )

            def lessons_from_schedule(
                self,
                image: Image.Image,  # noqa: ARG002
            ) -> list:
                return []

        summary = RunSummary()
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            reader=_DecreasingFansReader(),
            strategy=_FakeStrategy(  # type: ignore[arg-type]
                TurnDecision(action_kind="rest", rationale="t"),
            ),
            capture=_ScriptedCapture(default=HOME),  # type: ignore[arg-type]
            pointer=_NoopPointer(),  # type: ignore[arg-type]
            summary=summary,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        result = engine.run_full_produce(
            max_turns=10,
            consume_poll_interval=0.0,
            require_fields=(),
            no_progress_threshold=0,
        )
        assert result == "complete"
        # complete エントリで stop_reason=complete が記録される
        assert summary.stop_reason == "complete"
        # 1 ターン目 fans=1000、2 ターン目 fans=0 を観測
        assert summary.first_fans_left == 1000
        assert summary.last_fans_left == 0
        assert summary.fans_gained() == 1000


class TestE2EFlowScheduleStuck:
    """ホームから schedule に遷移できない場合 stuck:schedule を返すパス。"""

    def test_no_schedule_after_produce_card(self) -> None:
        # 常にホームを返す → produce card 押しても schedule に行かない
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            strategy=_FakeStrategy(  # type: ignore[arg-type]
                TurnDecision(action_kind="lesson", target_slot=0, rationale="t"),
            ),
            capture=_ScriptedCapture(default=HOME),  # type: ignore[arg-type]
            pointer=_NoopPointer(),  # type: ignore[arg-type]
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        result = engine.run_full_produce(
            max_turns=2,
            schedule_timeout=0.05,
            consume_poll_interval=0.0,
            require_fields=(),
            no_progress_threshold=0,
        )
        assert result == "stuck:schedule"
