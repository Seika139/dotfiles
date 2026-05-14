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
    queue: list[Image.Image] = field(default_factory=list)

    def capture(self, region: Region) -> Image.Image:  # noqa: ARG002
        if self.queue:
            return self.queue.pop(0)
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


class TestAuditionSwipeEarlyBreak:
    """G2: `target_audition_name` を元にした swipe ループの早期終了."""

    @staticmethod
    def _build(
        decision: TurnDecision,
        reader_name: str,
    ) -> tuple[ProduceEngine, FakePointer]:
        from auto_emulator.games.produce.reader import (  # noqa: PLC0415
            ProduceStateReader,
        )

        class _FakeReader(ProduceStateReader):
            def read_current_audition_name(
                self,
                image: Image.Image,  # noqa: ARG002
            ) -> str:
                return reader_name

        pointer = FakePointer()
        capture = FakeCapture(Image.new("RGB", (3024, 1610)))
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            reader=_FakeReader(),
            strategy=FakeStrategy(decision),
            capture=capture,
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        return engine, pointer

    def test_breaks_early_when_target_matches_immediately(self) -> None:
        # reader が常に "夕方ワイド アイドル一番" を返す
        decision = TurnDecision(
            action_kind="audition",
            target_slot=3,  # 通常なら 3 回 swipe する設定
            target_audition_name="夕方ワイド",
            rationale="t",
        )
        engine, pointer = self._build(decision, "夕方ワイド アイドル一番")
        engine.step()
        # target_slot=3 でも 1 回目 check で一致 → swipe 0 回
        assert len(pointer.drags) == 0
        # audition_tab + confirm_button の 2 click のみ
        assert len(pointer.clicks) == 2

    def test_falls_back_to_fixed_swipes_when_ocr_empty(self) -> None:
        # OCR 失敗 (空文字) → 従来通り target_slot 回 swipe
        decision = TurnDecision(
            action_kind="audition",
            target_slot=2,
            target_audition_name="夕方ワイド",
            rationale="t",
        )
        engine, pointer = self._build(decision, "")
        engine.step()
        # OCR 失敗で判定スキップ → 固定 2 回 swipe
        assert len(pointer.drags) == 2

    def test_no_target_name_uses_fixed_swipes(self) -> None:
        # target_audition_name=None → 従来挙動 (G2 機能を発火させない)
        decision = TurnDecision(
            action_kind="audition",
            target_slot=2,
            target_audition_name=None,
            rationale="t",
        )
        # reader が "夕方ワイド..." を返しても target_name=None なら判定しない
        engine, pointer = self._build(decision, "夕方ワイド アイドル一番")
        engine.step()
        assert len(pointer.drags) == 2

    def test_partial_match_triggers_break(self) -> None:
        # target_name が reader の名前に部分一致するだけで break する
        decision = TurnDecision(
            action_kind="audition",
            target_slot=5,
            target_audition_name="THE LEGEND",
            rationale="t",
        )
        engine, pointer = self._build(
            decision,
            "THE LEGEND 〜ファイナル〜",
        )
        engine.step()
        assert len(pointer.drags) == 0


class TestDialogAndBattleHelpers:
    def test_enable_battle_auto_clicks_auto_then_speed(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="noop", rationale="setup"),
        )
        engine.enable_battle_auto()
        assert len(pointer.clicks) == 2
        # AUTO トグル (0.782) → 倍速トグル (0.861)
        assert pointer.clicks[0][0] < pointer.clicks[1][0]

    def test_tap_dialog_yellow_choice(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="noop", rationale="setup"),
        )
        engine.tap_dialog_yellow_choice()
        assert len(pointer.clicks) == 1
        x, _ = pointer.clicks[0]
        # 黄色は右側
        assert x > 0.7

    def test_enable_dialog_fast_forward(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="noop", rationale="setup"),
        )
        engine.enable_dialog_fast_forward()
        assert len(pointer.clicks) == 1
        x, y = pointer.clicks[0]
        # 右下に位置するはず
        assert x > 0.7
        assert y > 0.85


class TestHomeScreenActions:
    def test_rest_clicks_card_then_confirm(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="rest", rationale="trouble high"),
        )
        engine.step()
        # 休むカード + 確認 OK の 2 クリック
        assert len(pointer.clicks) == 2
        rest_card_x, _ = pointer.clicks[0]
        assert 0.30 < rest_card_x < 0.42  # rest_card デフォルト 0.367

    def test_reflection_clicks_card(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="reflection", rationale="skill"),
        )
        engine.step()
        # 振り返りカード のみ (スキルパネルは Phase 5c)
        assert len(pointer.clicks) == 1
        reflection_x, _ = pointer.clicks[0]
        assert 0.55 < reflection_x < 0.65  # reflection_card デフォルト 0.597

    def test_noop_does_not_click(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="noop", rationale="no plan"),
        )
        engine.step()
        assert len(pointer.clicks) == 0


class TestRunLoop:
    def test_max_turns_caps_executions(self) -> None:
        engine, pointer = _engine(
            TurnDecision(action_kind="lesson", target_slot=0, rationale="t"),
        )
        executed = engine.run(max_turns=3)
        assert executed == 3
        # 1 ターンで 2 クリック (カード + 決定) → 6 クリック
        assert len(pointer.clicks) == 6


class TestScreenDetectionIntegration:
    @staticmethod
    def _image_with_br_color(color: tuple[int, int, int]) -> Image.Image:
        """右下に signature 色を持つ画像を組み立てる。

        Returns:
            3024x1610 PNG。右下のみ指定色、それ以外は中間グレー。
        """
        img = Image.new("RGB", (3024, 1610), color=(200, 200, 200))
        # 検出が見る領域 (fractional 0.81-0.88 / 0.91-0.96) を塗りつぶす
        block = Image.new("RGB", (212, 80), color=color)
        img.paste(block, (2449, 1465))
        return img

    def test_detect_screen_uses_capture(self) -> None:
        schedule_img = self._image_with_br_color((220, 149, 191))
        pointer = FakePointer()
        capture = FakeCapture(schedule_img)
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            capture=capture,
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        assert engine.detect_screen() == "schedule_lesson"

    def test_wait_for_screen_returns_first_match(self) -> None:
        home_img = self._image_with_br_color((163, 214, 136))
        schedule_img = self._image_with_br_color((220, 149, 191))
        pointer = FakePointer()
        capture = FakeCapture(
            image=schedule_img,
            queue=[home_img, home_img, schedule_img],
        )
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            capture=capture,
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        result = engine.wait_for_screen(
            "schedule_lesson",
            timeout=5.0,
            poll_interval=0.0,
        )
        assert result == "schedule_lesson"

    def test_wait_for_screen_timeout_returns_none(self) -> None:
        gray = Image.new("RGB", (3024, 1610), color=(180, 195, 220))
        pointer = FakePointer()
        capture = FakeCapture(gray)
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            capture=capture,
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        result = engine.wait_for_screen(
            "home",
            timeout=0.05,
            poll_interval=0.01,
        )
        assert result is None

    def test_wait_for_screen_accepts_set(self) -> None:
        home_img = self._image_with_br_color((163, 214, 136))
        pointer = FakePointer()
        capture = FakeCapture(home_img)
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            capture=capture,
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        result = engine.wait_for_screen(
            {"home", "schedule_lesson"},
            timeout=1.0,
            poll_interval=0.0,
        )
        assert result == "home"


class TestConsumeUntilHome:
    @staticmethod
    def _br_color_image(color: tuple[int, int, int]) -> Image.Image:
        img = Image.new("RGB", (3024, 1610), color=(200, 200, 200))
        block = Image.new("RGB", (212, 80), color=color)
        img.paste(block, (2449, 1465))
        return img

    def _build(
        self,
        capture: FakeCapture,
    ) -> tuple[ProduceEngine, FakePointer]:
        pointer = FakePointer()
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            capture=capture,
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        return engine, pointer

    def test_returns_true_immediately_when_home(self) -> None:
        home = self._br_color_image((163, 214, 136))
        capture = FakeCapture(home)
        engine, pointer = self._build(capture)
        assert engine.consume_until_home(poll_interval=0.0) is True
        assert pointer.clicks == []

    def test_taps_dialog_advance_until_home(self) -> None:
        unknown = Image.new("RGB", (3024, 1610), color=(180, 195, 220))
        home = self._br_color_image((163, 214, 136))
        capture = FakeCapture(
            image=home,
            queue=[unknown, unknown, home],
        )
        engine, pointer = self._build(capture)
        assert engine.consume_until_home(poll_interval=0.0) is True
        # 2 回 unknown を見て advance タップ、3 回目で home 検出
        assert len(pointer.clicks) == 2

    def test_returns_false_when_schedule_appears(self) -> None:
        schedule = self._br_color_image((220, 149, 191))
        capture = FakeCapture(schedule)
        engine, pointer = self._build(capture)
        assert engine.consume_until_home(poll_interval=0.0) is False
        assert pointer.clicks == []

    def test_returns_false_on_max_taps(self) -> None:
        unknown = Image.new("RGB", (3024, 1610), color=(180, 195, 220))
        capture = FakeCapture(unknown)
        engine, pointer = self._build(capture)
        assert (
            engine.consume_until_home(max_taps=4, poll_interval=0.0) is False
        )
        assert len(pointer.clicks) == 4


class TestModalDismiss:
    @staticmethod
    def _br_image(color: tuple[int, int, int]) -> Image.Image:
        img = Image.new("RGB", (3024, 1610), color=(200, 200, 200))
        block = Image.new("RGB", (212, 80), color=color)
        img.paste(block, (2449, 1465))
        return img

    HOME_COLOR = (163, 214, 136)
    UNKNOWN_COLOR = (180, 195, 220)

    def _build(self, capture: FakeCapture) -> tuple[ProduceEngine, FakePointer]:
        pointer = FakePointer()
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            capture=capture,
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        return engine, pointer

    def test_tap_dialog_checkmark_fallback(self) -> None:
        unknown = Image.new("RGB", (3024, 1610), color=self.UNKNOWN_COLOR)
        capture = FakeCapture(unknown)
        engine, pointer = self._build(capture)
        engine.tap_dialog_checkmark_fallback()
        # 単発のタップで checkmark_choice 座標 (0.500, 0.330) に発火
        assert len(pointer.clicks) == 1
        x, y = pointer.clicks[0]
        assert 0.45 < x < 0.55
        assert 0.30 < y < 0.36

    def test_consume_until_home_tries_checkmark_before_dismiss(self) -> None:
        unknown = Image.new("RGB", (3024, 1610), color=self.UNKNOWN_COLOR)
        home = self._br_image(self.HOME_COLOR)
        # streak=5 で recovery 発動 -> checkmark タップ -> home 遷移
        capture = FakeCapture(
            image=home,
            queue=[unknown, unknown, unknown, unknown, unknown, home],
        )
        engine, pointer = self._build(capture)
        result = engine.consume_until_home(
            poll_interval=0.0,
            unknown_threshold=5,
        )
        assert result is True
        # advance タップ x 4 (streak 1-4) + checkmark タップ 1 = 5
        assert len(pointer.clicks) == 5
        # 5 回目のクリックは checkmark_choice (中央上寄り)
        last_x, last_y = pointer.clicks[-1]
        assert 0.45 < last_x < 0.55
        assert 0.30 < last_y < 0.36

    def test_consume_until_home_falls_back_to_dismiss_when_checkmark_fails(
        self,
    ) -> None:
        unknown = Image.new("RGB", (3024, 1610), color=self.UNKNOWN_COLOR)
        home = self._br_image(self.HOME_COLOR)
        # streak=5 -> checkmark タップしても unknown -> modal_dismiss 候補で home
        capture = FakeCapture(
            image=home,
            queue=[
                unknown,
                unknown,
                unknown,
                unknown,
                unknown,
                unknown,  # checkmark タップ後の検出も unknown
                home,  # modal_dismiss 1 候補目で home
            ],
        )
        engine, pointer = self._build(capture)
        result = engine.consume_until_home(
            poll_interval=0.0,
            unknown_threshold=5,
        )
        assert result is True
        # advance x4 + checkmark 1 + modal_dismiss 1 候補 = 6
        assert len(pointer.clicks) == 6

    def test_consume_until_home_checkmark_can_be_disabled(self) -> None:
        unknown = Image.new("RGB", (3024, 1610), color=self.UNKNOWN_COLOR)
        home = self._br_image(self.HOME_COLOR)
        # checkmark_fallback=False -> 即 modal_dismiss が発動
        capture = FakeCapture(
            image=home,
            queue=[unknown, unknown, unknown, unknown, unknown, home],
        )
        engine, pointer = self._build(capture)
        result = engine.consume_until_home(
            poll_interval=0.0,
            unknown_threshold=5,
            checkmark_fallback=False,
        )
        assert result is True
        # advance x4 + modal_dismiss 1 = 5 (checkmark タップは入らない)
        assert len(pointer.clicks) == 5
        # 5 回目のクリックは modal_dismiss の close_top_right (x≈0.965)
        last_x, _ = pointer.clicks[-1]
        assert last_x > 0.9

    def test_try_dismiss_modal_stops_on_first_success(self) -> None:
        home = self._br_image(self.HOME_COLOR)
        # 最初の dismiss 候補で home に遷移するシナリオ
        capture = FakeCapture(image=home, queue=[home])
        engine, pointer = self._build(capture)
        # detect_screen は queue 消費後 default (home) を返すので最初の candidate で成功
        assert engine.try_dismiss_modal(settle=0.0) is True
        assert len(pointer.clicks) == 1  # 1 候補で打ち止め

    def test_try_dismiss_modal_returns_false_when_all_fail(self) -> None:
        unknown = Image.new("RGB", (3024, 1610), color=self.UNKNOWN_COLOR)
        capture = FakeCapture(unknown)
        engine, pointer = self._build(capture)
        assert engine.try_dismiss_modal(settle=0.0) is False
        # 4 候補すべて試す
        assert len(pointer.clicks) == 4

    def test_consume_until_home_invokes_dismiss_when_streak_exceeded(self) -> None:
        unknown = Image.new("RGB", (3024, 1610), color=self.UNKNOWN_COLOR)
        home = self._br_image(self.HOME_COLOR)
        # unknown を 5 回観測 -> dismiss 発動 -> 候補 1 目で home 遷移
        capture = FakeCapture(
            image=home,
            queue=[unknown, unknown, unknown, unknown, unknown, home],
        )
        engine, pointer = self._build(capture)
        result = engine.consume_until_home(
            poll_interval=0.0,
            unknown_threshold=5,
        )
        assert result is True
        # advance タップ x 4 (streak 1-4) + dismiss 候補 1 個 = 5
        # streak=5 で dismiss 発動して success ならその後はループ先頭の home 検出
        assert len(pointer.clicks) == 5


class TestReadStateWithRetry:
    @staticmethod
    def _br_image(color: tuple[int, int, int]) -> Image.Image:
        img = Image.new("RGB", (3024, 1610), color=(200, 200, 200))
        block = Image.new("RGB", (212, 80), color=color)
        img.paste(block, (2449, 1465))
        return img

    HOME_COLOR = (163, 214, 136)

    def _engine(self) -> ProduceEngine:
        return ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            capture=FakeCapture(self._br_image(self.HOME_COLOR)),
            pointer=FakePointer(),
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )

    def test_returns_state_when_no_fields_required(self) -> None:
        engine = self._engine()
        # フェイク画像なので season は None だが require_fields が空なら通る
        state = engine.read_state_with_retry(
            require_fields=(),
            max_attempts=1,
            poll_interval=0.0,
        )
        assert state is not None

    def test_returns_none_when_required_field_missing(self) -> None:
        engine = self._engine()
        # season は OCR 不可なので必ず None -> リトライしても揃わない
        state = engine.read_state_with_retry(
            require_fields=("season",),
            max_attempts=2,
            poll_interval=0.0,
        )
        assert state is None

    def test_run_full_produce_returns_stuck_ocr_when_required_field_missing(
        self,
    ) -> None:
        home = self._br_image(self.HOME_COLOR)
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            strategy=FakeStrategy(
                TurnDecision(action_kind="rest", rationale="t"),
            ),
            capture=FakeCapture(home),
            pointer=FakePointer(),
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        result = engine.run_full_produce(
            max_turns=3,
            consume_poll_interval=0.0,
            ocr_retry_attempts=2,
            ocr_retry_interval=0.0,
            require_fields=("season",),
        )
        assert result == "stuck:ocr"


class TestItemAndChoiceColor:
    @staticmethod
    def _br_image(color: tuple[int, int, int]) -> Image.Image:
        img = Image.new("RGB", (3024, 1610), color=(200, 200, 200))
        block = Image.new("RGB", (212, 80), color=color)
        img.paste(block, (2449, 1465))
        return img

    HOME_COLOR = (163, 214, 136)

    def _build(self) -> tuple[ProduceEngine, FakePointer]:
        pointer = FakePointer()
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            strategy=FakeStrategy(
                TurnDecision(action_kind="noop", rationale="setup"),
            ),
            capture=FakeCapture(self._br_image(self.HOME_COLOR)),
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        return engine, pointer

    def test_execute_item_emits_four_clicks(self) -> None:
        engine, pointer = self._build()
        engine.execute_decision(
            TurnDecision(action_kind="item", rationale="hp low"),
        )
        # アイテムタブ + first_slot + use + close = 4 クリック
        assert len(pointer.clicks) == 4
        # 最初のクリックは home.item_tab (x≈0.050)
        assert pointer.clicks[0][0] < 0.10
        # 最後のクリックは close_button (x≈0.500)
        assert 0.45 < pointer.clicks[3][0] < 0.55

    def test_tap_dialog_pink_choice(self) -> None:
        engine, pointer = self._build()
        engine.tap_dialog_pink_choice()
        assert len(pointer.clicks) == 1
        assert pointer.clicks[0][0] < 0.30  # 左寄り

    def test_tap_dialog_green_choice(self) -> None:
        engine, pointer = self._build()
        engine.tap_dialog_green_choice()
        assert len(pointer.clicks) == 1
        # 緑色の選択肢は中央付近 (x 約 0.46)
        assert 0.35 < pointer.clicks[0][0] < 0.55

    def test_tap_dialog_choice_by_index_maps_color(self) -> None:
        engine, pointer = self._build()
        engine.tap_dialog_choice_by_index(0)
        engine.tap_dialog_choice_by_index(1)
        engine.tap_dialog_choice_by_index(2)
        engine.tap_dialog_choice_by_index(99)  # クランプで yellow
        # 0=桃 / 1=緑 / 2=黄 / 99→黄 と並ぶ
        xs = [c[0] for c in pointer.clicks]
        assert xs[0] < xs[1] < xs[2]  # 左→中央→右
        assert xs[3] == xs[2]  # クランプで yellow と同じ


class TestRunFullProduce:
    @staticmethod
    def _br_image(color: tuple[int, int, int]) -> Image.Image:
        img = Image.new("RGB", (3024, 1610), color=(200, 200, 200))
        block = Image.new("RGB", (212, 80), color=color)
        img.paste(block, (2449, 1465))
        return img

    HOME_COLOR = (163, 214, 136)
    SCHEDULE_COLOR = (220, 149, 191)
    UNKNOWN_COLOR = (180, 195, 220)

    def _build(
        self,
        capture: FakeCapture,
        decision: TurnDecision,
    ) -> tuple[ProduceEngine, FakePointer]:
        pointer = FakePointer()
        engine = ProduceEngine(
            region=Region(left=0.0, top=0.0, right=1000.0, bottom=1000.0),
            strategy=FakeStrategy(decision),
            capture=capture,
            pointer=pointer,
            click_settle=0.0,
            loop_interval=0.0,
            logger=lambda _: None,
        )
        return engine, pointer

    def test_stuck_home_when_no_screen_detected(self) -> None:
        unknown = Image.new("RGB", (3024, 1610), color=self.UNKNOWN_COLOR)
        engine, _ = self._build(
            FakeCapture(unknown),
            TurnDecision(action_kind="rest", rationale="t"),
        )
        # consume_until_home が max_taps を使い切って False を返す
        result = engine.run_full_produce(
            max_turns=2,
            consume_max_taps=3,
            consume_poll_interval=0.0,
        )
        assert result == "stuck:home"

    def test_stuck_schedule_when_produce_card_no_op(self) -> None:
        # 常にホーム画面を返す -> プロデュースカード押してもスケジュールに行かない
        home = self._br_image(self.HOME_COLOR)
        engine, _ = self._build(
            FakeCapture(home),
            TurnDecision(action_kind="lesson", target_slot=0, rationale="t"),
        )
        result = engine.run_full_produce(
            max_turns=3,
            schedule_timeout=0.02,
            consume_poll_interval=0.0,
            require_fields=(),  # OCR 経路をスキップして遷移失敗のみ検証
        )
        assert result == "stuck:schedule"

    def test_max_turns_with_rest_decision(self) -> None:
        # rest はホーム画面から実行されるためスケジュール遷移を要さない
        home = self._br_image(self.HOME_COLOR)
        engine, pointer = self._build(
            FakeCapture(home),
            TurnDecision(action_kind="rest", rationale="trouble"),
        )
        result = engine.run_full_produce(
            max_turns=3,
            consume_poll_interval=0.0,
            require_fields=(),
            no_progress_threshold=0,  # B2 を無効化
        )
        assert result == "max_turns"
        # 各ターン: rest card + confirm OK の 2 クリック x 3 = 6
        assert len(pointer.clicks) == 6

    def test_stuck_no_progress_when_signature_repeats(self) -> None:
        # フェイク画像なので signature は (None, None, None) で毎ターン一致
        home = self._br_image(self.HOME_COLOR)
        engine, _ = self._build(
            FakeCapture(home),
            TurnDecision(action_kind="rest", rationale="t"),
        )
        result = engine.run_full_produce(
            max_turns=10,
            consume_poll_interval=0.0,
            require_fields=(),
            no_progress_threshold=2,  # 2 ターン同一で発火
        )
        assert result == "stuck:no_progress"

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
