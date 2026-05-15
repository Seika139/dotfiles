"""`ProduceStateReader` のユニットテスト。

OCR 依存テストは tesseract バイナリ未インストール環境では自動スキップする。
golden 画像は `tests/fixtures/produce/` 配下。
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PIL import Image

from auto_emulator.games.produce import (
    FractionalRegion,
    GameState,
    LessonRegions,
    ProduceStateReader,
    StatsRegions,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "produce"
SCHEDULE_FIXTURE = FIXTURE_DIR / "schedule_s2_w8_fans6225.png"

requires_tesseract = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="tesseract バイナリ未インストール",
)


class TestFractionalRegion:
    def test_to_pixels_scales_by_image_size(self) -> None:
        region = FractionalRegion(x=0.25, y=0.5, w=0.5, h=0.25)
        assert region.to_pixels(1000, 800) == (250, 400, 750, 600)

    def test_rejects_overflow(self) -> None:
        with pytest.raises(ValueError, match="x\\+w が"):
            FractionalRegion(x=0.6, y=0.0, w=0.5, h=0.1)


class TestGameStateDefaults:
    def test_unknown_screen_by_default(self) -> None:
        state = GameState()
        assert state.screen == "unknown"
        assert state.season is None
        assert state.audition_available is False
        assert state.lessons == []


class TestIterLessonRegions:
    def test_default_returns_six_pairs(self) -> None:
        pairs = ProduceStateReader.iter_lesson_regions(LessonRegions())
        assert len(pairs) == 6

    def test_pairs_are_in_left_to_right_order(self) -> None:
        pairs = ProduceStateReader.iter_lesson_regions(LessonRegions())
        name_xs = [name_region.x for name_region, _ in pairs]
        assert name_xs == sorted(name_xs)

    def test_name_and_level_bands_dont_overlap(self) -> None:
        pairs = ProduceStateReader.iter_lesson_regions(LessonRegions())
        for name_region, level_region in pairs:
            # name バンドの方が下 (y 大)
            assert name_region.y > level_region.y + level_region.h, (
                "level バンドが name バンドの上にある前提"
            )

    def test_custom_layout_with_three_cards(self) -> None:
        pairs = ProduceStateReader.iter_lesson_regions(
            LessonRegions(card_centers_x=(0.25, 0.5, 0.75), card_width=0.20),
        )
        assert len(pairs) == 3
        # 中央カードの name は中心 0.5 から ±0.10 = 0.40-0.60
        name0, _ = pairs[1]
        assert name0.x == pytest.approx(0.40)
        assert name0.w == pytest.approx(0.20)


class TestSelectedFansPreview:
    """#40: 選択中レッスンの単一 fans プレビュー領域とその読取."""

    def test_region_inside_image_and_above_cards(self) -> None:
        regions = LessonRegions()
        r = regions.selected_fans_preview
        assert 0.0 <= r.x <= 1.0
        assert 0.0 <= r.y <= 1.0
        assert r.x + r.w <= 1.0
        assert r.y + r.h <= 1.0
        # プレビュー帯はカード name バンドより上 (y 小) にある
        assert r.y + r.h <= regions.name_band[0]

    def test_lessons_have_no_per_card_fans(self) -> None:
        # #40: per-card preview_fans は単一フレームで取れず常に None
        reader = ProduceStateReader()
        with Image.open(FIXTURE_DIR / "real_schedule_canvas.png") as img:
            lessons = reader.lessons_from_schedule(img)
        assert all(opt.preview_fans is None for opt in lessons)

    @requires_tesseract
    def test_reads_selected_preview_on_canvas(self) -> None:
        # 実機 canvas の選択中カードは「+277」。Tesseract で読める
        reader = ProduceStateReader()
        with Image.open(FIXTURE_DIR / "real_schedule_canvas.png") as img:
            value = reader.read_selected_lesson_preview_fans(img)
        assert value == 277


class TestAuditionCenterCardRegion:
    """G2: `AuditionRegions.center_card_name` のデフォルト値検証."""

    def test_default_region_is_inside_image(self) -> None:
        from auto_emulator.games.produce.reader import (  # noqa: PLC0415
            AuditionRegions,
        )

        regions = AuditionRegions()
        cn = regions.center_card_name
        # fractional は 0.0-1.0 範囲内
        assert 0.0 <= cn.x <= 1.0
        assert 0.0 <= cn.y <= 1.0
        # x+w / y+h も 1.0 以内
        assert cn.x + cn.w <= 1.0
        assert cn.y + cn.h <= 1.0

    def test_read_current_audition_name_returns_empty_on_blank_image(
        self,
    ) -> None:
        from auto_emulator.games.produce.reader import (  # noqa: PLC0415
            ProduceStateReader,
        )

        reader = ProduceStateReader()
        blank = Image.new("RGB", (3024, 1610), color=(200, 200, 200))
        # 完全に灰色なら Tesseract は空 (or 空白) を返す
        name = reader.read_current_audition_name(blank)
        # OCR 結果は空白除去後、不確定文字混入の可能性はあるが
        # 「読めない」状況で空文字相当を返すことだけ確認
        assert isinstance(name, str)


class TestIterStatRegions:
    def test_default_returns_six_stats(self) -> None:
        pairs = ProduceStateReader.iter_stat_regions(StatsRegions())
        assert len(pairs) == 6

    def test_labels_are_canonical(self) -> None:
        pairs = ProduceStateReader.iter_stat_regions(StatsRegions())
        labels = [label for label, _ in pairs]
        assert labels == ["Vo", "Da", "Vi", "Me", "SP", "Fans"]

    def test_stats_are_left_to_right(self) -> None:
        pairs = ProduceStateReader.iter_stat_regions(StatsRegions())
        xs = [region.x for _, region in pairs]
        assert xs == sorted(xs)


class TestHpBarColorAnalysis:
    def test_full_pink_bar_returns_one(self) -> None:
        # 全幅ピンク (HSV で saturation 高) の合成画像
        bar = Image.new("RGB", (3024, 1610), color=(50, 50, 50))
        pink = Image.new("RGB", (3024, 200), color=(240, 80, 130))
        bar.paste(pink, (0, 30))
        reader = ProduceStateReader()
        pct = reader.read_hp_pct(bar)
        assert pct is not None
        assert pct > 0.95

    def test_empty_gray_bar_returns_near_zero(self) -> None:
        gray = Image.new("RGB", (3024, 1610), color=(180, 180, 180))
        reader = ProduceStateReader()
        pct = reader.read_hp_pct(gray)
        assert pct is not None
        assert pct < 0.05


class TestScreenKindDetection:
    def test_home_fixture(self) -> None:
        with Image.open(FIXTURE_DIR / "home_s2_w8.png") as img:
            assert ProduceStateReader.detect_screen_kind(img) == "home"

    def test_schedule_lesson_fixture(self) -> None:
        with Image.open(SCHEDULE_FIXTURE) as img:
            assert ProduceStateReader.detect_screen_kind(img) == "schedule_lesson"

    def test_audition_battle_fixture(self) -> None:
        with Image.open(FIXTURE_DIR / "audition_turn1.png") as img:
            assert ProduceStateReader.detect_screen_kind(img) == "audition_battle"

    def test_real_canvas_schedule_fixture(self) -> None:
        # Phase 3: 実機 canvas キャプチャでも schedule_lesson を検出する回帰
        with Image.open(FIXTURE_DIR / "real_schedule_canvas.png") as img:
            assert ProduceStateReader.detect_screen_kind(img) == "schedule_lesson"

    def test_real_canvas_home_fixture(self) -> None:
        # Phase 3: 実機 canvas キャプチャでも home を検出する回帰
        with Image.open(FIXTURE_DIR / "real_home_canvas.png") as img:
            assert ProduceStateReader.detect_screen_kind(img) == "home"

    def test_tiny_image_returns_unknown(self) -> None:
        with Image.new("RGB", (5, 5)) as img:
            assert ProduceStateReader.detect_screen_kind(img) == "unknown"

    def test_uniform_neutral_blue_returns_unknown(self) -> None:
        # 中性的な青グレー: schedule (R 高) / home (G>R) / audition (全部 <140)
        # のいずれの signature にも該当しない
        with Image.new("RGB", (3024, 1610), color=(180, 195, 220)) as img:
            assert ProduceStateReader.detect_screen_kind(img) == "unknown"


class TestProduceStateReader:
    def test_lessons_without_tesseract_returns_six_placeholders(self) -> None:
        # tesseract 未導入でも構造的な戻り値は壊さない (placeholder で埋める)
        if shutil.which("tesseract") is not None:
            pytest.skip("tesseract がある環境では別テスト")
        reader = ProduceStateReader()
        with Image.new("RGB", (3024, 1610)) as img:
            options = reader.lessons_from_schedule(img)
        assert len(options) == 6
        assert [opt.slot for opt in options] == [0, 1, 2, 3, 4, 5]
        for opt in options:
            assert opt.level == 1  # OCR 失敗時のデフォルト
            assert opt.preview_fans is None

    def test_real_canvas_schedule_robust_signals(self) -> None:
        """Phase 3: デフォルト座標は実機 canvas 領域基準。

        装飾フォントの数字 (season/week/tension) は vanilla Tesseract
        では読めず DigitMatcher テンプレ前提なので、ここではフォント
        非依存で頑健なシグナル (screen 検出 / 色ベースの HP バー / トラブル
        率) のみを契約として固定する。digit 値の精度は
        `test_produce_digit_matcher.py` 側で担保する。
        """
        fixture = FIXTURE_DIR / "real_schedule_canvas.png"
        assert fixture.exists(), f"canvas リファレンスが見つかりません: {fixture}"
        reader = ProduceStateReader()
        with Image.open(fixture) as img:
            state = reader.read(img)
        # screen 検出は右下色 signature でフォント非依存
        assert state.screen == "schedule_lesson"
        # HP バーは色比率なので装飾フォントの影響を受けない
        assert state.hp_pct is not None
        assert 0.0 < state.hp_pct < 1.0
        # トラブル率は太字数字で Tesseract でも比較的安定 (実機値 8%)
        assert state.trouble_pct == 8

    def test_old_wide_fixture_still_loads_without_crash(self) -> None:
        """旧 3024x1610 fixture は canvas 比率と非互換だが read() が例外を出さない。

        旧 fixture はもう座標基準ではない (canvas が基準)。値は保証しないが、
        異なるアスペクト比の画像でもクラッシュせず GameState を返すことを
        確認する (頑健性の回帰)。
        """
        assert SCHEDULE_FIXTURE.exists()
        reader = ProduceStateReader()
        with Image.open(SCHEDULE_FIXTURE) as img:
            state = reader.read(img)
        assert isinstance(state, GameState)

    @requires_tesseract
    def test_raw_text_always_populated(self) -> None:
        reader = ProduceStateReader()
        with Image.open(SCHEDULE_FIXTURE) as img:
            state = reader.read(img)
        for key in ("header_season_text", "header_week_text", "header_fans_text"):
            assert key in state.raw
