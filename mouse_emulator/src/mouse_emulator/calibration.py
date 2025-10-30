from __future__ import annotations

import threading
from collections.abc import Callable

from pynput import keyboard, mouse

from .region import Region


class Calibrator:
    def __init__(self, printer: Callable[[str], None] | None = None) -> None:
        self._printer = printer or print
        self._points: list[tuple[float, float]] = []
        self._ready = threading.Event()
        self._lock = threading.Lock()
        self._shift_pressed = False
        self._enter_armed = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )
        self._mouse = mouse.Controller()

    def run(self) -> Region:
        self._printer(
            "キャリブレーション: カーソルを領域の左上に置き、shift+enter を押してください"
        )
        self._listener.start()
        self._ready.wait()
        self._listener.stop()
        self._listener.join()
        if len(self._points) != 2:
            raise RuntimeError("キャリブレーションに失敗しました")
        return Region.from_points(self._points[0], self._points[1])

    def _record_point(self) -> None:
        position = self._mouse.position
        with self._lock:
            if len(self._points) == 0:
                self._printer("左上を記録しました。次に右下を同様に指定してください")
            elif len(self._points) == 1:
                self._printer("右下を記録しました。キャリブレーション完了です")
            else:
                return
            self._points.append((float(position[0]), float(position[1])))
            if len(self._points) == 2:
                self._ready.set()

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key in {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r}:
            self._shift_pressed = True
            return
        if key == keyboard.Key.enter and self._shift_pressed and self._enter_armed:
            self._enter_armed = False
            self._record_point()

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key in {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r}:
            self._shift_pressed = False
        if key == keyboard.Key.enter:
            self._enter_armed = True


def run_calibration(printer: Callable[[str], None] | None = None) -> Region:
    calibrator = Calibrator(printer=printer)
    return calibrator.run()
