"""プロデュースモードのオーケストレータ。

`capture → read → decide → execute` の 1 ループを `step()` が担う。
`dodge.DodgeEngine` と同じく `Region` ベースの fractional 座標で
画面解像度に依存しない設計とし、シナリオ層はここを呼び出すだけ。

Phase 5a: スケジュール選択画面でのレッスン選択と決定までを実装。
        オーディションスワイプ・休む・振り返りは stub (ログのみ)。
        ホーム画面遷移とダイアログ処理は YAML 側 (sample2.yml) に任せる。
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from PIL import Image

from auto_emulator.games.produce.actions import (
    AUDITION_BATTLE_POINTS,
    DIALOG_POINTS,
    HOME_POINTS,
    SCHEDULE_POINTS,
    AuditionBattlePoints,
    DialogPoints,
    HomeActionPoints,
    Point,
    ScheduleActionPoints,
    audition_swipe_path,
)
from auto_emulator.games.produce.decision import StrategyEngine, TurnDecision
from auto_emulator.games.produce.reader import ProduceStateReader
from auto_emulator.games.produce.state import GameState
from auto_emulator.runtime.termination import TerminationMonitor
from auto_emulator.services.capture import MSSScreenCaptureService, ScreenCaptureService
from mouse_core import PointerController, Region


@dataclass(frozen=True)
class ProduceActionPoints:
    """Engine が参照する画面別ポイントセット。差し替えで挙動を変えられる。"""

    home: HomeActionPoints = HOME_POINTS
    schedule: ScheduleActionPoints = SCHEDULE_POINTS
    audition_battle: AuditionBattlePoints = AUDITION_BATTLE_POINTS
    dialog: DialogPoints = DIALOG_POINTS


class ProduceEngine:
    """1 ターン単位で state 読み取り→決定→実行を行うオーケストレータ。"""

    def __init__(  # noqa: PLR0913
        self,
        region: Region,
        *,
        reader: ProduceStateReader | None = None,
        strategy: StrategyEngine | None = None,
        capture: ScreenCaptureService | None = None,
        pointer: PointerController | None = None,
        action_points: ProduceActionPoints | None = None,
        logger: Callable[[str], None] | None = None,
        click_settle: float = 0.4,
        loop_interval: float = 1.5,
    ) -> None:
        self._region = region
        self._reader = reader or ProduceStateReader()
        self._strategy = strategy or StrategyEngine()
        self._capture = capture or MSSScreenCaptureService()
        self._pointer = pointer or PointerController()
        self._points = action_points or ProduceActionPoints()
        self._log = logger or (lambda msg: print(msg, flush=True))
        self._click_settle = click_settle
        self._loop_interval = loop_interval

    def capture_state(self) -> tuple[Image.Image, GameState]:
        """画面をキャプチャし、レッスン情報まで含めた `GameState` を返す。

        Returns:
            (撮影フレーム, 抽出された `GameState`) のタプル。
        """
        frame = self._capture.capture(region=self._region)
        state = self._reader.read(frame)
        lessons = self._reader.lessons_from_schedule(frame)
        return frame, state.model_copy(update={"lessons": lessons})

    def step(self) -> tuple[GameState, TurnDecision]:
        """1 ターン進める。state を読んで decide → execute_decision を行う。

        Returns:
            観測した `GameState` と適用した `TurnDecision` のペア。
        """
        _, state = self.capture_state()
        decision = self._strategy.decide(state)
        self._log(
            f"[produce] turn season={state.season} week={state.week_remaining} "
            f"fans_left={state.fans_to_target} -> {decision.action_kind} "
            f"slot={decision.target_slot} ({decision.rationale})",
        )
        self.execute_decision(decision)
        return state, decision

    def run(
        self,
        stop_monitor: TerminationMonitor | None = None,
        max_turns: int | None = None,
    ) -> int:
        """指定ターン数 (または停止指示まで) `step` を繰り返す。

        Returns:
            実行したターン数。
        """
        executed = 0
        limit = max_turns if max_turns is not None else 1_000_000
        while executed < limit:
            if stop_monitor and stop_monitor.stop_requested():
                break
            if stop_monitor:
                stop_monitor.wait_if_paused()
            self.step()
            executed += 1
            time.sleep(self._loop_interval)
        return executed

    def execute_decision(self, decision: TurnDecision) -> None:
        """`TurnDecision` をクリック列に変換して発行する。

        スケジュール画面想定のクリックのみ実装済み。それ以外はログ出力のみ。
        """
        kind = decision.action_kind
        if kind == "lesson":
            self._tap_lesson_slot(decision.target_slot)
            self._sleep_settle()
            self._tap(self._points.schedule.confirm_button)
            return
        if kind == "audition":
            self._tap(self._points.schedule.audition_tab)
            self._sleep_settle()
            for _ in range(decision.target_slot):
                self._swipe_audition_next()
                self._sleep_settle()
            self._tap(self._points.schedule.confirm_button)
            return
        if kind == "rest":
            self._execute_rest()
            return
        if kind == "reflection":
            self._execute_reflection()
            return
        if kind in {"item", "noop"}:
            self._log(f"[produce] {kind} action not yet implemented")
            return
        self._log(f"[produce] unknown action_kind={kind!r}; skipping")

    def _execute_rest(self) -> None:
        """ホーム画面想定: 休むカード → 確認ダイアログ OK。

        スケジュール画面から呼ばれた場合は事前に back ボタンを押して
        ホームへ戻る必要があるが、Phase 5b では呼び出し側が screen 状態を
        管理する想定とし、ここでは home 起点の操作のみ発行する。
        """
        self._tap(self._points.home.rest_card)
        self._sleep_settle()
        self._tap(self._points.home.rest_confirm)

    def _execute_reflection(self) -> None:
        """ホーム画面想定: 振り返りカードを押す。スキルパネル操作は Phase 5c。"""
        self._tap(self._points.home.reflection_card)
        # スキル取得・パッシブ ON はサブシーンで人手 or テンプレ判定が必要

    def enable_dialog_fast_forward(self) -> None:
        """会話パートで早送り x4 トグルを ON にする (M2 / M14)。

        既に ON の場合に押すと OFF になるため、呼び出し側は状態を把握すること。
        """
        self._tap(self._points.dialog.fast_forward_toggle)

    def tap_dialog_yellow_choice(self) -> None:
        """3 択ダイアログで黄色の選択肢をタップする (M11/M16)。

        `sample2.yml` 既存ルールに合わせる。文脈非依存の default 戦略で、
        テンション低下を許容する。
        """
        self._tap(self._points.dialog.choice_yellow)

    def enable_battle_auto(self) -> None:
        """オーディション戦闘で AUTO ON + 倍速 ON を順に押す (M3)。"""
        self._tap(self._points.audition_battle.auto_toggle)
        self._sleep_settle()
        self._tap(self._points.audition_battle.speed_toggle)

    def _tap(self, point: Point) -> None:
        self._pointer.click_relative(self._region, (point.x, point.y))

    def _tap_lesson_slot(self, slot: int) -> None:
        regions = self._reader.lesson_regions
        if slot < 0 or slot >= len(regions.card_centers_x):
            self._log(f"[produce] invalid lesson slot {slot}; falling back to 0")
            slot = 0
        cx = regions.card_centers_x[slot]
        cy = sum(regions.name_band) / 2  # カードの縦中央
        self._pointer.click_relative(self._region, (cx, cy))

    def _swipe_audition_next(self) -> None:
        start, end = audition_swipe_path()
        start_center = (start.x + start.w / 2, start.y + start.h / 2)
        end_center = (end.x + end.w / 2, end.y + end.h / 2)
        self._pointer.drag_relative(self._region, start_center, end_center)

    def _sleep_settle(self) -> None:
        time.sleep(self._click_settle)
