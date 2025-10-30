from __future__ import annotations

import threading
from collections.abc import Iterable

from pynput import keyboard

from .keys import MODIFIER_KEYS, key_to_name, normalize_combo


class KeyState:
    """グローバルキーの状態を追跡するヘルパー"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pressed: set[str] = set()
        self._active_combos: set[tuple[str, ...]] = set()
        self._exit_requested = threading.Event()

    def on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        name = key_to_name(key)
        if name is None:
            return
        if name == "esc":
            self._exit_requested.set()
            return
        with self._lock:
            self._pressed.add(name)
            if {"ctrl", "c"}.issubset(self._pressed):
                self._exit_requested.set()

    def on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        name = key_to_name(key)
        if name is None:
            return
        with self._lock:
            self._pressed.discard(name)

    def current_combo(self) -> tuple[str, ...]:
        with self._lock:
            if not self._pressed:
                return tuple()
            return tuple(sorted(self._pressed))

    def modifiers_only(self) -> bool:
        with self._lock:
            return bool(self._pressed) and all(key in MODIFIER_KEYS for key in self._pressed)

    def add_active_combo(self, combo: Iterable[str]) -> None:
        normalized = normalize_combo(combo)
        with self._lock:
            self._active_combos.add(normalized)

    def clear_inactive_combos(self) -> None:
        with self._lock:
            current = set(self._pressed)
            inactive = {combo for combo in self._active_combos if not set(combo).issubset(current)}
            self._active_combos.difference_update(inactive)

    def is_combo_active(self, combo: Iterable[str]) -> bool:
        normalized = normalize_combo(combo)
        with self._lock:
            return normalized in self._active_combos

    @property
    def exit_requested(self) -> bool:
        return self._exit_requested.is_set()

    def wait_for_exit(self, timeout: float | None = None) -> bool:
        return self._exit_requested.wait(timeout=timeout)
