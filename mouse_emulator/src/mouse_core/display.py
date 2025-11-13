from __future__ import annotations

import importlib
from collections.abc import Sequence
from typing import Protocol, cast

__all__ = [
    "NSScreen",
    "ScreenLike",
    "get_display_bounds",
    "is_region_within_displays",
    "to_nss_point",
]

from .region import Region


class _ScreenPoint(Protocol):
    x: float
    y: float


class _ScreenSize(Protocol):
    width: float
    height: float


class _ScreenFrame(Protocol):
    origin: _ScreenPoint
    size: _ScreenSize


class ScreenLike(Protocol):
    def frame(self) -> _ScreenFrame: ...


class _ScreenProvider(Protocol):
    @classmethod
    def screens(cls) -> Sequence[ScreenLike]: ...

    @classmethod
    def mainScreen(cls) -> ScreenLike | None: ...  # noqa: N802 - AppKit API 名に合わせる


try:
    _appkit = importlib.import_module("AppKit")
except ModuleNotFoundError:  # pragma: no cover - AppKit 非対応環境
    NSScreen: _ScreenProvider | None = None
else:
    NSScreen = cast("_ScreenProvider | None", getattr(_appkit, "NSScreen", None))


def get_display_bounds() -> tuple[float, float, float, float] | None:
    if NSScreen is None:  # pragma: no cover - AppKit unavailable
        return None

    screens = NSScreen.screens()
    if not screens:
        return None

    min_x = min(float(screen.frame().origin.x) for screen in screens)
    min_y = min(float(screen.frame().origin.y) for screen in screens)
    max_x = max(
        float(screen.frame().origin.x + screen.frame().size.width) for screen in screens
    )
    max_y = max(
        float(screen.frame().origin.y + screen.frame().size.height)
        for screen in screens
    )
    return min_x, min_y, max_x, max_y


def _get_main_screen() -> ScreenLike | None:
    if NSScreen is None:  # pragma: no cover - AppKit unavailable
        return None
    main = NSScreen.mainScreen()
    if main is not None:
        return main
    screens = NSScreen.screens()
    if not screens:
        return None
    return screens[0]


def to_nss_point(x: float, y: float) -> tuple[float, float] | None:
    """pynput座標 (左上原点・下向きプラス) を NSScreen 座標に変換する。

    Returns:
        (x_ns, y_ns): NSScreen 座標 (左下原点・上向きプラス)。
        None: NSScreen 情報が取得できない場合。
    """
    main_screen = _get_main_screen()
    if main_screen is None:
        return None
    frame = main_screen.frame()
    main_left = float(frame.origin.x)
    main_top = float(frame.origin.y + frame.size.height)
    x_ns = main_left + float(x)
    y_ns = main_top - float(y)
    return x_ns, y_ns


def _region_to_nss_bounds(region: Region) -> tuple[float, float, float, float] | None:
    top_left = to_nss_point(region.left, region.top)
    bottom_right = to_nss_point(region.right, region.bottom)
    if top_left is None or bottom_right is None:
        return None

    left_ns = min(top_left[0], bottom_right[0])
    right_ns = max(top_left[0], bottom_right[0])
    top_ns = max(top_left[1], bottom_right[1])
    bottom_ns = min(top_left[1], bottom_right[1])
    return left_ns, bottom_ns, right_ns, top_ns


def is_region_within_displays(region: Region) -> bool:
    bounds = get_display_bounds()
    region_bounds = _region_to_nss_bounds(region)
    if bounds is None or region_bounds is None:
        return False
    min_x, min_y, max_x, max_y = bounds
    left_ns, bottom_ns, right_ns, top_ns = region_bounds
    return (
        left_ns >= min_x
        and right_ns <= max_x
        and bottom_ns >= min_y
        and top_ns <= max_y
    )
