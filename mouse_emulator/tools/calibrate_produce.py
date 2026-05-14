r"""プロデュース画面のキャリブツール (`overlay` / `extract` / `dump-regions`)。

サブコマンド:

- `overlay`  : スクショに全リージョン矩形 + クリックポイントを描き込む。
- `extract`  : スクショの指定領域を crop して PNG として保存
                 (digit テンプレート補充用)。
- `dump-regions` : 現コード定義の全 fractional リージョンを JSON 出力。

使い方:
    .venv/bin/python tools/calibrate_produce.py overlay \\
        tests/fixtures/produce/schedule_s2_w8_fans6225.png \\
        --out /tmp/calibrated.png

ズレていたら `reader.HeaderRegions` などのデフォルト値を編集し、
再度ツールを走らせて反復する。Tesseract 不要。
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from auto_emulator.games.produce.actions import (
    AUDITION_BATTLE_POINTS,
    DIALOG_POINTS,
    HOME_POINTS,
    SCHEDULE_POINTS,
    Point,
)
from auto_emulator.games.produce.reader import (
    HeaderRegions,
    LessonRegions,
    ProduceStateReader,
    StatsRegions,
    StatusRegions,
)
from auto_emulator.games.produce.state import FractionalRegion


@dataclass(frozen=True)
class LabeledRegion:
    label: str
    region: FractionalRegion
    color: str


@dataclass(frozen=True)
class LabeledPoint:
    label: str
    point: Point
    color: str


def collect_regions() -> list[LabeledRegion]:
    header = HeaderRegions()
    stats = StatsRegions()
    status = StatusRegions()
    lessons = LessonRegions()
    items: list[LabeledRegion] = [
        LabeledRegion("season", header.season_digit, "#ff3366"),
        LabeledRegion("week", header.week_remaining, "#ff3366"),
        LabeledRegion("fans", header.fans_to_target, "#ff3366"),
        LabeledRegion("hp_bar", status.hp_bar, "#33ccff"),
        LabeledRegion("trouble", status.trouble_pct, "#33ccff"),
        LabeledRegion("tension", status.tension_lv, "#33ccff"),
    ]
    items.extend(
        LabeledRegion(f"stat:{label}", region, "#66ff66")
        for label, region in ProduceStateReader.iter_stat_regions(stats)
    )
    for slot, (name_region, level_region) in enumerate(
        ProduceStateReader.iter_lesson_regions(lessons),
    ):
        items.extend(
            (
                LabeledRegion(f"lesson{slot}:name", name_region, "#ffaa00"),
                LabeledRegion(f"lesson{slot}:lv", level_region, "#cc8800"),
            ),
        )
    return items


def collect_points() -> list[LabeledPoint]:
    home = HOME_POINTS
    schedule = SCHEDULE_POINTS
    battle = AUDITION_BATTLE_POINTS
    dialog = DIALOG_POINTS
    return [
        LabeledPoint("home:produce", home.produce_card, "#9933ff"),
        LabeledPoint("home:rest", home.rest_card, "#9933ff"),
        LabeledPoint("home:reflection", home.reflection_card, "#9933ff"),
        LabeledPoint("home:trend", home.trend_card, "#9933ff"),
        LabeledPoint("home:rest_ok", home.rest_confirm, "#bb66ff"),
        LabeledPoint("sched:lesson_tab", schedule.lesson_tab, "#ff66cc"),
        LabeledPoint("sched:audition_tab", schedule.audition_tab, "#ff66cc"),
        LabeledPoint("sched:confirm", schedule.confirm_button, "#ff66cc"),
        LabeledPoint("sched:back", schedule.back_button, "#ff66cc"),
        LabeledPoint("sched:reflection", schedule.reflection_button, "#ff66cc"),
        LabeledPoint("battle:auto", battle.auto_toggle, "#00ccaa"),
        LabeledPoint("battle:speed", battle.speed_toggle, "#00ccaa"),
        LabeledPoint("battle:pause", battle.pause_button, "#00ccaa"),
        LabeledPoint("dialog:ff", dialog.fast_forward_toggle, "#ffcc00"),
        LabeledPoint("dialog:yellow", dialog.choice_yellow, "#ffcc00"),
        LabeledPoint("dialog:advance", dialog.advance_safe, "#ffcc00"),
    ]


def render(
    image: Image.Image,
    regions: list[LabeledRegion],
    points: list[LabeledPoint],
) -> Image.Image:
    output = image.convert("RGBA").copy()
    draw = ImageDraw.Draw(output)
    width, height = output.size
    stroke = max(2, width // 400)
    radius = max(8, min(width, height) // 150)
    label_offset = max(6, stroke * 2)
    for item in regions:
        box = item.region.to_pixels(width, height)
        draw.rectangle(box, outline=item.color, width=stroke)
        draw.text(
            (box[0] + label_offset, box[1] + label_offset),
            item.label,
            fill=item.color,
        )
    for marker in points:
        cx = int(marker.point.x * width)
        cy = int(marker.point.y * height)
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=marker.color,
            width=stroke,
        )
        draw.text(
            (cx + radius + label_offset, cy - radius),
            marker.label,
            fill=marker.color,
        )
    return output


def _parse_box4(spec: str) -> tuple[float, float, float, float]:
    """`x,y,w,h` 4 値の文字列を float タプルへ変換する。

    Args:
        spec: カンマ区切り 4 値の文字列 (例: "0.605,0.040,0.100,0.052")。

    Returns:
        (x, y, w, h) の float タプル。

    Raises:
        ValueError: 値が 4 個でない、または数値解釈に失敗したとき。
    """
    parts = [p.strip() for p in spec.split(",")]
    expected = 4
    if len(parts) != expected:
        raise ValueError(
            f"expected 4 comma-separated values, got {len(parts)}: {spec!r}",
        )
    x, y, w, h = (float(p) for p in parts)
    return x, y, w, h


def cmd_extract(args: argparse.Namespace) -> int:
    """`extract` サブコマンド: スクショの指定領域を crop して保存。

    digit テンプレートの補充用。`--frac` (fractional) または `--px`
    (ピクセル) で領域を指定し、入力 PNG から切り出して `--out` に保存する。

    Returns:
        終了コード (0 成功, 2 入力ファイル不在, 3 引数不正)。
    """
    input_path: Path = args.input
    if not input_path.exists():
        sys.stderr.write(f"file not found: {input_path}\n")
        return 2
    output_path: Path = args.out
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as img:
        width, height = img.size
        if args.frac is not None:
            try:
                fx, fy, fw, fh = _parse_box4(args.frac)
            except ValueError as e:
                sys.stderr.write(f"--frac parse error: {e}\n")
                return 3
            region = FractionalRegion(x=fx, y=fy, w=fw, h=fh)
            box = region.to_pixels(width, height)
        else:
            try:
                px, py, pw, ph = _parse_box4(args.px)
            except ValueError as e:
                sys.stderr.write(f"--px parse error: {e}\n")
                return 3
            box = (int(px), int(py), int(px + pw), int(py + ph))
        crop = img.crop(box)
        crop.save(output_path)
    sys.stdout.write(
        f"crop saved: {output_path} (box={box}, size={crop.size})\n",
    )
    return 0


def _build_extract_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "extract",
        help="スクショの指定領域を crop して PNG として保存 (digit テンプレ補充)",
    )
    p.add_argument("input", type=Path, help="入力スクリーンショット PNG")
    p.add_argument(
        "--out",
        type=Path,
        required=True,
        help="出力 PNG パス (例: tests/fixtures/produce/digits/4_pink.png)",
    )
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument(
        "--frac",
        type=str,
        default=None,
        help="fractional 領域 (0.0-1.0): 'x,y,w,h' (例: '0.605,0.040,0.100,0.052')",
    )
    grp.add_argument(
        "--px",
        type=str,
        default=None,
        help="ピクセル領域: 'x,y,w,h' (例: '1900,80,300,80')",
    )
    p.set_defaults(func=cmd_extract)


def cmd_overlay(args: argparse.Namespace) -> int:
    """`overlay` サブコマンド: スクショに矩形 + マーカーを描画。

    Returns:
        終了コード (0 成功, 2 入力ファイル不在)。
    """
    input_path: Path = args.input
    if not input_path.exists():
        sys.stderr.write(f"file not found: {input_path}\n")
        return 2
    output_path: Path = args.out or input_path.with_name(
        f"{input_path.stem}_calibrated.png",
    )
    with Image.open(input_path) as img:
        rendered = render(
            img,
            [] if args.no_regions else collect_regions(),
            [] if args.no_points else collect_points(),
        )
    rendered.save(output_path)
    sys.stdout.write(f"calibrated overlay saved: {output_path}\n")
    return 0


def _build_overlay_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "overlay",
        help="スクショに全リージョン/アクション座標を描き込む",
    )
    p.add_argument("input", type=Path, help="入力スクリーンショット PNG")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="出力 PNG パス (省略時は input と同階層に _calibrated.png)",
    )
    p.add_argument(
        "--no-regions",
        action="store_true",
        help="リージョン矩形を描かない",
    )
    p.add_argument(
        "--no-points",
        action="store_true",
        help="アクション座標マーカーを描かない",
    )
    p.set_defaults(func=cmd_overlay)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="プロデュース画面のキャリブツール (overlay/extract/dump-regions)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    _build_overlay_parser(sub)
    _build_extract_parser(sub)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
