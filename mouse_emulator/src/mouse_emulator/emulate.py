from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from pynput import keyboard, mouse
from tabulate import tabulate

from mouse_core import ColorPrinter, Colors, PointerController, Region, run_calibration

from .input_tracker import KeyState
from .keys import normalize_combo
from .profile import Profile, ProfileStore


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
    _pointer: PointerController = field(init=False, repr=False)
    _actions: dict[tuple[str, ...], Action] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._key_state = KeyState()
        self._pointer = PointerController()
        self._actions = {
            normalize_combo(action.keys): Action(
                description=action.description,
                combo=normalize_combo(action.keys),
                relative=(action.click_position.x, action.click_position.y),
            )
            for action in self.profile.actions
        }

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
            combo = sorted(action.combo, key=len, reverse=True)
            matrix.append([" + ".join(combo), action.description])
        print(tabulate(matrix, headers=["キー", "説明"]))

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key is None:
            return
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

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key is None:
            return
        self._key_state.on_release(key)
        self._key_state.clear_inactive_combos()

    def _perform_action(self, action: Action) -> None:
        self._pointer.click_relative(
            self.region,
            action.relative,
            button=mouse.Button.left,
        )


def emulate_from_profile(profile_path: Path, base_dir: Path) -> None:
    store = ProfileStore(base_dir=base_dir)
    path = store.resolve_path(str(profile_path))
    profile = store.load(path)
    region = run_calibration(ColorPrinter(Colors.GREEN))
    emulator = Emulator(profile=profile, region=region)
    emulator.run()
