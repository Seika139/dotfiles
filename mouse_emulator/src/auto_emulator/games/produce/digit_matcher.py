"""数字テンプレートマッチで装飾フォントを誤認なく読む。

Tesseract が苦手とするゲームフォント (シーズン badge / week 黄色大型 /
fans ピンク) を、digit 0-9 のテンプレートを `cv2.matchTemplate` で
照合することで識別する。OCR より高速かつ装飾の有無に影響されない。

使い方:
    templates = [DigitTemplate(digit=2, pattern=np_array_of_2), ...]
    matcher = DigitMatcher(templates)
    number = matcher.read_number(small_image_with_digits)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from operator import itemgetter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class DigitTemplate:
    """1 つの digit テンプレート。

    `pattern` はグレースケール 2D numpy 配列 (uint8)。複数サイズや
    複数スタイル (大型黄色 / 小型 / pink) を区別したい場合は
    同じ digit に対して別個の `DigitTemplate` を持たせる。
    """

    digit: int
    pattern: np.ndarray
    style: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.digit <= 9:
            msg = f"digit must be 0-9, got {self.digit}"
            raise ValueError(msg)
        if self.pattern.ndim != 2:
            msg = f"pattern must be 2D grayscale, got {self.pattern.shape}"
            raise ValueError(msg)


_TEMPLATE_FILENAME_RE = re.compile(r"^([0-9])(?:_(.+))?\.png$", re.IGNORECASE)


def load_digit_templates(directory: Path) -> list[DigitTemplate]:
    """ディレクトリ内の `{digit}_{style}.png` を全てロードする。

    ファイル名の先頭 1 文字が digit (0-9)、続く `_{style}` は任意。
    例: `6_pink.png` / `8_yellow_large.png` / `2.png`。

    Args:
        directory: テンプレート PNG が入ったディレクトリ。

    Returns:
        ロードされたテンプレートのリスト (ファイル名昇順)。
        該当ファイルがなければ空リスト。
    """
    if not directory.is_dir():
        return []
    templates: list[DigitTemplate] = []
    for path in sorted(directory.iterdir()):
        match = _TEMPLATE_FILENAME_RE.match(path.name)
        if match is None:
            continue
        digit = int(match.group(1))
        style = match.group(2) or ""
        with Image.open(path) as img:
            pattern = np.asarray(img.convert("L"), dtype=np.uint8)
        templates.append(DigitTemplate(digit=digit, pattern=pattern, style=style))
    return templates


def extract_template(
    image: Image.Image,
    box: tuple[int, int, int, int],
    digit: int,
    style: str = "",
) -> DigitTemplate:
    """フィクスチャ画像の指定矩形から digit テンプレートを切り出す。

    Args:
        image: 元画像。
        box: クロップ範囲 `(left, top, right, bottom)` (PNG ピクセル)。
        digit: この矩形が表す数字 0-9。
        style: 任意ラベル (例: "small_yellow", "pink") - 同じ digit を
            別スタイルで複数登録するときの識別子。

    Returns:
        `DigitTemplate` インスタンス。
    """
    crop = image.crop(box).convert("L")
    pattern = np.asarray(crop, dtype=np.uint8)
    return DigitTemplate(digit=digit, pattern=pattern, style=style)


class DigitMatcher:
    """digit 0-9 テンプレートの集合で画像から数字列を読む。"""

    def __init__(
        self,
        templates: list[DigitTemplate],
        *,
        threshold: float = 0.6,
        nms_overlap_ratio: float = 0.5,
    ) -> None:
        """Constructor.

        Args:
            templates: 1 つ以上のテンプレート。同じ digit を複数登録可。
            threshold: matchTemplate スコア (TM_CCOEFF_NORMED 0.0-1.0)
                の最低値。これ未満は無視。
            nms_overlap_ratio: テンプレ幅のこの比率以内の重なりは同じ
                digit と見做して上位スコアを残す (Non-Max Suppression)。

        Raises:
            ValueError: テンプレートが空の場合。
        """
        if not templates:
            msg = "DigitMatcher requires at least one template"
            raise ValueError(msg)
        self._templates = list(templates)
        self._threshold = threshold
        self._nms_overlap_ratio = nms_overlap_ratio

    def find_digits(self, image: Image.Image) -> list[tuple[int, int, float]]:
        """画像内にマッチした digit を `(x, digit, score)` で返す。

        Args:
            image: 検索対象画像 (PIL Image)。

        Returns:
            左 x 昇順にソート済み。重なりは NMS で 1 つに統合。
        """
        arr = np.asarray(image.convert("L"), dtype=np.uint8)
        candidates: list[tuple[int, int, float, int]] = []
        for tmpl in self._templates:
            if tmpl.pattern.shape[0] > arr.shape[0]:
                continue
            if tmpl.pattern.shape[1] > arr.shape[1]:
                continue
            result = cv2.matchTemplate(arr, tmpl.pattern, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= self._threshold)
            for y, x in zip(*locations, strict=False):
                score = float(result[y, x])
                candidates.append((int(x), tmpl.digit, score, tmpl.pattern.shape[1]))
        candidates.sort(key=lambda c: -c[2])
        accepted: list[tuple[int, int, float, int]] = []
        for cand in candidates:
            x, _, _, width = cand
            keep = True
            for ax, _, _, aw in accepted:
                if abs(x - ax) < max(width, aw) * self._nms_overlap_ratio:
                    keep = False
                    break
            if keep:
                accepted.append(cand)
        accepted.sort(key=itemgetter(0))
        return [(x, d, s) for x, d, s, _ in accepted]

    def read_number(self, image: Image.Image) -> int | None:
        """画像内の数字列を 1 つの整数として返す。

        Returns:
            検出できれば int、何もマッチしなければ None。
        """
        matches = self.find_digits(image)
        if not matches:
            return None
        digits = "".join(str(d) for _, d, _ in matches)
        try:
            return int(digits)
        except ValueError:
            return None
