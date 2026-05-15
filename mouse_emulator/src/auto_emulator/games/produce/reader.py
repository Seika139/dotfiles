"""プロデュース画面の単一フレームから `GameState` を組み立てる。

リージョン座標は **ゲーム canvas 領域** に対する fractional 値。
シャニマスは `<canvas width=1135 height=640>` (アスペクト ≈ 1.773) で
描画され、ブラウザ/ディスプレイによって canvas の外側に余白が付く。
そのためキャリブの基準はディスプレイ全体でも 16:9 でもなく **canvas
そのもの**。Phase 3 で実機 canvas 領域キャプチャ
(`tests/fixtures/produce/real_schedule_canvas.png`) を基準に再調整した。

重要: `produce-run` のキャリブ手順 (左上→右下クリック) は canvas の角
ぴったりを指す必要がある。余白を含めると全 fractional 座標がズレる。
ズレたら `tools/calibrate_produce.py overlay` で確認しながら再調整する。
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

    Phase 3 で実機 canvas 領域キャプチャ (`real_schedule_canvas.png`,
    2858x1608 ≈ canvas アスペクト 1.773) を基準に再キャリブ。旧 fixture
    (3024x1610, アスペクト 1.878) は canvas 外の余白を含み座標がズレる。

    注意: シャニマスの装飾フォントは vanilla Tesseract では誤認しやすく、
    座標が正しくても数値が常に正しいとは限らない。数字は DigitMatcher
    (cv2.matchTemplate) で補う設計。`fans_to_target` は "CLEAR!" 表示時は
    数字が無いため None になる (目標達成済みの正常系)。
    """

    season_digit: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.314, y=0.020, w=0.020, h=0.048),
    )
    week_remaining: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.350, y=0.008, w=0.066, h=0.080),
    )
    fans_to_target: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.620, y=0.028, w=0.085, h=0.045),
    )


@dataclass(frozen=True)
class LessonRegions:
    """スケジュール画面のレッスン/お仕事カード 6 枚分の座標。

    `card_centers_x` の長さがカード数を決める。各カードの name/level 領域は
    card_width とバンド (top/bottom) から動的に算出するので、座標を直接 6 回
    書く必要はない。
    """

    # Phase 3: 実機 canvas (`real_schedule_canvas.png`) を基準に再キャリブ。
    # card_centers_x の長さがカード数を決める。name/level 領域は card_width
    # とバンドから動的算出する。
    card_centers_x: tuple[float, ...] = (0.25, 0.39, 0.52, 0.65, 0.78, 0.91)
    card_width: float = 0.125
    name_band: tuple[float, float] = (0.715, 0.778)
    level_band: tuple[float, float] = (0.625, 0.672)
    level_width_ratio: float = 0.55
    # #40: 「+27/+6/+277」プレビューは選択中レッスン 1 枚分が stat 列に
    # 揃った固定位置に出る (per-card ではない)。最右の緑ピル "+277" が
    # ファン獲得見込み。単一フレームでは選択中カードの値しか取れない。
    selected_fans_preview: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(
            x=0.845, y=0.482, w=0.065, h=0.050,
        ),
    )


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

    スケジュール画面下部、プレビュー (+27 等) 直下に並ぶ 6 数値。
    Phase 3 で実機 canvas (`real_schedule_canvas.png`) を基準に再キャリブ。
    各ステは `[ステアイコン] [ランク E] / [数値]` の繰り返しで、数値だけを
    狙う。Fans は他より右、桁数が多い (例 13,775) ため width を共有。
    """

    stat_centers_x: tuple[float, ...] = (
        0.397,
        0.485,
        0.580,
        0.675,
        0.760,
        0.886,
    )
    stat_width: float = 0.055
    stat_band: tuple[float, float] = (0.552, 0.590)
    labels: tuple[str, ...] = ("Vo", "Da", "Vi", "Me", "SP", "Fans")


@dataclass(frozen=True)
class StatusRegions:
    """体力バー / トラブル率 / テンション。

    Phase 3 で実機 canvas (`real_schedule_canvas.png`) を基準に再キャリブ。
    `hp_bar` は OCR ではなくカラーピクセル比率で測る前提のため width が広め。
    `tension_lv` は「♡ Lv.N」の N (NEXT バッジの手前) を狙う。
    """

    hp_bar: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.795, y=0.018, w=0.140, h=0.022),
    )
    # トラブル率はピンクの星形バッジ内に**白文字**で出る大型数字。
    # Phase 3 で実機 canvas (`real_schedule_canvas.png`) の "8" を基準に
    # バッジ装飾 (白い星形の縁) を避け数字だけを囲うよう再キャリブ。
    trouble_pct: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(
            x=0.8947, y=0.2593, w=0.0255, h=0.0498,
        ),
    )
    tension_lv: FractionalRegion = field(
        default_factory=lambda: FractionalRegion(x=0.896, y=0.074, w=0.013, h=0.034),
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

        # 末尾 `_c` は実機 canvas 由来テンプレ (Phase 3)。旧 fixture 由来
        # (yellow_small/pink 等) と併用し、画像に合う方がマッチする。
        season = self._ocr_int(
            image,
            self._header.season_digit,
            styles=("season_cl", "season_c", "yellow_small", "pink"),
        )
        week = self._ocr_int(
            image,
            self._header.week_remaining,
            styles=("week_cl", "week_c", "yellow_large"),
        )
        # 0.68: マルチスケール化で "CLEAR!" 装飾が低スコアの幻桁を生む
        # ため、達成済み (数字なし→None) と実数 (例 6225) を分ける閾値。
        fans = self._ocr_int_with_commas(
            image,
            self._header.fans_to_target,
            styles=("pink",),
            matcher_threshold=0.68,
        )

        if season is not None and 1 <= season <= 4:
            state = state.model_copy(update={"season": season})
        if week is not None:
            state = state.model_copy(update={"week_remaining": week})
        if fans is not None:
            state = state.model_copy(update={"fans_to_target": fans})

        hp_pct = self.read_hp_pct(image)
        trouble = self.read_trouble_pct(image)
        tension = self._ocr_int(
            image,
            self._status.tension_lv,
            styles=("tension_c",),
        )
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

        右下 (fractional 0.85-0.91 / 0.90-0.95) の平均 RGB:
            schedule_lesson: マゼンタ系 (R>175, G<170, B>150) — 決定ボタン
            home:            グリーン系 (G>R+10 かつ G>B)    — 流行確認カード
            audition_battle: ダークグレー (RGB すべて 140 未満) — ステージ背景

        R 閾値は 200→175 に緩和。ライブ MSS キャプチャは macOS の
        screencapture より色が暗く (決定ボタン r≈188 vs 手動 r≈227)、
        r>200 だと screen=unknown になっていた。175 でも home/audition と
        は誤判定しないことを実機 + 全 fixture で確認済み。

        サンプル領域は実機 canvas 領域キャプチャ
        (`tests/fixtures/produce/real_*.png`) で決定ボタンの純マゼンタを
        捉える位置に調整済み (Phase 3)。fixture (3024x1610) は横長で
        アスペクト比が違うため旧座標 (0.81-0.88/0.91-0.96) からズレていた。

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

        br = arr[int(h * 0.90) : int(h * 0.95), int(w * 0.85) : int(w * 0.91)]
        if br.size == 0:
            return "unknown"
        r = float(br[:, :, 0].mean())
        g = float(br[:, :, 1].mean())
        b = float(br[:, :, 2].mean())

        if r > 175.0 and g < 170.0 and b > 150.0:
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

        各カード単位で name (日本語 OCR) と level (数字 OCR) を読み取る。
        `preview_fans` は #40 の知見により常に None: 実機 UI ではファン
        プレビューは選択中カード 1 枚分しか固定位置に出ず、6 カードぶんを
        単一フレームで取れない。選択中カードの値は `read()` が
        `GameState.selected_lesson_preview_fans` に詰める。

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

    def read_selected_lesson_preview_fans(
        self,
        image: Image.Image,
    ) -> int | None:
        """選択中レッスンの「+N」ファン獲得見込み (固定位置) を読む.

        緑ピル内の白文字数字。専用 digit テンプレ未整備なので Tesseract
        フォールバック頼みで、読めなければ None (graceful degradation)。

        Returns:
            プレビューのファン数、読めなければ None。
        """
        return self._ocr_int(image, self._lessons.selected_fans_preview)

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
                styles=("stats_cl", "stats_c", "stats"),
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
        """トラブル率バッジ (ピンク星形内の白文字) を読み取る。

        白文字onピンクは Tesseract も dark-on-light テンプレも素では
        当たらないため、明度しきい値で「濃い字on明るい背景」へ二値化
        してから DigitMatcher にかける。フォントはゲーム共通なので
        stats 系テンプレ + マルチスケール照合で解像度非依存に当たる。

        Returns:
            0-100 のパーセント値。読めない場合は None。
        """
        if self._digit_matcher is None:
            return None
        box = self._status.trouble_pct.to_pixels(image.width, image.height)
        gray = np.asarray(image.crop(box).convert("L"))
        if gray.size == 0:
            return None
        binarized = Image.fromarray(
            np.where(gray > 195, 0, 255).astype(np.uint8),
        )
        value = self._digit_matcher.read_number(
            binarized,
            styles=("stats_cl", "stats"),
            threshold=0.65,
        )
        if value is None:
            return None
        return max(0, min(100, value))
