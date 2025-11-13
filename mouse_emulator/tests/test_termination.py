from __future__ import annotations

from pynput import keyboard

from auto_emulator.runtime.termination import TerminationMonitor


def test_termination_monitor_sets_flag_on_esc() -> None:
    monitor = TerminationMonitor()
    assert not monitor.stop_requested()
    monitor._on_press(keyboard.Key.esc)
    assert monitor.stop_requested()


def test_termination_monitor_sets_flag_on_ctrl_c() -> None:
    monitor = TerminationMonitor()
    monitor._on_press(keyboard.Key.ctrl)
    monitor._on_press(keyboard.KeyCode.from_char("c"))
    assert monitor.stop_requested()


def test_termination_monitor_toggle_pause() -> None:
    monitor = TerminationMonitor(pause_combo=("ctrl", "p"))
    assert not monitor.is_paused()
    monitor._on_press(keyboard.Key.ctrl)
    monitor._on_press(keyboard.KeyCode.from_char("p"))
    assert monitor.is_paused()
    monitor._on_release(keyboard.Key.ctrl)
    monitor._on_release(keyboard.KeyCode.from_char("p"))
    monitor._on_press(keyboard.Key.ctrl)
    monitor._on_press(keyboard.KeyCode.from_char("p"))
    assert not monitor.is_paused()
