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
    extract_template,
)

FIXTURE = Path(__file__).parent / "fixtures" / "produce" / "schedule_s2_w8_fans6225.png"


def _load_pink_templates() -> tuple[DigitTemplate, DigitTemplate, DigitTemplate]:
    """フィクスチャの "6,225" から digit 6 / 2 / 5 をピンクスタイルで抽出。"""
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
