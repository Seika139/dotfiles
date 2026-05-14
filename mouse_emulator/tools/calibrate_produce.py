"""プロデュース画面のリージョン/アクション座標を画像にオーバーレイする。

スクリーンショット PNG を入力し、`reader.py` で定義した全リージョン
(ヘッダー / レッスンカード / ステ / 体力 / トラブル / テンション) と
`actions.py` の全クリックポイント (ホーム / スケジュール / 戦闘 / 会話) を
矩形 + マーカー + ラベルで描き込んだ PNG を出力する。

使い方:
    .venv/bin/python tools/calibrate_produce.py \
        tests/fixtures/produce/schedule_s2_w8_fans6225.png \
        --out /tmp/calibrated.png
    open /tmp/calibrated.png  # 目視で位置ズレを確認

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="プロデュース画面のリージョン/アクション座標を描画",
    )
    parser.add_argument("input", type=Path, help="入力スクリーンショット PNG")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="出力 PNG パス (省略時は input と同階層に _calibrated.png)",
    )
    parser.add_argument(
        "--no-regions",
        action="store_true",
        help="リージョン矩形を描かない",
    )
    parser.add_argument(
        "--no-points",
        action="store_true",
        help="アクション座標マーカーを描かない",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        sys.stderr.write(f"file not found: {args.input}\n")
        return 2
    output_path = args.out or args.input.with_name(
        f"{args.input.stem}_calibrated.png",
    )
    with Image.open(args.input) as img:
        rendered = render(
            img,
            [] if args.no_regions else collect_regions(),
            [] if args.no_points else collect_points(),
        )
    rendered.save(output_path)
    sys.stdout.write(f"calibrated overlay saved: {output_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
