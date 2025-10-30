from __future__ import annotations
from tabulate import tabulate

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from pynput import keyboard, mouse

from .calibration import run_calibration
from .color_printer import ColorPrinter, Colors
from .input_tracker import KeyState
from .keys import normalize_combo
from .profile import Profile, ProfileStore
from .region import Region


@dataclass(slots=True)
class Action:
    description: str
    combo: tuple[str, ...]
    relative: tuple[float, float]


@dataclass(slots=True)
class Emulator:
    profile: Profile
    region: Region
    _key_state: KeyState = field(init=False, repr=False)
    _mouse: mouse.Controller = field(init=False, repr=False)
    _actions: dict[tuple[str, ...], Action] = field(init=False, repr=False)
    _lock: threading.Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._key_state = KeyState()
        self._mouse = mouse.Controller()
        self._actions = {
            normalize_combo(action.keys): Action(
                description=action.description,
                combo=normalize_combo(action.keys),
                relative=(action.click_position.x, action.click_position.y),
            )
            for action in self.profile.actions
        }
        self._lock = threading.Lock()

    def run(self) -> None:
        print("エミュレーション開始: esc または ctrl+c で終了します")
        self.print_profile_info()
        keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )
        keyboard_listener.start()
        try:
            while not self._key_state.exit_requested:
                time.sleep(0.1)
        finally:
            keyboard_listener.stop()
            keyboard_listener.join()

    def print_profile_info(self) -> None:
        print("実行可能なアクション:")
        matrix = []
        for action in self._actions.values():
            matrix.append(
                [
                    " + ".join(action.combo),
                    f"{action.relative[0]:.3f}",
                    f"{action.relative[1]:.3f}",
                    action.description,
                ]
            )
        print(tabulate(matrix, headers=["キー", "x", "y", "説明"]))

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        self._key_state.on_press(key)
        if self._key_state.exit_requested:
            return
        combo = self._key_state.current_combo()
        if not combo:
            return
        normalized = normalize_combo(combo)
        if normalized not in self._actions:
            return
        if self._key_state.is_combo_active(normalized):
            return
        self._key_state.add_active_combo(normalized)
        action = self._actions[normalized]
        self._perform_action(action)

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        self._key_state.on_release(key)
        self._key_state.clear_inactive_combos()

    def _perform_action(self, action: Action) -> None:
        abs_x, abs_y = self.region.to_absolute(*action.relative)
        with self._lock:
            self._mouse.position = (abs_x, abs_y)
            time.sleep(0.03)
            self._mouse.click(mouse.Button.left, 1)


def emulate_from_profile(profile_path: Path, base_dir: Path) -> None:
    store = ProfileStore(base_dir=base_dir)
    path = store.resolve_path(str(profile_path))
    profile = store.load(path)
    region = run_calibration(ColorPrinter(Colors.GREEN))
    emulator = Emulator(profile=profile, region=region)
    emulator.run()
