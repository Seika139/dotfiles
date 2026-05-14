"""`tools/calibrate_produce.py` の CLI サブコマンドの単体テスト。

`overlay` は既存フィクスチャで描画成功すること、`extract` と
`dump-regions` は意図した出力を出すことを軽量に検証する。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from tools.calibrate_produce import (
    collect_region_dump,
    main,
)

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "produce"
    / "schedule_s2_w8_fans6225.png"
)


class TestCollectRegionDump:
    def test_top_level_shape(self) -> None:
        data = collect_region_dump()
        assert set(data.keys()) == {"regions", "points"}

    def test_regions_categories(self) -> None:
        data = collect_region_dump()
        assert set(data["regions"].keys()) == {
            "header",
            "stats",
            "status",
            "lessons",
        }

    def test_points_categories(self) -> None:
        data = collect_region_dump()
        assert set(data["points"].keys()) == {
            "home",
            "schedule",
            "audition_battle",
            "dialog",
            "modal_dismiss",
            "item",
        }

    def test_dialog_includes_checkmark_choice(self) -> None:
        # E1.3 で追加した checkmark fallback が確実に含まれる
        data = collect_region_dump()
        assert "checkmark_choice" in data["points"]["dialog"]
        cm = data["points"]["dialog"]["checkmark_choice"]
        assert 0.0 <= cm["x"] <= 1.0
        assert 0.0 <= cm["y"] <= 1.0
        assert isinstance(cm["description"], str)

    def test_stats_by_label_has_six_entries(self) -> None:
        data = collect_region_dump()
        labels = data["regions"]["stats"]["by_label"]
        assert set(labels.keys()) == {"Vo", "Da", "Vi", "Me", "SP", "Fans"}


class TestDumpRegionsCli:
    def test_writes_json_to_file(self, tmp_path: Path) -> None:
        out = tmp_path / "regions.json"
        rc = main(["dump-regions", "--out", str(out)])
        assert rc == 0
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert "regions" in loaded
        assert "points" in loaded

    def test_writes_to_stdout_when_no_out(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = main(["dump-regions"])
        assert rc == 0
        captured = capsys.readouterr()
        loaded = json.loads(captured.out)
        assert "regions" in loaded


class TestExtractCli:
    def test_frac_crop_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "crop.png"
        rc = main(
            [
                "extract",
                str(FIXTURE),
                "--out",
                str(out),
                "--frac",
                "0.605,0.040,0.100,0.052",
            ],
        )
        assert rc == 0
        assert out.exists()
        with Image.open(out) as img:
            assert img.size[0] > 0
            assert img.size[1] > 0

    def test_px_crop_matches_frac_when_equivalent(self, tmp_path: Path) -> None:
        # 同等領域を fractional と pixel で指定し、サイズが一致するか
        with Image.open(FIXTURE) as img:
            width, height = img.size
        # fractional の (0.605, 0.040, 0.100, 0.052) と等価な pixel
        px_x = int(0.605 * width)
        px_y = int(0.040 * height)
        px_w = int(0.100 * width)
        px_h = int(0.052 * height)
        out_px = tmp_path / "px.png"
        rc = main(
            [
                "extract",
                str(FIXTURE),
                "--out",
                str(out_px),
                "--px",
                f"{px_x},{px_y},{px_w},{px_h}",
            ],
        )
        assert rc == 0
        with Image.open(out_px) as crop:
            assert crop.size[0] == px_w
            assert crop.size[1] == px_h

    def test_missing_input_returns_error(self, tmp_path: Path) -> None:
        rc = main(
            [
                "extract",
                str(tmp_path / "no_such.png"),
                "--out",
                str(tmp_path / "x.png"),
                "--frac",
                "0,0,0.1,0.1",
            ],
        )
        assert rc == 2

    def test_invalid_frac_returns_error(self, tmp_path: Path) -> None:
        rc = main(
            [
                "extract",
                str(FIXTURE),
                "--out",
                str(tmp_path / "x.png"),
                "--frac",
                "not,numbers,here,nope",
            ],
        )
        assert rc == 3

    def test_wrong_count_frac_returns_error(self, tmp_path: Path) -> None:
        rc = main(
            [
                "extract",
                str(FIXTURE),
                "--out",
                str(tmp_path / "x.png"),
                "--frac",
                "0.1,0.2,0.3",  # 3 値しかない
            ],
        )
        assert rc == 3


class TestOverlayCli:
    def test_overlay_creates_calibrated_png(self, tmp_path: Path) -> None:
        out = tmp_path / "cal.png"
        rc = main(
            [
                "overlay",
                str(FIXTURE),
                "--out",
                str(out),
            ],
        )
        assert rc == 0
        assert out.exists()
        with Image.open(out) as img:
            assert img.size[0] > 0
            assert img.size[1] > 0
