"""マウス操作に関する共通ユーティリティ群。"""

from __future__ import annotations

from mouse_core.calibration import Calibrator, run_calibration
from mouse_core.canvas_refine import RefineReport, refine_region_to_aspect
from mouse_core.color_printer import ColorPrinter, Colors
from mouse_core.loggers import SessionLogger
from mouse_core.pointer import PointerController
from mouse_core.region import Region

__all__ = [
    "Calibrator",
    "ColorPrinter",
    "Colors",
    "PointerController",
    "RefineReport",
    "Region",
    "SessionLogger",
    "refine_region_to_aspect",
    "run_calibration",
]
