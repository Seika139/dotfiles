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

from auto_emulator.games.produce.digit_matcher import DigitMatcher
from auto_emulator.games.produce.state import (
    FractionalRegion,
    GameState,
    LessonOption,
    ScreenKind,
)


@dataclass(frozen=True)
class HeaderRegions:
    """画面上部のヘッダー領域。

    `schedule_s2_w8_fans6225.png` (3024x1610, 1512x805 CSS) を元に
    キャリブレーション済み (#6 で実 OCR 検証)。新しい解像度で外れる
    場合は `tools/calibrate_produce.py` で再生成する。

    注意: シャニマスの装飾フォントは vanilla Tesseract では誤認しやすく
    ("2"→"4", "8"→"8" 安定, "6,225"→"9965" など)、座標が正しくても
    数値が常に正しいとは限らない。長期的には数字テンプレートマッチ
    (cv2.matchTemplate でゴールデン digits を 0-9 ぶん用意) への置換を
    想定する。
    """

    season_digit: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.334, y=0.009, w=0.022, h=0.038),
    )
    week_remaining: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.393, y=0.019, w=0.043, h=0.075),
    )
    fans_to_target: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.605, y=0.040, w=0.100, h=0.052),
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
    # G3: ファン獲得見込み (`+277` 等) のプレビュー帯。レッスンカード右上に
    # 表示される 3 値のうち最右が fans。`+` を含むので OCR は数字のみ抽出する。
    # 実機 fixture 未取得のため値は推定。calibrate_produce で要確認。
    fans_band: tuple[float, float] = (0.690, 0.745)
    fans_width_ratio: float = 0.55


@dataclass(frozen=True)
class AuditionRegions:
    """オーディションタブで中央に見えているカード名の領域 (G2).

    スワイプで切り替えるカードのうち、画面中央 (≒ slot 0 で確定タップが
    効く位置) のオーディション名を読み取る。`target_audition_name` と
    前方一致したら swipe を打ち切るのに使う。

    実機 fixture 未取得のため値は推定。`calibrate_produce overlay` で確認。
    """

    center_card_name: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.330, y=0.640, w=0.330, h=0.070),
    )


@dataclass(frozen=True)
class StatsRegions:
    """6 ステ表示行 (Vo/Da/Vi/Me/SP/Fans) の座標。

    スケジュール画面下部、プレビュー (+31 等) 直下に並ぶ 6 数値。
    `schedule_s2_w8_fans6225.png` でキャリブ済み (#25)。
    Fans 数値は他のステより少し右寄り (アイコンのため)。
    """

    stat_centers_x: tuple[float, ...] = (
        0.399,
        0.490,
        0.583,
        0.671,
        0.744,
        0.870,
    )
    stat_width: float = 0.05
    stat_band: tuple[float, float] = (0.546, 0.585)
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
        default_factory=lambda: FractionalRegion(x=0.866, y=0.255, w=0.050, h=0.063),
    )
    tension_lv: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.878, y=0.066, w=0.014, h=0.028),
    )


_FANS_RE = re.compile(r"([0-9][0-9,]*)")
_INT_RE = re.compile(r"([0-9]+)")


class ProduceStateReader:
    """単一フレームから `GameState` を抽出する。

    Tesseract 日本語データ (`jpn`) が利用可能であることを前提とする。
    数値のみ抽出する場面では `eng` + 数字ホワイトリストで精度を上げる。
    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        header: HeaderRegions | None = None,
        lessons: LessonRegions | None = None,
        stats: StatsRegions | None = None,
        status: StatusRegions | None = None,
        auditions: AuditionRegions | None = None,
        digit_matcher: DigitMatcher | None = None,
        tesseract_cmd: str | None = None,
    ) -> None:
        self._header = header or HeaderRegions()
        self._lessons = lessons or LessonRegions()
        self._stats = stats or StatsRegions()
        self._status = status or StatusRegions()
        self._auditions = auditions or AuditionRegions()
        self._digit_matcher = digit_matcher
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

    @property
    def audition_regions(self) -> AuditionRegions:
        return self._auditions

    def read_current_audition_name(self, image: Image.Image) -> str:
        """G2: スワイプ中に画面中央のオーディションカード名を OCR で読み取る.

        OCR が失敗した場合は空文字を返す (engine 側は fallback で固定 swipe
        を続ける)。

        Returns:
            OCR で抽出した日本語混じり名 (空白除去後)、失敗時は ""。
        """
        return self._ocr_japanese(image, self._auditions.center_card_name)

    def read(self, image: Image.Image) -> GameState:
        screen = self._detect_screen_kind(image)
        state = GameState(screen=screen)

        season = self._ocr_int(
            image,
            self._header.season_digit,
            styles=("yellow_small", "pink"),
        )
        week = self._ocr_int(
            image,
            self._header.week_remaining,
            styles=("yellow_large",),
        )
        fans = self._ocr_int_with_commas(
            image,
            self._header.fans_to_target,
            styles=("pink",),
        )

        if season is not None and 1 <= season <= 4:
            state = state.model_copy(update={"season": season})
        if week is not None:
            state = state.model_copy(update={"week_remaining": week})
        if fans is not None:
            state = state.model_copy(update={"fans_to_target": fans})

        hp_pct = self.read_hp_pct(image)
        trouble = self.read_trouble_pct(image)
        tension = self._ocr_int(image, self._status.tension_lv)  # Tesseract 経路
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
        # 装飾フォント対策: 3 倍アップスケール + 二値化で Tesseract の認識率を上げる。
        # それでもシャニマス UI の "2" / "6,225" 等は誤認するため、上位の決定
        # ロジックは OCR の値を「指標」として扱い、厳密一致は期待しない。
        crop = self._crop(image, region)
        big = crop.resize((crop.width * 3, crop.height * 3), Image.LANCZOS)
        binarized = big.point(lambda v: 0 if v < 160 else 255)
        config_parts = ["--psm 7"]
        if digits_only:
            # cspell:ignore tessedit
            config_parts.append("-c tessedit_char_whitelist=0123456789,")
        config = " ".join(config_parts)
        try:
            text = pytesseract.image_to_string(
                binarized,
                lang="eng",
                config=config,
            )
        except (pytesseract.TesseractError, pytesseract.TesseractNotFoundError):
            return ""
        return str(text).strip()

    def _ocr_int(
        self,
        image: Image.Image,
        region: FractionalRegion,
        *,
        styles: tuple[str, ...] | None = None,
    ) -> int | None:
        if self._digit_matcher is not None:
            crop = image.crop(region.to_pixels(image.width, image.height))
            matched = self._digit_matcher.read_number(crop, styles=styles)
            if matched is not None:
                return matched
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
        *,
        styles: tuple[str, ...] | None = None,
        matcher_threshold: float | None = None,
    ) -> int | None:
        if self._digit_matcher is not None:
            crop = image.crop(region.to_pixels(image.width, image.height))
            matched = self._digit_matcher.read_number(
                crop,
                styles=styles,
                threshold=matcher_threshold,
            )
            if matched is not None:
                return matched
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
    def detect_screen_kind(image: Image.Image) -> ScreenKind:
        """画面種別を右下コーナーの色 signature で識別する。

        右下 (fractional 0.81-0.88 / 0.91-0.96) の平均 RGB:
            schedule_lesson: マゼンタ系 (R>200, G<170, B>150) — 決定ボタン
            home:            グリーン系 (G>R+10 かつ G>B)    — 流行確認カード
            audition_battle: ダークグレー (RGB すべて 140 未満) — ステージ背景

        `schedule_audition` / `dialog` / `result` は signature 未整理のため
        現状 unknown を返す。新しい画面を識別したいときは
        `tools/calibrate_produce.py` で右下色をサンプルしてから条件を追加する。

        Returns:
            判定された画面種別。識別できない場合は `"unknown"`。
        """
        arr = np.asarray(image.convert("RGB"))
        h, w = arr.shape[:2]
        if h < 10 or w < 10:
            return "unknown"

        br = arr[int(h * 0.91) : int(h * 0.96), int(w * 0.81) : int(w * 0.88)]
        if br.size == 0:
            return "unknown"
        r = float(br[:, :, 0].mean())
        g = float(br[:, :, 1].mean())
        b = float(br[:, :, 2].mean())

        if r > 200.0 and g < 170.0 and b > 150.0:
            return "schedule_lesson"
        if g > r + 10.0 and g > b:
            return "home"
        if r < 140.0 and g < 140.0 and b < 140.0:
            return "audition_battle"
        return "unknown"

    @staticmethod
    def _detect_screen_kind(image: Image.Image) -> ScreenKind:
        """互換用エイリアス。Phase 5b までの呼び出しを壊さないため残す。

        Returns:
            `detect_screen_kind` への委譲結果。
        """
        return ProduceStateReader.detect_screen_kind(image)

    def lessons_from_schedule(self, image: Image.Image) -> list[LessonOption]:
        """スケジュール画面下部のレッスン/お仕事カード 6 枚を抽出する。

        各カード単位で name (日本語 OCR) と level (数字 OCR) を読み取り、
        G3 でファン獲得プレビュー (`+277` の数字部分) も同時に読み取る。
        テンプレート/OCR が失敗したカードは `preview_fans=None` のまま。

        Returns:
            slot 0 (左端) から slot 5 (右端) 順の `LessonOption` リスト。
            OCR が失敗したカードは name="", level=1 のプレースホルダで返す。
        """
        options: list[LessonOption] = []
        fans_regions = self.iter_lesson_fans_regions(self._lessons)
        for slot, (name_region, level_region) in enumerate(
            self.iter_lesson_regions(self._lessons),
        ):
            name = self._ocr_japanese(image, name_region)
            level = self._ocr_int(image, level_region) or 1
            # G3: preview_fans は読めない (テンプレ不足/OCR 失敗) なら None
            # に倒し、Strategy 側はその場合 fans 効率比較を skip する設計。
            raw_fans = self._ocr_int(image, fans_regions[slot])
            preview_fans = raw_fans if raw_fans is not None and raw_fans >= 0 else None
            options.append(
                LessonOption(
                    slot=slot,
                    name=name,
                    level=max(1, min(5, level)),
                    preview_fans=preview_fans,
                ),
            )
        return options

    @staticmethod
    def iter_lesson_fans_regions(
        regions: LessonRegions,
    ) -> list[FractionalRegion]:
        """各カードの fans プレビュー領域 (G3) を slot 順で返す.

        Returns:
            slot 0..N-1 順の `FractionalRegion` リスト。
        """
        fans_top, fans_bottom = regions.fans_band
        fans_half_w = (regions.card_width * regions.fans_width_ratio) / 2
        return [
            FractionalRegion(
                x=cx - fans_half_w,
                y=fans_top,
                w=fans_half_w * 2,
                h=fans_bottom - fans_top,
            )
            for cx in regions.card_centers_x
        ]

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
            value = self._ocr_int_with_commas(
                image,
                region,
                styles=("stats",),
                matcher_threshold=0.80,
            )
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
        value = self._ocr_int(
            image,
            self._status.trouble_pct,
            styles=("yellow_large", "pink"),
        )
        if value is None:
            return None
        return max(0, min(100, value))
