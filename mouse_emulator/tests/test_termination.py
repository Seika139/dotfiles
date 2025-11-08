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
    ctrl_c = keyboard.KeyCode.from_char("c")
    monitor._on_press(ctrl_c)  # noqa: SLF001
    assert monitor.stop_requested()
    monitor._on_release(keyboard.Key.ctrl)  # noqa: SLF001
    assert not monitor._ctrl_pressed  # noqa: SLF001
