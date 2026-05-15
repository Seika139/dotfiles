"""`DigitMatcher` のユニットテスト。

OCR 不要、cv2.matchTemplate のみで動くので環境依存なし。
ゴールデン画像 `schedule_s2_w8_fans6225.png` の "6,225" 領域から
digit 6 / 2 / 5 のテンプレートを抽出して自己整合性を検証する。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from auto_emulator.games.produce import (
    DigitMatcher,
    DigitTemplate,
    FractionalRegion,
    ProduceStateReader,
    extract_template,
    load_digit_templates,
)
from auto_emulator.games.produce.reader import (
    HeaderRegions,
    LessonRegions,
    StatsRegions,
    StatusRegions,
)

FIXTURE = Path(__file__).parent / "fixtures" / "produce" / "schedule_s2_w8_fans6225.png"
TEMPLATE_DIR = Path(__file__).parent / "fixtures" / "produce" / "digits"


def _fr(x: float, y: float, w: float, h: float) -> FractionalRegion:
    """`FractionalRegion` を生成する短縮ヘルパ.

    Returns:
        指定座標の `FractionalRegion`。
    """
    return FractionalRegion(x=x, y=y, w=w, h=h)


def _legacy_reader(matcher: DigitMatcher | None = None) -> ProduceStateReader:
    """旧 fixture (`schedule_s2_w8_fans6225.png`, 3024x1610) 専用の reader.

    Phase 3 でデフォルト座標は canvas 基準に移行したが、旧 fixture は
    canvas 外の余白を含む別アスペクト比なので、その回帰 anchor を保つ
    ために当時の (legacy) 座標を明示構築する。新しい実機検証は
    `real_schedule_canvas.png` + canvas digit テンプレ側で担保する。

    Returns:
        legacy 座標を注入した `ProduceStateReader`。
    """
    return ProduceStateReader(
        header=HeaderRegions(
            season_digit=_fr(0.334, 0.009, 0.022, 0.038),
            week_remaining=_fr(0.393, 0.019, 0.043, 0.075),
            fans_to_target=_fr(0.605, 0.040, 0.100, 0.052),
        ),
        stats=StatsRegions(
            stat_centers_x=(0.399, 0.490, 0.583, 0.671, 0.744, 0.870),
            stat_width=0.05,
            stat_band=(0.546, 0.585),
        ),
        status=StatusRegions(
            hp_bar=_fr(0.795, 0.018, 0.140, 0.022),
            trouble_pct=_fr(0.866, 0.255, 0.050, 0.063),
            tension_lv=_fr(0.878, 0.066, 0.014, 0.028),
        ),
        lessons=LessonRegions(
            card_centers_x=(0.220, 0.353, 0.487, 0.620, 0.753, 0.887),
            card_width=0.130,
            name_band=(0.860, 0.928),
            level_band=(0.755, 0.815),
        ),
        digit_matcher=matcher,
    )


def _load_pink_templates() -> tuple[DigitTemplate, DigitTemplate, DigitTemplate]:
    """フィクスチャの "6,225" から digit 6 / 2 / 5 をピンクスタイルで抽出。

    Returns:
        (six, two, five) のテンプレートタプル。
    """
    img = Image.open(FIXTURE)
    six = extract_template(img, (1875, 70, 1932, 128), 6, "pink")
    two = extract_template(img, (1948, 70, 2005, 128), 2, "pink")
    five = extract_template(img, (2060, 70, 2115, 128), 5, "pink")
    return six, two, five


class TestDigitTemplate:
    def test_rejects_invalid_digit(self) -> None:
        with pytest.raises(ValueError, match="digit must be 0-9"):
            DigitTemplate(digit=10, pattern=np.zeros((5, 5), dtype=np.uint8))

    def test_rejects_non_2d_pattern(self) -> None:
        with pytest.raises(ValueError, match="2D grayscale"):
            DigitTemplate(digit=5, pattern=np.zeros((5,), dtype=np.uint8))


class TestExtractTemplate:
    def test_extracts_correct_shape(self) -> None:
        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        tmpl = extract_template(img, (10, 10, 60, 70), 3)
        # height x width
        assert tmpl.pattern.shape == (60, 50)
        assert tmpl.digit == 3


class TestDigitMatcher:
    def test_empty_templates_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one template"):
            DigitMatcher([])

    def test_reads_fans_number_from_fixture(self) -> None:
        six, two, five = _load_pink_templates()
        matcher = DigitMatcher([six, two, five])
        img = Image.open(FIXTURE)
        fans_area = img.crop((1830, 60, 2150, 145))
        number = matcher.read_number(fans_area)
        assert number == 6225

    def test_finds_all_digits_in_order(self) -> None:
        six, two, five = _load_pink_templates()
        matcher = DigitMatcher([six, two, five])
        img = Image.open(FIXTURE)
        fans_area = img.crop((1830, 60, 2150, 145))
        matches = matcher.find_digits(fans_area)
        digits = [d for _, d, _ in matches]
        assert digits == [6, 2, 2, 5]

    def test_higher_threshold_drops_low_score_matches(self) -> None:
        # threshold 0.9 では同 digit のレンダリング揺らぎを許容できず
        # 第二の "2" (score ~0.69) が落ちる
        six, two, five = _load_pink_templates()
        strict = DigitMatcher([six, two, five], threshold=0.9)
        img = Image.open(FIXTURE)
        fans_area = img.crop((1830, 60, 2150, 145))
        number = strict.read_number(fans_area)
        assert number != 6225  # 第二 "2" が落ちて "625" になる
        assert number == 625

    def test_returns_none_when_no_match(self) -> None:
        six, _, _ = _load_pink_templates()
        matcher = DigitMatcher([six])
        # ピンク以外の領域 (体力バー周辺) では何もマッチしないはず
        img = Image.open(FIXTURE)
        empty_area = img.crop((100, 200, 400, 400))  # 中央のステージ背景
        assert matcher.read_number(empty_area) is None

    def test_template_larger_than_image_is_skipped(self) -> None:
        # 巨大テンプレートを与えても (image より大きい) クラッシュしない
        big_pattern = np.zeros((1000, 1000), dtype=np.uint8)
        big_tmpl = DigitTemplate(digit=0, pattern=big_pattern)
        matcher = DigitMatcher([big_tmpl])
        small = Image.new("L", (50, 50))
        assert matcher.read_number(small) is None


class TestLoadDigitTemplates:
    def test_loads_all_pngs_from_fixture_dir(self) -> None:
        templates = load_digit_templates(TEMPLATE_DIR)
        digits = {t.digit for t in templates}
        # 現状フィクスチャに含まれる digit (header: 2/5/6/8 + stats: 0-3,5-9)
        # "4" は出現していないので含まない
        assert 4 not in digits
        assert {0, 1, 2, 3, 5, 6, 7, 8, 9}.issubset(digits)

    def test_parses_style_from_filename(self) -> None:
        # 完全一致だとテンプレ追加の度に壊れるので不変条件で検証する。
        templates = load_digit_templates(TEMPLATE_DIR)
        styles_per_digit: dict[int, set[str]] = {}
        for t in templates:
            styles_per_digit.setdefault(t.digit, set()).add(t.style)
        # 旧 fixture 由来 style はそのまま残っている (legacy 回帰の前提)
        assert "pink" in styles_per_digit[2]
        assert "yellow_small" in styles_per_digit[2]
        assert "stats" in styles_per_digit[2]
        assert "yellow_large" in styles_per_digit[8]
        assert "stats" in styles_per_digit[0]
        # Phase 3 で追加した canvas style (`*_c`) が正しくパースされる
        assert "season_c" in styles_per_digit[2]
        assert "week_c" in styles_per_digit[7]
        assert "tension_c" in styles_per_digit[1]
        assert "stats_c" in styles_per_digit[0]
        assert "stats_c" in styles_per_digit[8]

    def test_returns_empty_for_nonexistent_dir(self) -> None:
        templates = load_digit_templates(TEMPLATE_DIR / "nonexistent")
        assert templates == []


CANVAS_FIXTURE = (
    Path(__file__).parent / "fixtures" / "produce" / "real_schedule_canvas.png"
)


class TestCanvasReaderWithMatcher:
    """Phase 3: 実機 canvas キャプチャ + canvas テンプレで header/status を読む.

    `real_schedule_canvas.png` は season=2 / week=7 / tension=1 /
    trouble=8 / ファン CLEAR (None) の実機状態。デフォルト座標 (canvas
    基準) + canvas digit テンプレ (`*_c`) で正しく抽出できることを固定する。
    """

    def test_header_and_status_read_correctly(self) -> None:
        templates = load_digit_templates(TEMPLATE_DIR)
        matcher = DigitMatcher(templates)
        reader = ProduceStateReader(digit_matcher=matcher)
        with Image.open(CANVAS_FIXTURE) as img:
            state = reader.read(img)
        assert state.screen == "schedule_lesson"
        assert state.season == 2
        assert state.week_remaining == 7
        assert state.tension_lv == 1
        assert state.trouble_pct == 8
        assert state.hp_pct is not None
        assert 0.0 < state.hp_pct < 1.0
        # ファン人数は "CLEAR!" 表示 (目標達成済み) なので数字なし → None
        assert state.fans_to_target is None

    def test_training_stats_read_correctly(self) -> None:
        """戦略が使う 5 ステ (Vo/Da/Vi/Me/SP) は canvas で正読できる.

        オーディション stat-ratio gating と振り返り cap proximity が
        参照するのはこの 5 つ。stats 行の Fans (累計ファン 13,775) は
        情報的で戦略非依存、かつ桁数が多く `_c` テンプレでは安定読み取り
        できない既知の制約があるため、ここでは検証しない (主ファン指標は
        ヘッダー由来の `fans_to_target`)。
        """
        templates = load_digit_templates(TEMPLATE_DIR)
        matcher = DigitMatcher(templates)
        reader = ProduceStateReader(digit_matcher=matcher)
        with Image.open(CANVAS_FIXTURE) as img:
            state = reader.read(img)
        assert state.stats is not None
        assert state.stats["Vo"] == 236
        assert state.stats["Da"] == 133
        assert state.stats["Vi"] == 101
        assert state.stats["Me"] == 178
        assert state.stats["SP"] == 30


class TestEndToEndReaderWithMatcher:
    def test_header_fields_all_correct_with_matcher(self) -> None:
        templates = load_digit_templates(TEMPLATE_DIR)
        matcher = DigitMatcher(templates)
        reader = _legacy_reader(matcher)
        with Image.open(FIXTURE) as img:
            state = reader.read(img)
        # DigitMatcher 統合で 3 つの値すべて期待通り
        assert state.season == 2
        assert state.week_remaining == 8
        assert state.fans_to_target == 6225

    def test_trouble_and_tension_with_calibrated_regions(self) -> None:
        # #25 で trouble / tension のリージョンを正しく合わせた
        templates = load_digit_templates(TEMPLATE_DIR)
        matcher = DigitMatcher(templates)
        reader = _legacy_reader(matcher)
        with Image.open(FIXTURE) as img:
            state = reader.read(img)
        assert state.trouble_pct == 8
        assert state.tension_lv == 1
        # HP は色解析で動くので必ず正常範囲
        assert state.hp_pct is not None
        assert 0.0 < state.hp_pct < 1.0

    def test_stats_all_six_correct_with_stats_templates(self) -> None:
        # #27 で stats スタイル digit を追加、stats も完全読み取り可能に
        templates = load_digit_templates(TEMPLATE_DIR)
        matcher = DigitMatcher(templates)
        reader = _legacy_reader(matcher)
        with Image.open(FIXTURE) as img:
            state = reader.read(img)
        assert state.stats == {
            "Vo": 226,
            "Da": 128,
            "Vi": 96,
            "Me": 178,
            "SP": 30,
            "Fans": 3775,
        }

    def test_all_fields_complete_match_with_full_pipeline(self) -> None:
        """D4: フル設定での全 7 フィールド回帰防止 anchor.

        `schedule_s2_w8_fans6225.png` から DigitMatcher + Tesseract +
        HP 色解析 すべてのパスで厳密一致を要求する。失敗したら
        座標 or 前処理 or テンプレートのいずれかが壊れた合図。
        """
        templates = load_digit_templates(TEMPLATE_DIR)
        matcher = DigitMatcher(templates)
        reader = _legacy_reader(matcher)
        with Image.open(FIXTURE) as img:
            state = reader.read(img)
        assert state.season == 2
        assert state.week_remaining == 8
        assert state.fans_to_target == 6225
        assert state.trouble_pct == 8
        assert state.tension_lv == 1
        assert state.stats == {
            "Vo": 226,
            "Da": 128,
            "Vi": 96,
            "Me": 178,
            "SP": 30,
            "Fans": 3775,
        }
        assert state.hp_pct is not None
        assert 0.40 < state.hp_pct < 0.55  # 観測値 0.478

    def test_tesseract_only_fallback_reads_at_least_week(self) -> None:
        """D4: DigitMatcher 不在でも Tesseract fallback で week_remaining は読める.

        装飾フォントの "8" は前処理 (アップスケール + 二値化) で
        Tesseract が認識できる。他の数字は誤認しがちなので None で
        ないことだけ確認する。
        """
        reader = _legacy_reader()  # digit_matcher なし
        with Image.open(FIXTURE) as img:
            state = reader.read(img)
        assert state.week_remaining == 8
        # season/fans は装飾フォントで誤認するが None ではない
        assert state.season is not None
        assert state.fans_to_target is not None
