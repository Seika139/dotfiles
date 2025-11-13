from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pytest
from PIL import Image

from auto_emulator import cli
from mouse_core import display
from mouse_core.region import Region


class _DummyCaptureService:
    def __init__(
        self,
        *,
        should_raise: bool = False,
        width: int = 100,
        height: int = 80,
    ) -> None:
        self.should_raise = should_raise
        self.width = width
        self.height = height

    def capture(self, region: Region | None = None) -> Image.Image:
        del region
        if self.should_raise:
            raise RuntimeError("capture failed")
        return Image.new("RGB", (self.width, self.height))


@pytest.mark.parametrize(
    ("bounds", "expected"),
    [
        ((0.0, 0.0, 1920.0, 1080.0), True),
        ((0.0, 0.0, 1920.0, 1080.0), False),
        (None, False),
    ],
)
def test_is_region_within_displays(
    monkeypatch: pytest.MonkeyPatch,
    bounds: tuple[float, float, float, float] | None,
    expected: bool,
) -> None:
    region = Region(left=100.0, top=100.0, right=500.0, bottom=500.0)
    if bounds is not None and not expected:
        region = Region(
            left=bounds[2] + 10.0,
            top=bounds[3] + 10.0,
            right=bounds[2] + 20.0,
            bottom=bounds[3] + 20.0,
        )

    def fake_bounds() -> tuple[float, float, float, float] | None:
        return bounds

    monkeypatch.setattr(display, "get_display_bounds", fake_bounds)
    monkeypatch.setattr(
        display,
        "_region_to_nss_bounds",
        lambda region: (
            region.left,
            min(region.top, region.bottom),
            region.right,
            max(region.top, region.bottom),
        ),
    )
    assert display.is_region_within_displays(region) is expected


def test_is_region_within_displays_multiscreen(monkeypatch: pytest.MonkeyPatch) -> None:
    @dataclass(slots=True)
    class _Point:
        x: float
        y: float

    @dataclass(slots=True)
    class _Size:
        width: float
        height: float

    @dataclass(slots=True)
    class _Frame:
        origin: _Point
        size: _Size

    @dataclass(slots=True)
    class _Screen:
        _frame: _Frame

        @classmethod
        def from_values(
            cls,
            origin: tuple[float, float],
            size: tuple[float, float],
        ) -> _Screen:
            return cls(_Frame(_Point(*origin), _Size(*size)))

        def frame(self) -> _Frame:
            return self._frame

    class _DummyNSScreen:
        _screens: ClassVar[list[_Screen]] = [
            _Screen.from_values((0.0, 0.0), (1920.0, 1080.0)),  # メインディスプレイ
            _Screen.from_values((0.0, 1080.0), (1920.0, 1200.0)),  # メインの上に配置
        ]

        @classmethod
        def screens(cls) -> list[_Screen]:
            return cls._screens

        @classmethod
        def mainScreen(cls) -> _Screen:  # noqa: N802 - AppKit に合わせる
            return cls._screens[0]

    monkeypatch.setattr(display, "NSScreen", _DummyNSScreen)

    # 上側ディスプレイ (pynput 座標では y が負) の中心付近の領域
    region = Region(left=100.0, top=-400.0, right=500.0, bottom=-200.0)
    assert display.is_region_within_displays(region) is True


def test_validate_preset_region_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "is_region_within_displays", lambda _: True)
    capture_service = _DummyCaptureService()
    region = Region(left=0, top=0, right=100, bottom=100)

    ok, message = cli._validate_preset_region(region, capture_service)

    assert ok is True
    assert message is None


def test_validate_preset_region_display_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "is_region_within_displays", lambda _: False)
    capture_service = _DummyCaptureService()
    region = Region(left=0, top=0, right=100, bottom=100)

    ok, message = cli._validate_preset_region(region, capture_service)

    assert ok is False
    assert message is not None
    assert "ディスプレイ" in message


def test_validate_preset_region_capture_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "is_region_within_displays", lambda _: True)
    capture_service = _DummyCaptureService(should_raise=True)
    region = Region(left=0, top=0, right=100, bottom=100)

    ok, message = cli._validate_preset_region(region, capture_service)

    assert ok is False
    assert message is not None
    assert "キャプチャ" in message
