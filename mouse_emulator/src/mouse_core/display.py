from __future__ import annotations

import importlib
from typing import Any

from .region import Region

try:
    _appkit = importlib.import_module("AppKit")
except ModuleNotFoundError:  # pragma: no cover - AppKit 非対応環境
    NSScreen: Any | None = None
else:
    NSScreen = getattr(_appkit, "NSScreen", None)


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


def is_region_within_displays(region: Region) -> bool:
    bounds = get_display_bounds()
    if bounds is None:
        return False
    min_x, min_y, max_x, max_y = bounds
    return (
        region.left >= min_x
        and region.right <= max_x
        and region.top >= min_y
        and region.bottom <= max_y
    )
