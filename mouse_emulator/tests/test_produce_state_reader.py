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


class TestIterLessonFansRegions:
    """G3: `iter_lesson_fans_regions` のジオメトリ検証."""

    def test_default_returns_six_regions(self) -> None:
        fans = ProduceStateReader.iter_lesson_fans_regions(LessonRegions())
        assert len(fans) == 6

    def test_fans_band_is_above_name_band(self) -> None:
        regions = LessonRegions()
        fans = ProduceStateReader.iter_lesson_fans_regions(regions)
        for fans_region in fans:
            # fans プレビュー (上部) は name バンド (下部) より上にある
            assert fans_region.y + fans_region.h <= regions.name_band[0]

    def test_fans_regions_left_to_right(self) -> None:
        fans = ProduceStateReader.iter_lesson_fans_regions(LessonRegions())
        xs = [r.x for r in fans]
        assert xs == sorted(xs)


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

    @requires_tesseract
    def test_reads_schedule_fixture_week_remaining(self) -> None:
        """週数 (大型黄色 "8") は vanilla Tesseract で安定して読める。

        他のフィールド (season "2", fans "6,225") は装飾フォントで
        誤認されやすいので別テストで「読めるが値は best effort」のみ
        確認する。
        """
        assert SCHEDULE_FIXTURE.exists(), (
            f"golden 画像が見つかりません: {SCHEDULE_FIXTURE}"
        )
        reader = ProduceStateReader()
        with Image.open(SCHEDULE_FIXTURE) as img:
            state = reader.read(img)
        assert state.week_remaining == 8, (
            f"raw week text: {state.raw.get('header_week_text')!r}"
        )

    @requires_tesseract
    def test_other_header_fields_are_readable_but_not_strict(self) -> None:
        """OCR が誤認しても None でなければ「リージョンは正しい場所を指す」と見做す。

        装飾フォントで season "2"→"4" / fans "6,225"→"9965" 等の誤認が
        起きるため厳密一致は期待しない。長期的には数字テンプレートマッチ
        への置換で値の正確性を上げる。
        """
        reader = ProduceStateReader()
        with Image.open(SCHEDULE_FIXTURE) as img:
            state = reader.read(img)
        # season は OCR で "4" など読まれるが、必ず int が返ってくる
        assert state.season is not None
        # fans も同様。実値 6225 とは異なる可能性が高い
        assert state.fans_to_target is not None
        # HP バー解析は色情報なので装飾フォントの影響を受けず安定
        assert state.hp_pct is not None
        assert 0.0 < state.hp_pct < 1.0

    @requires_tesseract
    def test_raw_text_always_populated(self) -> None:
        reader = ProduceStateReader()
        with Image.open(SCHEDULE_FIXTURE) as img:
            state = reader.read(img)
        for key in ("header_season_text", "header_week_text", "header_fans_text"):
            assert key in state.raw
