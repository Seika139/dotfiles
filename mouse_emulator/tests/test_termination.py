# ruff: noqa: S101

from __future__ import annotations

from pynput import keyboard

from auto_emulator.runtime.termination import TerminationMonitor


def test_termination_monitor_sets_flag_on_esc() -> None:
    monitor = TerminationMonitor()
    assert not monitor.stop_requested()
    monitor._on_press(keyboard.Key.esc)  # noqa: SLF001
    assert monitor.stop_requested()


def test_termination_monitor_sets_flag_on_ctrl_c() -> None:
    monitor = TerminationMonitor()
    monitor._on_press(keyboard.Key.ctrl)  # noqa: SLF001
    monitor._on_press(keyboard.KeyCode.from_char("c"))  # noqa: SLF001
    assert monitor.stop_requested()


def test_termination_monitor_toggle_pause() -> None:
    monitor = TerminationMonitor(pause_combo=("ctrl", "p"))
    assert not monitor.is_paused()
    monitor._on_press(keyboard.Key.ctrl)  # noqa: SLF001
    monitor._on_press(keyboard.KeyCode.from_char("p"))  # noqa: SLF001
    assert monitor.is_paused()
    monitor._on_release(keyboard.Key.ctrl)  # noqa: SLF001
    monitor._on_release(keyboard.KeyCode.from_char("p"))  # noqa: SLF001
    monitor._on_press(keyboard.Key.ctrl)  # noqa: SLF001
    monitor._on_press(keyboard.KeyCode.from_char("p"))  # noqa: SLF001
    assert not monitor.is_paused()
