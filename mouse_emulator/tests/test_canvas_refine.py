"""`refine_region_to_aspect` のユニットテスト。

実機なし。合成「画面」(一様背景 + 既知アスペクトの高分散 canvas) に
雑な括りを与え、精緻化が真 canvas に収束しアスペクトが揃うこと、
境界が無い画像ではフォールバックすることを検証する。
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from mouse_core import Region, refine_region_to_aspect

ASPECT = 1135 / 640  # シャニマス canvas = 1.7734375


def _screen_with_canvas(
    canvas_box: tuple[int, int, int, int],
    size: tuple[int, int] = (1920, 1080),
) -> Image.Image:
    """一様グレー背景に、高分散ノイズの canvas を貼った合成画面。

    Returns:
        canvas 部分だけランダムノイズ (高分散)、外は一様な RGB 画像。
    """
    rng = np.random.default_rng(42)
    w, h = size
    arr = np.full((h, w, 3), 30, dtype=np.uint8)  # 暗い一様背景
    x0, y0, x1, y1 = canvas_box
    arr[y0:y1, x0:x1] = rng.integers(
        0, 256, size=(y1 - y0, x1 - x0, 3), dtype=np.uint8,
    )
    return Image.fromarray(arr)


class TestRefineConverges:
    def test_sloppy_bracket_snaps_to_true_canvas(self) -> None:
        # 真 canvas: 1135x640 アスペクト、画面中央付近
        true_box = (400, 220, 400 + 1135, 220 + 640)
        screen = _screen_with_canvas(true_box)
        # 雑な括り: 各辺を内/外に 20-35px ズラす
        rough = Region(left=378, top=242, right=1560, bottom=845)

        report = refine_region_to_aspect(screen, rough, ASPECT)

        assert report.used_refinement
        # アスペクトがほぼ目標
        assert abs(report.refined.width / report.refined.height - ASPECT) < 0.01
        # 真 canvas に各辺 ±12px で収束
        assert abs(report.refined.left - true_box[0]) <= 12
        assert abs(report.refined.top - true_box[1]) <= 12
        assert abs(report.refined.right - true_box[2]) <= 12
        assert abs(report.refined.bottom - true_box[3]) <= 12
        # 補正量がレポートに乗る
        assert report.dx_left != 0.0 or report.dy_top != 0.0

    def test_summary_mentions_correction(self) -> None:
        true_box = (300, 150, 300 + 1135, 150 + 640)
        screen = _screen_with_canvas(true_box)
        rough = Region(left=285, top=170, right=1450, bottom=780)
        report = refine_region_to_aspect(screen, rough, ASPECT)
        assert "canvas 精緻化" in report.summary()


class TestRefineFallback:
    def test_flat_image_falls_back_to_rough(self) -> None:
        # コンテンツ境界が無い一様画像 -> 精緻化せず rough を返す
        flat = Image.new("RGB", (1920, 1080), color=(30, 30, 30))
        rough = Region(left=400, top=220, right=1535, bottom=860)
        report = refine_region_to_aspect(flat, rough, ASPECT)
        assert not report.used_refinement
        assert report.refined == rough
        assert "スキップ" in report.summary()

    def test_tiny_window_falls_back(self) -> None:
        screen = _screen_with_canvas((10, 10, 30, 30), size=(100, 100))
        rough = Region(left=5, top=5, right=12, bottom=12)
        report = refine_region_to_aspect(screen, rough, ASPECT)
        assert not report.used_refinement
        assert report.refined == rough
