from __future__ import annotations

import threading
import time
from typing import Final

from pynput import mouse

from .region import Region

DEFAULT_MOVE_DELAY: Final[float] = 0.03
DEFAULT_DRAG_HOLD: Final[float] = 0.05
DEFAULT_DRAG_MOVE_DELAY: Final[float] = 0.01
DEFAULT_DRAG_STEPS: Final[int] = 12


class PointerController:
    """マウス操作をカプセル化し、移動とクリックの同期を保証する。"""

    def __init__(self, move_delay: float = DEFAULT_MOVE_DELAY) -> None:
        self._mouse = mouse.Controller()
        self._lock = threading.Lock()
        self._move_delay = move_delay

    def move_to(self, x: int, y: int) -> None:
        with self._lock:
            self._mouse.position = (x, y)

    def click_absolute(
        self,
        x: int,
        y: int,
        button: mouse.Button = mouse.Button.left,
        count: int = 1,
        *,
        ensure_move: bool = True,
    ) -> None:
        with self._lock:
            if ensure_move:
                self._mouse.position = (x, y)
                time.sleep(self._move_delay)
            self._mouse.click(button, count)

    def click_relative(
        self,
        region: Region,
        relative: tuple[float, float],
        *,
        button: mouse.Button = mouse.Button.left,
        ensure_move: bool = True,
    ) -> None:
        rel_x, rel_y = relative
        abs_x, abs_y = region.to_absolute(rel_x, rel_y)
        self.click_absolute(
            abs_x,
            abs_y,
            button=button,
            ensure_move=ensure_move,
        )

    def position(self) -> tuple[int, int]:
        with self._lock:
            current = self._mouse.position
        return int(current[0]), int(current[1])

    def drag_relative(
        self,
        region: Region,
        start: tuple[float, float],
        end: tuple[float, float],
        *,
        button: mouse.Button = mouse.Button.left,
        profile: tuple[int, float, float] | None = None,
    ) -> None:
        start_abs = region.to_absolute(*start)
        end_abs = region.to_absolute(*end)
        steps, step_delay, hold_duration = (
            profile
            if profile is not None
            else (DEFAULT_DRAG_STEPS, DEFAULT_DRAG_MOVE_DELAY, DEFAULT_DRAG_HOLD)
        )
        with self._lock:
            self._mouse.position = start_abs
            time.sleep(self._move_delay)
            self._mouse.press(button)
            time.sleep(max(0.0, hold_duration))
            total_steps = max(1, steps)
            x_step = (end_abs[0] - start_abs[0]) / total_steps
            y_step = (end_abs[1] - start_abs[1]) / total_steps
            current_x = float(start_abs[0])
            current_y = float(start_abs[1])
            for _ in range(total_steps - 1):
                current_x += x_step
                current_y += y_step
                self._mouse.position = (int(current_x), int(current_y))
                time.sleep(step_delay)
            self._mouse.position = end_abs
            time.sleep(self._move_delay)
            self._mouse.release(button)
