from __future__ import annotations

import threading
import time
from collections.abc import Callable
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Self

from pynput import keyboard

from mouse_emulator.keys import key_to_name


class TerminationMonitor(AbstractContextManager["TerminationMonitor"]):
    """ESC/Ctrl+C で停止し、任意のホットキーで一時停止をトグルするモニタ。"""

    def __init__(
        self,
        pause_combo: tuple[str, ...] | None = None,
        on_pause: Callable[[], None] | None = None,
        on_resume: Callable[[], None] | None = None,
        *,
        manage_listener: bool = True,
    ) -> None:
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pressed: set[str] = set()
        self._pause_combo = set(pause_combo) if pause_combo else None
        self._pause_combo_active = False
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._manage_listener = manage_listener
        self._listener = (
            keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
                suppress=False,
            )
            if manage_listener
            else None
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
        if self._listener is not None and not self._listener.running:
            self._listener.start()

    def stop(self) -> None:
        if self._listener is not None and self._listener.running:
            self._listener.stop()
            self._listener.join()

    def stop_requested(self) -> bool:
        return self._stop_event.is_set()

    def wait(self, timeout: float | None = None) -> bool:
        return self._stop_event.wait(timeout)

    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    def wait_if_paused(self, interval: float = 0.1) -> None:
        while self.is_paused() and not self.stop_requested():
            time.sleep(max(0.01, interval))

    def pause_combo_repr(self) -> str | None:
        if self._pause_combo is None:
            return None
        return "+".join(sorted(self._pause_combo))

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        name = key_to_name(key) if key is not None else None
        self.on_key_press(name)

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        name = key_to_name(key) if key is not None else None
        self.on_key_release(name)

    def on_key_press(self, name: str | None) -> None:
        if name is None:
            return
        if name == "esc":
            self._stop_event.set()
            return
        self._pressed.add(name)

        if {"ctrl", "c"}.issubset(self._pressed):
            self._stop_event.set()
            return

        if (
            self._pause_combo is not None
            and self._pause_combo.issubset(self._pressed)
            and not self._pause_combo_active
        ):
            self._pause_combo_active = True
            if self._pause_event.is_set():
                self._pause_event.clear()
                if self._on_resume:
                    self._on_resume()
            else:
                self._pause_event.set()
                if self._on_pause:
                    self._on_pause()

    def on_key_release(self, name: str | None) -> None:
        if name is None:
            return
        self._pressed.discard(name)
        if self._pause_combo is not None and name in self._pause_combo:
            self._pause_combo_active = False
