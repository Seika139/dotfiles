from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import NamedTuple

from pynput import keyboard, mouse

from mouse_core import ColorPrinter, Colors, run_calibration

from .input_tracker import KeyState
from .keys import MODIFIER_KEYS
from .profile import (
    CalibrationPreset,
    CalibrationSettings,
    ClickPosition,
    Profile,
    ProfileEntry,
    ProfileStore,
)

printer = ColorPrinter(Colors.GREEN)


class ClickEvent(NamedTuple):
    position: tuple[float, float]


@dataclass(slots=True)
class RegistrationSession:
    profile_store: ProfileStore
    profile_name: str

    def run(self) -> Path:
        region = run_calibration(ColorPrinter(Colors.WARNING))
        printer(
            "登録モード: クリックした位置を登録し、esc または ctrl+c で終了します。",
        )
        printer("キーを押して指示が表示されたら、対応する座標をクリックしてください")
        key_state = KeyState()
        click_queue: Queue[ClickEvent] = Queue()
        combo_queue: Queue[tuple[str, ...]] = Queue()
        last_combo: tuple[str, ...] | None = None

        def emit_combo() -> None:
            nonlocal last_combo
            combo = key_state.current_combo()
            if not combo:
                last_combo = None
                return
            if all(key in MODIFIER_KEYS for key in combo):
                last_combo = None
                return
            if combo == last_combo:
                return
            combo_queue.put_nowait(combo)
            last_combo = combo

        def on_click(x: float, y: float, button: mouse.Button, pressed: bool) -> None:
            if button is not mouse.Button.left or not pressed:
                return
            click_queue.put_nowait(ClickEvent(position=(x, y)))

        def on_press(key: keyboard.Key | keyboard.KeyCode | None) -> None:
            if key is None:
                return
            key_state.on_press(key)
            if key_state.exit_requested:
                return
            emit_combo()

        def on_release(key: keyboard.Key | keyboard.KeyCode | None) -> None:
            if key is None:
                return
            key_state.on_release(key)
            emit_combo()

        keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release,
            suppress=False,
        )
        mouse_listener = mouse.Listener(on_click=on_click)
        keyboard_listener.start()
        mouse_listener.start()

        entries: list[ProfileEntry] = []
        pending_combo: tuple[str, ...] | None = None
        try:
            while True:
                if key_state.exit_requested:
                    break
                while True:
                    try:
                        pending_combo = tuple(
                            sorted(combo_queue.get_nowait(), key=len, reverse=True),
                        )
                    except Empty:
                        break
                    combo_label = " + ".join(pending_combo)
                    printer(f"キー: {combo_label} に登録する座標をクリックしてください")
                try:
                    event = click_queue.get(timeout=0.1)
                except Empty:
                    continue
                if pending_combo is None:
                    continue
                try:
                    rel_x, rel_y = region.to_relative(*event.position)
                except ValueError:
                    printer(
                        f"相対座標: {event.position}, "
                        "キャリブレーション領域外のクリックです。もう一度指定してください",
                    )
                    continue
                combo_label = " + ".join(pending_combo)
                try:
                    entry = ProfileEntry(
                        description=combo_label,
                        click_position=ClickPosition(x=rel_x, y=rel_y),
                        keys=list(pending_combo),
                    )
                except ValueError as exc:
                    printer(f"エントリの作成に失敗しました: {exc}")
                    continue
                entries.append(entry)
                printer(
                    f"登録完了: キー: {combo_label}, "
                    f"相対座標: ({rel_x:.3f}, {rel_y:.3f})",
                )
                pending_combo = None
        finally:
            keyboard_listener.stop()
            mouse_listener.stop()
            keyboard_listener.join()
            mouse_listener.join()

        if not entries:
            raise RuntimeError("1 件以上のアクションを登録してください")
        calibration_settings = CalibrationSettings(
            preset=CalibrationPreset(
                left=region.left,
                top=region.top,
                right=region.right,
                bottom=region.bottom,
            ),
        )
        profile = Profile(actions=entries, calibration=calibration_settings)
        target_path = self.profile_store.resolve_path(self.profile_name)
        self.profile_store.save(target_path, profile)
        printer(f"プロファイルを保存しました: {target_path}")
        return target_path


def register_profile(profile_name: str, base_dir: Path) -> Path:
    session = RegistrationSession(
        profile_store=ProfileStore(base_dir=base_dir),
        profile_name=profile_name,
    )
    return session.run()
