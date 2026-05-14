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
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
