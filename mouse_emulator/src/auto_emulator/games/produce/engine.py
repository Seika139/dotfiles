"""プロデュースモードのオーケストレータ。

`capture → read → decide → execute` の 1 ループを `step()` が担う。
`dodge.DodgeEngine` と同じく `Region` ベースの fractional 座標で
画面解像度に依存しない設計とし、シナリオ層はここを呼び出すだけ。

`run_full_produce` は home / schedule_lesson のどちらを起点にしても
自走できる。home 起点なら produce_card で schedule へ遷移し、schedule
起点ならそのターンの遷移をスキップして直接レッスン/オーディションを
実行する (E1 で yml ベース経路を廃止し Engine 一本化)。
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
    ITEM_POINTS,
    MODAL_DISMISS_POINTS,
    SCHEDULE_POINTS,
    AuditionBattlePoints,
    DialogPoints,
    HomeActionPoints,
    ItemActionPoints,
    ModalDismissPoints,
    Point,
    ScheduleActionPoints,
    audition_swipe_path,
    modal_dismiss_sequence,
)
from auto_emulator.games.produce.decision import StrategyEngine, TurnDecision
from auto_emulator.games.produce.reader import ProduceStateReader
from auto_emulator.games.produce.state import GameState, ScreenKind
from auto_emulator.games.produce.turn_log import (
    JsonlTurnLogger,
    RunSummary,
    TurnLogEntry,
)
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
    modal_dismiss: ModalDismissPoints = MODAL_DISMISS_POINTS
    item: ItemActionPoints = ITEM_POINTS


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
        turn_logger: JsonlTurnLogger | None = None,
        summary: RunSummary | None = None,
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
        self._turn_logger = turn_logger
        self._summary = summary
        self._click_settle = click_settle
        self._loop_interval = loop_interval

    @property
    def summary(self) -> RunSummary | None:
        """Engine に紐付いた `RunSummary` (D6) を返す。未指定なら None。"""
        return self._summary

    def detect_screen(self) -> ScreenKind:
        """現在の画面種別を 1 ショットで判定する。

        Returns:
            画面種別 (識別不能なら `"unknown"`)。
        """
        frame = self._capture.capture(region=self._region)
        return ProduceStateReader.detect_screen_kind(frame)

    def wait_for_screen(
        self,
        target: ScreenKind | set[ScreenKind],
        *,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
    ) -> ScreenKind | None:
        """指定画面のいずれかが現れるまで定期キャプチャで待つ。

        Args:
            target: 待ち受ける画面種別。単一でも集合でも可。
            timeout: 全体タイムアウト (秒)。
            poll_interval: 1 ポーリング間隔 (秒)。

        Returns:
            最初に観測された画面種別。timeout 超過時は `None`。
        """
        targets: set[ScreenKind] = (
            {target} if isinstance(target, str) else set(target)
        )
        deadline = time.monotonic() + timeout
        while True:
            kind = self.detect_screen()
            if kind in targets:
                return kind
            if time.monotonic() >= deadline:
                self._log(
                    f"[produce] wait_for_screen timeout: wanted={targets} "
                    f"last_seen={kind!r}",
                )
                return None
            time.sleep(poll_interval)

    def capture_state(self) -> tuple[Image.Image, GameState]:
        """画面をキャプチャし、レッスン情報まで含めた `GameState` を返す。

        Returns:
            (撮影フレーム, 抽出された `GameState`) のタプル。
        """
        frame = self._capture.capture(region=self._region)
        state = self._reader.read(frame)
        lessons = self._reader.lessons_from_schedule(frame)
        preview_fans = self._reader.read_selected_lesson_preview_fans(frame)
        return frame, state.model_copy(
            update={
                "lessons": lessons,
                "selected_lesson_preview_fans": preview_fans,
            },
        )

    def read_state_with_retry(
        self,
        *,
        require_fields: tuple[str, ...] = ("season",),
        max_attempts: int = 3,
        poll_interval: float = 0.3,
    ) -> GameState | None:
        """重要フィールドが揃うまで `capture_state` をリトライする。

        OCR が失敗してフィールドが None になるターンは捨て、ジターを置いて
        再撮影する。`max_attempts` 回試して揃わなければ `None`。

        Args:
            require_fields: 必須フィールド名のタプル (例: ("season",))。
            max_attempts: 試行回数。
            poll_interval: 各試行の間で待つ秒数。

        Returns:
            重要フィールドが揃った `GameState`、または `None`。
        """
        last_state: GameState | None = None
        for attempt in range(max_attempts):
            _, state = self.capture_state()
            last_state = state
            if all(getattr(state, name) is not None for name in require_fields):
                return state
            self._log(
                f"[produce] state OCR retry {attempt + 1}/{max_attempts}: "
                f"missing fields among {require_fields}",
            )
            if attempt + 1 < max_attempts:
                time.sleep(poll_interval)
        self._log(
            f"[produce] state OCR gave up after {max_attempts} attempts; "
            f"last_state season={last_state.season if last_state else None}",
        )
        return None

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
            self._swipe_to_target_audition(
                target_name=decision.target_audition_name,
                max_swipes=decision.target_slot,
            )
            self._tap(self._points.schedule.confirm_button)
            return
        if kind == "rest":
            self._execute_rest()
            return
        if kind == "reflection":
            self._execute_reflection()
            return
        if kind == "item":
            self._execute_item()
            return
        if kind == "noop":
            self._log("[produce] noop")
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

    def _execute_item(self) -> None:
        """ホーム画面想定: アイテムタブ → 最初のスロット → 使用 → 閉じる。

        旧 `sample2.yml` の 3 ステップ (選択 / 使用 / 閉じる) を等価実装。
        スロット選択は左上 (`first_slot`) 固定で、最初の手持ちアイテム
        (スタミナ回復ドリンク等) を使う想定。将来複数アイテム選択や
        在庫確認を入れる場合はここを拡張する。
        """
        self._tap(self._points.home.item_tab)
        self._sleep_settle()
        self._tap(self._points.item.first_slot)
        self._sleep_settle()
        self._tap(self._points.item.use_button)
        self._sleep_settle()
        self._tap(self._points.item.close_button)

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

    def tap_dialog_green_choice(self) -> None:
        """3 択ダイアログで緑色 (中央、「いいよ」等) の選択肢をタップする。"""
        self._tap(self._points.dialog.choice_green)

    def tap_dialog_pink_choice(self) -> None:
        """3 択ダイアログで桃色 (左) の選択肢をタップする。"""
        self._tap(self._points.dialog.choice_pink)

    def tap_dialog_checkmark_fallback(self) -> None:
        """3 択が表示されず単一カードに ✓ が付いているときの確定タップ.

        旧 `sample2.yml` の "3つの選択肢が検知できなかった時のためのチェック
        マーク検出" ステップ相当。色判定ベースの `tap_dialog_*_choice` で
        進まないシーン (例: 強制シナリオで 1 択しか出ないケース) で使う
        フォールバック。座標は `DialogPoints.checkmark_choice` を参照する。
        """
        self._tap(self._points.dialog.checkmark_choice)

    def tap_dialog_choice_by_index(self, index: int) -> None:
        """0=桃(左) / 1=緑(中央) / 2=黄(右) でインデックス指定タップ.

        `choose_dialog_option` の戻り値とそのまま組み合わせて使える。
        想定外の index はクランプして安全側 (黄=末尾) に倒す。
        """
        if index <= 0:
            self.tap_dialog_pink_choice()
        elif index == 1:
            self.tap_dialog_green_choice()
        else:
            self.tap_dialog_yellow_choice()

    def run_full_produce(  # noqa: PLR0913
        self,
        *,
        max_turns: int = 200,
        schedule_timeout: float = 12.0,
        consume_max_taps: int = 30,
        consume_poll_interval: float = 0.5,
        ocr_retry_attempts: int = 3,
        ocr_retry_interval: float = 0.3,
        require_fields: tuple[str, ...] = ("season",),
        no_progress_threshold: int = 3,
        stop_monitor: TerminationMonitor | None = None,
    ) -> str:
        """ホーム検出 → step → 結果消化 を繰り返し、True End or 上限で停止する。

        Args:
            max_turns: 上限ターン数。
            schedule_timeout: プロデュースカード後にスケジュール画面が
                出現するまでの最大待ち時間 (秒)。
            consume_max_taps: 中間画面消化の最大タップ回数。
            consume_poll_interval: 中間画面消化時のポーリング間隔 (秒)。
            ocr_retry_attempts: 状態 OCR のリトライ回数。
            ocr_retry_interval: OCR リトライの間で待つ秒数。
            require_fields: 状態に必須のフィールド名 (B1)。
            no_progress_threshold: 同じ (season, week, fans) が連続出現したら
                クリック空振りとみなして停止する閾値 (B2)。0 以下で無効化。
            stop_monitor: 外部停止/一時停止を伝えるモニタ。

        Returns:
            停止理由:
                "complete": ファン目標到達 (fans_to_target=0 を観測)
                "max_turns": ターン上限到達
                "stuck:home": 中間画面消化に失敗
                "stuck:schedule": プロデュースカード後にスケジュール未到達
                "stuck:ocr": 状態 OCR が連続失敗
                "stuck:no_progress": ターン進行が連続観測されない
                "stopped": stop_monitor からの停止要求
        """
        last_signature: tuple[int | None, int | None, int | None] | None = None
        no_progress_streak = 0
        turn_index = 0
        last_state: GameState | None = None
        last_decision: TurnDecision | None = None
        for _ in range(max_turns):
            if stop_monitor and stop_monitor.stop_requested():
                self._log_turn(turn_index, last_state, last_decision, "stopped")
                return "stopped"
            ready = self._reach_ready_screen(
                max_taps=consume_max_taps,
                poll_interval=consume_poll_interval,
            )
            if ready is None:
                self._log_turn(
                    turn_index, last_state, last_decision, "stuck:home",
                )
                return "stuck:home"
            on_schedule = ready == "schedule"
            state = self.read_state_with_retry(
                require_fields=require_fields,
                max_attempts=ocr_retry_attempts,
                poll_interval=ocr_retry_interval,
            )
            if state is None:
                self._log_turn(turn_index, last_state, last_decision, "stuck:ocr")
                return "stuck:ocr"
            signature = (state.season, state.week_remaining, state.fans_to_target)
            if no_progress_threshold > 0 and last_signature is not None:
                if signature == last_signature:
                    no_progress_streak += 1
                    if no_progress_streak >= no_progress_threshold:
                        self._log(
                            f"[produce] no progress for {no_progress_streak} "
                            f"consecutive turns; signature={signature}",
                        )
                        self._log_turn(
                            turn_index, state, last_decision, "stuck:no_progress",
                        )
                        return "stuck:no_progress"
                else:
                    no_progress_streak = 0
            last_signature = signature
            if state.fans_to_target is not None and state.fans_to_target <= 0:
                self._log_turn(turn_index, state, last_decision, "complete")
                return "complete"
            decision = self._strategy.decide(state)
            last_state = state
            last_decision = decision
            self._log_turn(turn_index, state, decision, stop_reason=None)
            turn_index += 1
            self._log(
                f"[produce] turn season={state.season} week={state.week_remaining} "
                f"fans_left={state.fans_to_target} -> {decision.action_kind} "
                f"slot={decision.target_slot} ({decision.rationale})",
            )
            if decision.action_kind in {"lesson", "audition"} and not on_schedule:
                # home 起点のときだけ produce_card で schedule へ遷移する。
                # 既に schedule にいる (schedule 起点) ならタップ不要。
                self._tap(self._points.home.produce_card)
                reached = self.wait_for_screen(
                    {"schedule_lesson", "schedule_audition"},
                    timeout=schedule_timeout,
                )
                if reached is None:
                    self._log_turn(
                        turn_index, state, decision, "stuck:schedule",
                    )
                    return "stuck:schedule"
            self.execute_decision(decision)
            time.sleep(self._loop_interval)
        self._log_turn(turn_index, last_state, last_decision, "max_turns")
        return "max_turns"

    def _reach_ready_screen(
        self,
        *,
        max_taps: int,
        poll_interval: float,
    ) -> str | None:
        """ターン開始可能な画面 (home / schedule) まで中間画面を消化する.

        `consume_until_home` の False は「schedule 到達」と「max_taps
        使い切り (詰まり)」を区別できないので、ここで画面種別を見て
        曖昧性を解消する。schedule 起点も有効な開始状態として扱う。

        Args:
            max_taps: 中間画面消化の最大タップ回数。
            poll_interval: ポーリング間隔 (秒)。

        Returns:
            "home" / "schedule" のいずれか。詰まりなら None。
        """
        if self.consume_until_home(
            max_taps=max_taps,
            poll_interval=poll_interval,
        ):
            return "home"
        if self.detect_screen() in {"schedule_lesson", "schedule_audition"}:
            return "schedule"
        return None

    def _log_turn(
        self,
        turn_index: int,
        state: GameState | None,
        decision: TurnDecision | None,
        stop_reason: str | None,
    ) -> None:
        if state is None or decision is None:
            # 最初のターンで stuck したケース等。dummy エントリは書かない
            return
        entry = TurnLogEntry.from_state_and_decision(
            turn_index,
            state,
            decision,
            stop_reason=stop_reason,
        )
        if self._turn_logger is not None:
            self._turn_logger.log(entry)
        if self._summary is not None:
            self._summary.record(entry)

    def consume_until_home(
        self,
        *,
        max_taps: int = 30,
        poll_interval: float = 0.5,
        unknown_threshold: int = 5,
        checkmark_fallback: bool = True,
    ) -> bool:
        """不明な中間画面 (結果表示・会話など) を中央タップで送ってホームへ戻す。

        ホーム or スケジュール画面に到達したら停止する。`unknown` が連続
        `unknown_threshold` 回出現したら、まず checkmark 確定タップ
        (`tap_dialog_checkmark_fallback`) を試み、それでも遷移しなければ
        `try_dismiss_modal` で閉じる候補を順に試す。

        Args:
            max_taps: 中央タップを試みる最大回数。
            poll_interval: 各タップ後に画面遷移を待つ秒数。
            unknown_threshold: この連続未識別回数を超えたらリカバリ発動。
            checkmark_fallback: True なら modal_dismiss の前に checkmark
                fallback を 1 回試す (E1.3, 旧 sample2.yml 互換)。

        Returns:
            ホーム画面に到達したら True、スケジュール画面に到達 or 上限
            到達なら False。
        """
        unknown_streak = 0
        for _ in range(max_taps):
            kind = self.detect_screen()
            if kind == "home":
                return True
            if kind in {"schedule_lesson", "schedule_audition"}:
                return False
            unknown_streak += 1
            if unknown_streak >= unknown_threshold:
                self._log(
                    f"[produce] unknown screen streak={unknown_streak}; "
                    "attempting dialog/modal recovery",
                )
                if checkmark_fallback and self._try_checkmark_recovery(
                    settle=poll_interval,
                ):
                    unknown_streak = 0
                    continue
                if self.try_dismiss_modal(settle=poll_interval):
                    unknown_streak = 0
                    continue
            self._tap(self._points.dialog.advance_safe)
            time.sleep(poll_interval)
        return False

    def _try_checkmark_recovery(self, *, settle: float) -> bool:
        """Checkmark fallback をタップし、画面遷移したら True を返す内部 helper.

        Args:
            settle: タップ後に画面遷移を待つ秒数。

        Returns:
            `unknown` 以外の画面に遷移したら True、そうでなければ False。
        """
        self._log("[produce] try checkmark fallback")
        self.tap_dialog_checkmark_fallback()
        time.sleep(settle)
        kind = self.detect_screen()
        if kind != "unknown":
            self._log(f"[produce] checkmark fallback success -> {kind}")
            return True
        return False

    def try_dismiss_modal(self, *, settle: float = 0.5) -> bool:
        """想定外モーダルを閉じる候補を順に試し、画面遷移したら True を返す。

        各候補をタップ → `settle` 秒待機 → 画面種別を再判定し、`unknown`
        以外になったら遷移成功とみなす。

        Args:
            settle: 各候補タップ後に画面遷移を待つ秒数。

        Returns:
            いずれかの候補で `unknown` 以外の画面に遷移できたら True、
            全候補を試してもダメなら False。
        """
        for candidate in modal_dismiss_sequence(self._points.modal_dismiss):
            self._log(f"[produce] dismiss try: {candidate.description}")
            self._tap(candidate)
            time.sleep(settle)
            kind = self.detect_screen()
            if kind != "unknown":
                self._log(f"[produce] dismiss success -> {kind}")
                return True
        return False

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

    def _swipe_to_target_audition(
        self,
        *,
        target_name: str | None,
        max_swipes: int,
    ) -> None:
        """G2: 目的のオーディションカードに到達するまで swipe する.

        各 swipe の前に reader で現在中央のカード名を観測し、`target_name`
        が前方一致したら early break する。観測が空文字 (OCR 失敗) のときは
        判定をスキップし、従来通り `max_swipes` 回固定 swipe で消化する。

        Args:
            target_name: 目的カード名。`None` なら判定せず `max_swipes` 回
                固定 swipe する従来挙動。
            max_swipes: 最大スワイプ回数 (= `target_slot`)。
        """
        for _ in range(max_swipes):
            if target_name and self._audition_matches_target(target_name):
                self._log(
                    f"[produce] target audition '{target_name}' already at "
                    "center; skipping further swipes",
                )
                return
            self._swipe_audition_next()
            self._sleep_settle()
        # 最後の swipe 後にもう 1 回 check してログを残す (確定 tap 前情報)
        if target_name and self._audition_matches_target(target_name):
            self._log(
                f"[produce] target audition '{target_name}' confirmed at center",
            )

    def _audition_matches_target(self, target_name: str) -> bool:
        """現在中央のオーディションカード名が `target_name` を含むか判定する.

        Returns:
            OCR で読めた名前に `target_name` (前方一致 or 部分一致) が含まれる
            なら True。OCR が空文字なら False (= 判定できないので swipe 継続)。
        """
        frame = self._capture.capture(region=self._region)
        current = self._reader.read_current_audition_name(frame)
        if not current:
            return False
        return target_name in current

    def _sleep_settle(self) -> None:
        time.sleep(self._click_settle)
