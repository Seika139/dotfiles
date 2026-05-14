"""プロデュース画面の単一フレームから `GameState` を組み立てる。

リージョン座標は 1512x805 CSS (DPR=2 で 3024x1610 PNG) の実機計測値を
fractional に正規化したもの。解像度が変わっても比率指定なので追従できる。
calibrate ヘルパでズレを再調整可能。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pytesseract  # type: ignore[import-untyped]
from PIL import Image

from auto_emulator.games.produce.state import (
    FractionalRegion,
    GameState,
    LessonOption,
    ScreenKind,
)


@dataclass(frozen=True)
class HeaderRegions:
    """画面上部のヘッダー領域。

    `schedule_s2_w8_fans6225.png` を元に初期キャリブレーション済み。
    新しい解像度で外れる場合は `tools/calibrate_produce.py` で再生成する。
    """

    season_digit: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.185, y=0.015, w=0.04, h=0.06),
    )
    week_remaining: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.250, y=0.015, w=0.05, h=0.06),
    )
    fans_to_target: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.405, y=0.010, w=0.130, h=0.075),
    )


@dataclass(frozen=True)
class LessonRegions:
    """スケジュール画面のレッスン/お仕事カード 6 枚分の座標。

    `card_centers_x` の長さがカード数を決める。各カードの name/level 領域は
    card_width とバンド (top/bottom) から動的に算出するので、座標を直接 6 回
    書く必要はない。
    """

    card_centers_x: tuple[float, ...] = (0.220, 0.353, 0.487, 0.620, 0.753, 0.887)
    card_width: float = 0.130
    name_band: tuple[float, float] = (0.860, 0.928)
    level_band: tuple[float, float] = (0.755, 0.815)
    level_width_ratio: float = 0.55


@dataclass(frozen=True)
class StatsRegions:
    """6 ステ表示行 (Vo/Da/Vi/Me/SP/Fans) の座標。

    スケジュール画面下部、プレビュー (+31 等) 直下に並ぶ 6 数値。
    """

    stat_centers_x: tuple[float, ...] = (
        0.155,
        0.265,
        0.375,
        0.485,
        0.595,
        0.730,
    )
    stat_width: float = 0.08
    stat_band: tuple[float, float] = (0.660, 0.710)
    labels: tuple[str, ...] = ("Vo", "Da", "Vi", "Me", "SP", "Fans")


@dataclass(frozen=True)
class StatusRegions:
    """体力バー / トラブル率 / テンション。

    `hp_bar` は OCR ではなくカラーピクセル比率で測る前提のため width が広め。
    """

    hp_bar: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.795, y=0.018, w=0.140, h=0.022),
    )
    trouble_pct: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.910, y=0.150, w=0.075, h=0.080),
    )
    tension_lv: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.853, y=0.055, w=0.040, h=0.040),
    )


_FANS_RE = re.compile(r"([0-9][0-9,]*)")
_INT_RE = re.compile(r"([0-9]+)")


class ProduceStateReader:
    """単一フレームから `GameState` を抽出する。

    Tesseract 日本語データ (`jpn`) が利用可能であることを前提とする。
    数値のみ抽出する場面では `eng` + 数字ホワイトリストで精度を上げる。
    """

    def __init__(
        self,
        *,
        header: HeaderRegions | None = None,
        lessons: LessonRegions | None = None,
        stats: StatsRegions | None = None,
        status: StatusRegions | None = None,
        tesseract_cmd: str | None = None,
    ) -> None:
        self._header = header or HeaderRegions()
        self._lessons = lessons or LessonRegions()
        self._stats = stats or StatsRegions()
        self._status = status or StatusRegions()
        if tesseract_cmd is not None:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    @property
    def lesson_regions(self) -> LessonRegions:
        return self._lessons

    @property
    def stat_regions(self) -> StatsRegions:
        return self._stats

    @property
    def status_regions(self) -> StatusRegions:
        return self._status

    def read(self, image: Image.Image) -> GameState:
        screen = self._detect_screen_kind(image)
        state = GameState(screen=screen)

        season = self._ocr_int(image, self._header.season_digit)
        week = self._ocr_int(image, self._header.week_remaining)
        fans = self._ocr_int_with_commas(image, self._header.fans_to_target)

        if season is not None and 1 <= season <= 4:
            state = state.model_copy(update={"season": season})
        if week is not None:
            state = state.model_copy(update={"week_remaining": week})
        if fans is not None:
            state = state.model_copy(update={"fans_to_target": fans})

        hp_pct = self.read_hp_pct(image)
        trouble = self.read_trouble_pct(image)
        tension = self._ocr_int(image, self._status.tension_lv)
        if hp_pct is not None:
            state = state.model_copy(update={"hp_pct": hp_pct})
        if trouble is not None:
            state = state.model_copy(update={"trouble_pct": trouble})
        if tension is not None:
            state = state.model_copy(update={"tension_lv": tension})

        stats = self.read_stats(image)
        if stats is not None:
            state = state.model_copy(update={"stats": stats})
        state.raw.update(
            {
                "header_season_text": self._ocr_text(
                    image,
                    self._header.season_digit,
                    digits_only=True,
                ),
                "header_week_text": self._ocr_text(
                    image,
                    self._header.week_remaining,
                    digits_only=True,
                ),
                "header_fans_text": self._ocr_text(
                    image,
                    self._header.fans_to_target,
                    digits_only=False,
                ),
            },
        )
        return state

    def _ocr_text(
        self,
        image: Image.Image,
        region: FractionalRegion,
        *,
        digits_only: bool,
    ) -> str:
        crop = self._crop(image, region)
        config_parts = ["--psm 7"]
        if digits_only:
            # cspell:ignore tessedit
            config_parts.append("-c tessedit_char_whitelist=0123456789,")
        config = " ".join(config_parts)
        try:
            text = pytesseract.image_to_string(crop, lang="eng", config=config)
        except (pytesseract.TesseractError, pytesseract.TesseractNotFoundError):
            return ""
        return str(text).strip()

    def _ocr_int(
        self,
        image: Image.Image,
        region: FractionalRegion,
    ) -> int | None:
        text = self._ocr_text(image, region, digits_only=True)
        match = _INT_RE.search(text)
        if match is None:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _ocr_int_with_commas(
        self,
        image: Image.Image,
        region: FractionalRegion,
    ) -> int | None:
        text = self._ocr_text(image, region, digits_only=True)
        match = _FANS_RE.search(text)
        if match is None:
            return None
        digits = match.group(1).replace(",", "")
        if not digits:
            return None
        try:
            return int(digits)
        except ValueError:
            return None

    @staticmethod
    def _crop(image: Image.Image, region: FractionalRegion) -> Image.Image:
        box = region.to_pixels(image.width, image.height)
        return image.crop(box).convert("L")

    @staticmethod
    def _detect_screen_kind(image: Image.Image) -> ScreenKind:
        """画面種別判定のスタブ。

        Phase 1 では呼び出し側でフィクスチャ種を分かっている前提のため、
        常に `unknown` を返す。Phase 2 でテンプレ判定を追加する。

        Returns:
            画面種別。Phase 1 では常に `"unknown"`。
        """
        del image
        return "unknown"

    def lessons_from_schedule(self, image: Image.Image) -> list[LessonOption]:
        """スケジュール画面下部のレッスン/お仕事カード 6 枚を抽出する。

        各カード単位で name (日本語 OCR) と level (数字 OCR) を読み取る。
        preview_fans は動的タップ前提のため Phase 3 まで `None` のまま。

        Returns:
            slot 0 (左端) から slot 5 (右端) 順の `LessonOption` リスト。
            OCR が失敗したカードは name="", level=1 のプレースホルダで返す。
        """
        options: list[LessonOption] = []
        for slot, (name_region, level_region) in enumerate(
            self.iter_lesson_regions(self._lessons),
        ):
            name = self._ocr_japanese(image, name_region)
            level = self._ocr_int(image, level_region) or 1
            options.append(
                LessonOption(
                    slot=slot,
                    name=name,
                    level=max(1, min(5, level)),
                    preview_fans=None,
                ),
            )
        return options

    @staticmethod
    def iter_lesson_regions(
        regions: LessonRegions,
    ) -> list[tuple[FractionalRegion, FractionalRegion]]:
        """各カードの (name_region, level_region) を順に返す。

        Returns:
            slot 0..N-1 順のリージョンペア。N は `len(card_centers_x)`。
        """
        pairs: list[tuple[FractionalRegion, FractionalRegion]] = []
        half_w = regions.card_width / 2
        name_top, name_bottom = regions.name_band
        level_top, level_bottom = regions.level_band
        level_half_w = (regions.card_width * regions.level_width_ratio) / 2
        for cx in regions.card_centers_x:
            name_region = FractionalRegion(
                x=cx - half_w,
                y=name_top,
                w=regions.card_width,
                h=name_bottom - name_top,
            )
            level_region = FractionalRegion(
                x=cx - level_half_w,
                y=level_top,
                w=level_half_w * 2,
                h=level_bottom - level_top,
            )
            pairs.append((name_region, level_region))
        return pairs

    def _ocr_japanese(
        self,
        image: Image.Image,
        region: FractionalRegion,
    ) -> str:
        """日本語混在テキストを読み取る (psm=7 single line)。

        Returns:
            OCR 結果。空白除去後の文字列。失敗時は空文字。
        """
        crop = self._crop(image, region)
        try:
            text = pytesseract.image_to_string(crop, lang="jpn", config="--psm 7")
        except (pytesseract.TesseractError, pytesseract.TesseractNotFoundError):
            return ""
        return str(text).strip().replace(" ", "")

    @staticmethod
    def iter_stat_regions(regions: StatsRegions) -> list[tuple[str, FractionalRegion]]:
        """6 ステ表示の (label, region) を順に返す。

        Returns:
            (Vo/Da/Vi/Me/SP/Fans, region) のペアのリスト。
        """
        pairs: list[tuple[str, FractionalRegion]] = []
        half_w = regions.stat_width / 2
        top, bottom = regions.stat_band
        for label, cx in zip(regions.labels, regions.stat_centers_x, strict=True):
            pairs.append(
                (
                    label,
                    FractionalRegion(
                        x=cx - half_w,
                        y=top,
                        w=regions.stat_width,
                        h=bottom - top,
                    ),
                ),
            )
        return pairs

    def read_stats(self, image: Image.Image) -> dict[str, int] | None:
        """6 ステ行を OCR で読み取り辞書化する。

        Returns:
            `{"Vo": 226, "Da": 128, ...}` 形式。全ステが読めなければ None。
        """
        result: dict[str, int] = {}
        for label, region in self.iter_stat_regions(self._stats):
            value = self._ocr_int_with_commas(image, region)
            if value is not None:
                result[label] = value
        if not result:
            return None
        return result

    def read_hp_pct(self, image: Image.Image) -> float | None:
        """HP バーの彩度ピクセル比率から残量を推定する。

        Returns:
            0.0 〜 1.0 の残量。バー領域に色がない場合は None。
        """
        crop_box = self._status.hp_bar.to_pixels(image.width, image.height)
        crop = image.crop(crop_box).convert("HSV")
        arr = np.asarray(crop)
        if arr.size == 0:
            return None
        saturated = arr[:, :, 1] > 80
        cols_with_color = saturated.any(axis=0)
        if cols_with_color.size == 0:
            return None
        ratio = float(cols_with_color.sum()) / float(cols_with_color.size)
        return max(0.0, min(1.0, ratio))

    def read_trouble_pct(self, image: Image.Image) -> int | None:
        """トラブル率バッジを OCR で読み取る。

        Returns:
            0-100 のパーセント値。読めない場合は None。
        """
        value = self._ocr_int(image, self._status.trouble_pct)
        if value is None:
            return None
        return max(0, min(100, value))
