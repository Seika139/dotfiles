from __future__ import annotations

from collections.abc import Iterable

from pynput import keyboard

MODIFIER_KEYS = {"shift", "ctrl", "alt", "cmd", "fn"}
RESERVED_COMBOS = {tuple(sorted(combo)) for combo in [("ctrl", "c"), ("esc",)]}


def normalize_key_name(value: str) -> str:
    lowered = value.strip().lower()
    match lowered:
        case "control" | "ctl" | "ctrl_l" | "ctrl_r":
            return "ctrl"
        case "option" | "alt_l" | "alt_r":
            return "alt"
        case "command" | "cmd_l" | "cmd_r":
            return "cmd"
        case "shift_l" | "shift_r":
            return "shift"
        case "return":
            return "enter"
        case "escape":
            return "esc"
        case _:
            return lowered


def normalize_combo(keys: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(sorted(normalize_key_name(key) for key in keys))
    if normalized in RESERVED_COMBOS:
        raise ValueError("reserved key combo cannot be used")
    return normalized


def parse_combo(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    parts = [normalize_key_name(part) for part in cleaned.split("+")]
    return normalize_combo(parts)


def key_to_name(key: keyboard.Key | keyboard.KeyCode) -> str | None:
    if isinstance(key, keyboard.KeyCode):
        if key.char is None:
            return None
        return normalize_key_name(key.char)
    name = getattr(key, "name", None)
    if not name:
        return None
    return normalize_key_name(name)
