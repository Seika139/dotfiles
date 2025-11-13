from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from pynput import keyboard, mouse
from tabulate import tabulate

from auto_emulator.runtime.termination import TerminationMonitor
from auto_emulator.services.capture import PILScreenCaptureService
from mouse_core import ColorPrinter, Colors, PointerController, Region, run_calibration
from mouse_core.display import is_region_within_displays
from mouse_core.loggers import SessionLogger

from .input_tracker import KeyState
from .keys import normalize_combo, parse_combo
from .profile import CalibrationSettings, Profile, ProfileStore

COLOR_MAP = {
    "default": Colors.DEFAULT,
    "green": Colors.GREEN,
    "blue": Colors.BLUE,
    "warning": Colors.WARNING,
    "fail": Colors.FAIL,
}

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")

PAUSE_NOTICE = "⏸ 一時停止しました。再開するには指定したキーを押してください。"
RESUME_NOTICE = "▶️ エミュレーションを再開します。"


def _strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


def _normalize_pause_combo(raw: str | None) -> tuple[str, ...] | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    if not cleaned or cleaned.lower() in {"none", "off", "disable"}:
        return None
    return parse_combo(cleaned)


def _resolve_log_path(value: str | None, base_dir: Path) -> Path | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    path = Path(cleaned).expanduser()
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def _resolve_emulation_region(
    settings: CalibrationSettings,
    calibrate_flag: bool | None,
    printer: ColorPrinter,
    emit: Callable[[str], None],
    capture_service: PILScreenCaptureService,
) -> Region:
    if _should_calibrate(calibrate_flag, settings):
        return run_calibration(printer)

    if settings.preset is not None:
        preset_region = settings.preset.to_region()
        is_valid, error_message = _validate_preset_region(
            preset_region,
            capture_service=capture_service,
        )
        if is_valid:
            emit("キャリブレーションをスキップし、設定済みの座標を使用します。")
            return preset_region
        if error_message:
            emit(error_message)
        emit("手動キャリブレーションを実行します。")
        return run_calibration(printer)

    emit(
        "キャリブレーション設定が見つからないため、手動キャリブレーションを実行します。",
    )
    return run_calibration(printer)


def _calibration_color(settings: CalibrationSettings) -> str:
    return COLOR_MAP.get(settings.color, Colors.GREEN)


def _should_calibrate(cli_flag: bool | None, settings: CalibrationSettings) -> bool:
    if cli_flag is not None:
        return cli_flag
    return settings.enabled


def _validate_preset_region(
    region: Region,
    *,
    capture_service: PILScreenCaptureService,
) -> tuple[bool, str | None]:
    if not is_region_within_displays(region):
        message = (
            "設定されたキャリブレーション座標が現在のディスプレイ領域と一致しません。"
        )
        return False, message
    try:
        image = capture_service.capture(region=region)
    except Exception as exc:  # noqa: BLE001
        message = (
            "設定されたキャリブレーション座標でのキャプチャに失敗しました。"
            f" 詳細: {exc}"
        )
        return False, message
    if image.width <= 0 or image.height <= 0:
        message = "設定されたキャリブレーション座標から取得した画像サイズが不正です。"
        return False, message
    return True, None


@dataclass(slots=True)
class EmulateOptions:
    calibrate: bool | None = None
    pause_key: str | None = None
    log_file: Path | None = None
    log_overwrite: bool = False


@dataclass(slots=True)
class Action:
    description: str
    combo: tuple[str, ...]
    relative: tuple[float, float]


@dataclass(slots=True)
class Emulator:
    profile: Profile
    region: Region
    monitor: TerminationMonitor | None
    log: Callable[[str], None]
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
        self.log("エミュレーション開始: esc または ctrl+c で終了します")
        self.print_profile_info()
        keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )
        keyboard_listener.start()
        try:
            while True:
                if self.monitor and self.monitor.stop_requested():
                    break
                if self._key_state.exit_requested:
                    break
                if self.monitor:
                    self.monitor.wait_if_paused()
                    if self.monitor.stop_requested():
                        break
                time.sleep(0.05)
        finally:
            keyboard_listener.stop()
            keyboard_listener.join()

    def print_profile_info(self) -> None:
        self.log("実行可能なアクション:")
        matrix = []
        for action in self._actions.values():
            combo = sorted(action.combo, key=len, reverse=True)
            matrix.append([" + ".join(combo), action.description])
        self.log(tabulate(matrix, headers=["キー", "説明"]))

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
        if self.monitor:
            self.monitor.wait_if_paused()
            if self.monitor.stop_requested():
                return
        self._pointer.click_relative(
            self.region,
            action.relative,
            button=mouse.Button.left,
        )


def emulate_from_profile(
    profile_path: Path,
    base_dir: Path,
    options: EmulateOptions | None = None,
) -> None:
    opts = options or EmulateOptions()
    store = ProfileStore(base_dir=base_dir)
    path = store.resolve_path(str(profile_path))
    profile = store.load(path)
    settings = profile.calibration

    try:
        pause_combo = _normalize_pause_combo(
            opts.pause_key
            if opts.pause_key is not None
            else profile.controls.pause_toggle,
        )
    except ValueError as exc:
        msg = f"controls.pause_toggle の値が不正です: {exc}"
        raise ValueError(msg) from exc

    log_path = (
        opts.log_file.expanduser()
        if opts.log_file is not None
        else _resolve_log_path(profile.logging.file, base_dir)
    )
    log_mode = "overwrite" if opts.log_overwrite else profile.logging.mode
    if log_path is not None and not log_path.is_absolute():
        log_path = (base_dir / log_path).resolve()

    with SessionLogger(log_path, mode=log_mode) as session_logger:
        printer = ColorPrinter(_calibration_color(settings))

        def log_info(message: str, *, color: bool = False) -> None:
            if color:
                printer(message)
            else:
                print(message)
            session_logger.log(_strip_ansi(message))

        capture_service = PILScreenCaptureService()
        region = _resolve_emulation_region(
            settings,
            opts.calibrate,
            printer,
            log_info,
            capture_service,
        )

        if log_path is not None:
            log_info(f"ログファイル: {log_path}")
        if pause_combo is not None:
            combo_label = "+".join(pause_combo)
            log_info(f"一時停止キー: {combo_label} (同じキーで再開)")

        try:
            with TerminationMonitor(
                pause_combo=pause_combo,
                on_pause=(lambda: log_info(PAUSE_NOTICE)) if pause_combo else None,
                on_resume=(lambda: log_info(RESUME_NOTICE)) if pause_combo else None,
            ) as monitor:
                emulator = Emulator(
                    profile=profile,
                    region=region,
                    monitor=monitor,
                    log=log_info,
                )
                emulator.run()
        except Exception as exc:
            log_info(f"エラー: {exc}")
            raise
