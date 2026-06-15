"""人力キャリブの粗い括りを、画面画像からゲーム canvas へ自動精緻化する。

2 点クリックは端がいい加減になりやすく、全 fractional 読取がズレる。
ここでは「粗 Region を外側に少し広げて全画面から見直し、ゲーム描画と
ブラウザ背景/レターボックス余白の境界を検出し、既知アスペクト
(canvas 1135x640 = 1.7734375 等) にスナップする」純関数を提供する。

設計の核:
- アスペクト比は厳密な既知定数。人力誤差の大半は端のズレなので、
  アスペクトスナップが最大レバレッジの補正。
- 周囲 (ページ背景/レターボックス) はほぼ一様で分散が低い。canvas は
  彩色・高分散。列/行ごとの「コンテンツらしさ (標準偏差)」プロファイル
  で中央の高分散帯 = canvas を切り出す。
- 端が不明瞭で信頼度が低い場合は生 Region にフォールバックする
  (誤検出で全読取を壊さない安全側)。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from mouse_core.region import Region


@dataclass(frozen=True)
class RefineReport:
    """精緻化の結果と、生キャリブからの補正量 (trust but verify 用)。"""

    refined: Region
    used_refinement: bool
    reason: str
    dx_left: float
    dy_top: float
    dx_right: float
    dy_bottom: float

    def summary(self) -> str:
        """1 行サマリ。CLI ログにそのまま出す想定。

        Returns:
            補正量を含む人間可読の 1 行。
        """
        if not self.used_refinement:
            return f"canvas 精緻化スキップ ({self.reason}); 手動 Region を使用"
        return (
            "canvas 精緻化: 手動からの補正 "
            f"L{self.dx_left:+.0f} T{self.dy_top:+.0f} "
            f"R{self.dx_right:+.0f} B{self.dy_bottom:+.0f} px "
            f"-> {self.refined.width:.0f}x{self.refined.height:.0f}"
        )


def _content_runs(profile: np.ndarray, threshold: float) -> list[tuple[int, int]]:
    """Profile が threshold 超の連続ランを返す。

    Returns:
        `(start, end)` 包含インデックスのリスト (左→右)。
    """
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for i, v in enumerate(profile):
        if v >= threshold and start is None:
            start = i
        elif v < threshold and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(profile) - 1))
    return runs


def _largest_run(profile: np.ndarray, threshold: float) -> tuple[int, int] | None:
    """最も長いコンテンツランを返す。

    Returns:
        最長ランの `(start, end)`。ランが無ければ None。
    """
    runs = _content_runs(profile, threshold)
    if not runs:
        return None
    return max(runs, key=lambda r: r[1] - r[0])


def refine_region_to_aspect(  # noqa: PLR0913
    screen: Image.Image,
    rough: Region,
    target_aspect: float,
    *,
    search_pad: float = 0.08,
    content_quantile: float = 0.35,
    min_content_frac: float = 0.40,
) -> RefineReport:
    """粗 Region を canvas へ精緻化する。

    Args:
        screen: 全画面キャプチャ (RGB)。
        rough: 人力 2 点クリックの粗 Region (スクリーン px)。
        target_aspect: canvas の width/height (例 1135/640)。
        search_pad: 粗 Region を外側に広げて見直す割合。
        content_quantile: 列/行プロファイルのしきい値を
            「最大値 * この比」で決める。
        min_content_frac: 検出コンテンツ幅/高が探索窓のこの比未満なら
            「境界が不明瞭」とみなしフォールバックする。

    Returns:
        `RefineReport`。精緻化に成功すれば `used_refinement=True` で
        補正済み Region、信頼度が低ければ生 `rough` を返す。
    """
    sw, sh = screen.width, screen.height
    pad_x = rough.width * search_pad
    pad_y = rough.height * search_pad
    sx0 = max(0, int(rough.left - pad_x))
    sy0 = max(0, int(rough.top - pad_y))
    sx1 = min(sw, int(rough.right + pad_x))
    sy1 = min(sh, int(rough.bottom + pad_y))
    if sx1 - sx0 < 20 or sy1 - sy0 < 20:
        return RefineReport(rough, False, "探索窓が小さすぎる", 0, 0, 0, 0)

    win = np.asarray(
        screen.crop((sx0, sy0, sx1, sy1)).convert("L"),
        dtype=np.float32,
    )
    # 列/行ごとの標準偏差 = コンテンツらしさ。背景/余白は一様で低い。
    col_std = win.std(axis=0)
    row_std = win.std(axis=1)
    # 一様画像 (ゲーム未表示/真っ黒等) は分散がほぼ無い。ここで弾かないと
    # threshold=0 で窓全体を誤検出するため絶対下限でフォールバック。
    min_abs_std = 5.0
    if col_std.max() < min_abs_std or row_std.max() < min_abs_std:
        return RefineReport(rough, False, "コンテンツ境界を検出できない", 0, 0, 0, 0)
    col_thr = float(col_std.max()) * content_quantile
    row_thr = float(row_std.max()) * content_quantile
    col_run = _largest_run(col_std, col_thr)
    row_run = _largest_run(row_std, row_thr)
    if col_run is None or row_run is None:
        return RefineReport(rough, False, "コンテンツ境界を検出できない", 0, 0, 0, 0)

    cw = col_run[1] - col_run[0] + 1
    ch = row_run[1] - row_run[0] + 1
    if cw < (sx1 - sx0) * min_content_frac or ch < (sy1 - sy0) * min_content_frac:
        return RefineReport(rough, False, "検出領域が不自然に小さい", 0, 0, 0, 0)

    det_left = sx0 + col_run[0]
    det_top = sy0 + row_run[0]
    det_cx = det_left + cw / 2.0
    det_cy = det_top + ch / 2.0

    # アスペクトスナップ: 検出ボックスを超えないよう、幅/高の小さい側に
    # 合わせて厳密アスペクトの最大矩形を中央に取る。
    final_w = min(float(cw), float(ch) * target_aspect)
    final_h = final_w / target_aspect
    left = det_cx - final_w / 2.0
    top = det_cy - final_h / 2.0
    refined = Region(
        left=left,
        top=top,
        right=left + final_w,
        bottom=top + final_h,
    )
    return RefineReport(
        refined=refined,
        used_refinement=True,
        reason="ok",
        dx_left=refined.left - rough.left,
        dy_top=refined.top - rough.top,
        dx_right=refined.right - rough.right,
        dy_bottom=refined.bottom - rough.bottom,
    )
