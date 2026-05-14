"""派生サブフィクスチャの存在 + 内容を検証する軽量テスト。

`tests/fixtures/produce/regions/` 配下の PNG は schedule fixture から
切り出した特定領域のスナップショット。サイズや channel が想定通りで
あるかを保証することで、フィクスチャ自体の回帰を検出する。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from auto_emulator.games.produce import (
    DigitMatcher,
    load_digit_templates,
)

REGIONS_DIR = Path(__file__).parent / "fixtures" / "produce" / "regions"


class TestSubFixturesExist:
    def test_header_band_size(self) -> None:
        with Image.open(REGIONS_DIR / "header_band.png") as img:
            assert img.size == (3024, 160)

    def test_stats_row_size(self) -> None:
        with Image.open(REGIONS_DIR / "stats_row.png") as img:
            assert img.size == (1800, 70)

    def test_fans_only_size(self) -> None:
        with Image.open(REGIONS_DIR / "fans_only.png") as img:
            assert img.size == (350, 85)

    def test_trouble_badge_size(self) -> None:
        with Image.open(REGIONS_DIR / "trouble_badge.png") as img:
            assert img.size == (424, 500)

    def test_hp_bar_region_size(self) -> None:
        with Image.open(REGIONS_DIR / "hp_bar_region.png") as img:
            assert img.size == (520, 80)


class TestFansOnlyDigitReadable:
    """サブフィクスチャ単独で DigitMatcher が動くことを確認する例。"""

    def test_reads_6225_from_isolated_fans_crop(self) -> None:
        templates = load_digit_templates(REGIONS_DIR.parent / "digits")
        matcher = DigitMatcher(templates)
        with Image.open(REGIONS_DIR / "fans_only.png") as img:
            number = matcher.read_number(img, styles=("pink",))
        assert number == 6225
