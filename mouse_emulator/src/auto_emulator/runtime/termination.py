from __future__ import annotations

import threading
from contextlib import AbstractContextManager
from types import TracebackType
from typing import ClassVar, Self

from pynput import keyboard


class TerminationMonitor(AbstractContextManager["TerminationMonitor"]):
    """Listens for ESC または Ctrl+C を押下した際に停止フラグを立てる。"""

    _CTRL_KEYS: ClassVar[set[keyboard.Key]] = {
        keyboard.Key.ctrl,
        keyboard.Key.ctrl_l,
        keyboard.Key.ctrl_r,
    }

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._ctrl_pressed = False
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()

    def start(self) -> None:
        if not self._listener.running:
            self._listener.start()

    def stop(self) -> None:
        if self._listener.running:
            self._listener.stop()
            self._listener.join()

    def stop_requested(self) -> bool:
        return self._stop_event.is_set()

    def wait(self, timeout: float | None = None) -> bool:
        return self._stop_event.wait(timeout)

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key is None:
            return
        if key in self._CTRL_KEYS:
            self._ctrl_pressed = True
            return
        if key == keyboard.Key.esc:
            self._stop_event.set()
            return
        if (
            self._ctrl_pressed
            and isinstance(key, keyboard.KeyCode)
            and key.char is not None
            and key.char.lower() == "c"
        ):
            self._stop_event.set()

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key in self._CTRL_KEYS:
            self._ctrl_pressed = False
