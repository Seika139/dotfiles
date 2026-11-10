#!/usr/bin/env python3
"""Give APM-installed Ponytail hooks their package root without a global env."""

import argparse
import copy
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


OWNER = "dietrichgebert/ponytail"
LEGACY_OWNER = "ponytail"
HOOK_FILES = {
    "ponytail-activate.js",
    "ponytail-mode-tracker.js",
    "ponytail-subagent.js",
}
LEGACY_COMMAND = re.compile(r"^node PONYTAIL_DIR/hooks/(ponytail-(?:mode-tracker|subagent)\.js)$")


def _raw_command(hook_file: str) -> str:
    return (
        "node -e \"require(require('path').join(process.env.CLAUDE_PLUGIN_ROOT"
        ".split(String.fromCharCode(92)).join('/'), 'hooks/"
        f"{hook_file}'))\""
    )


def _legacy_raw_command(hook_file: str) -> str:
    return (
        "node -e \"require(require('node:path').join(process.env.CLAUDE_PLUGIN_ROOT"
        ".replaceAll(String.fromCharCode(92), '/'), 'hooks/"
        f"{hook_file}'))\""
    )


def canonical_command(command: str) -> Optional[str]:
    """Return a per-process Node command for an exact, known APM hook."""
    hook_file = next(
        (
            name
            for name in HOOK_FILES
            if command in {_raw_command(name), _legacy_raw_command(name)}
        ),
        None,
    )
    if hook_file is None:
        return None
    return (
        "node -e \"const p=require('path'),o=require('os');"
        "process.env.CLAUDE_PLUGIN_ROOT=p.join(o.homedir(),'.apm','apm_modules',"
        "'DietrichGebert','ponytail');"
        f"require(p.join(process.env.CLAUDE_PLUGIN_ROOT,'hooks/{hook_file}'))\""
    )


def is_canonical_command(command: str) -> bool:
    return any(command == canonical_command(_raw_command(name)) for name in HOOK_FILES)


def _hook_entries(document: Dict[str, Any], *, sidecar: bool):
    events = document if sidecar else document.get("hooks", {})
    if not isinstance(events, dict):
        raise ValueError("hooks must be a JSON object")
    for event, entries in events.items():
        if not isinstance(entries, list):
            raise ValueError(f"hooks.{event} must be an array")
        yield event, entries


def _commands(entry: Any):
    if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
        return
    for hook in entry["hooks"]:
        if isinstance(hook, dict) and isinstance(hook.get("command"), str):
            yield hook


def _plain_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy({key: value for key, value in entry.items() if key != "_apm_source"})


def _atomic_json_write(path: Path, document: Dict[str, Any]) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def normalize(settings_path: Path, sidecar_path: Path) -> int:
    if settings_path.is_symlink() or (sidecar_path.exists() and sidecar_path.is_symlink()):
        raise ValueError("Claude settings and APM hook sidecar must not be symlinks")
    if not settings_path.exists():
        return 0

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    if not isinstance(settings, dict):
        raise ValueError("Claude settings must be a JSON object")
    sidecar: Dict[str, Any] = {}
    if sidecar_path.exists():
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        if not isinstance(sidecar, dict):
            raise ValueError("APM hook sidecar must be a JSON object")

    changed_settings = False
    changed_sidecar = False
    removed_legacy: List[Tuple[str, Dict[str, Any]]] = []
    canonical_pairs: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []
    skipped_owned = 0
    settings_events = settings.setdefault("hooks", {})
    if not isinstance(settings_events, dict):
        raise ValueError("settings.hooks must be a JSON object")

    for event, entries in list(_hook_entries(sidecar, sidecar=True)):
        retained = []
        for entry in entries:
            owner = entry.get("_apm_source") if isinstance(entry, dict) else None
            legacy = owner == LEGACY_OWNER and any(
                LEGACY_COMMAND.fullmatch(hook.get("command", "")) for hook in _commands(entry)
            )
            if legacy:
                removed_legacy.append((event, _plain_entry(entry)))
                changed_sidecar = True
                continue
            if owner == OWNER:
                original = _plain_entry(entry)
                candidate = copy.deepcopy(entry)
                unknown = False
                for hook in _commands(candidate):
                    updated = canonical_command(hook["command"])
                    if updated is not None:
                        hook["command"] = updated
                    elif any(name in hook["command"] for name in HOOK_FILES) and (
                        "process.env.CLAUDE_PLUGIN_ROOT" in hook["command"]
                    ) and not is_canonical_command(hook["command"]):
                        unknown = True
                canonical = _plain_entry(candidate)
                actual_entries = settings_events.get(event, [])
                if not isinstance(actual_entries, list):
                    raise ValueError(f"settings.hooks.{event} must be an array")
                if original != canonical and (original in actual_entries or canonical in actual_entries):
                    entry.clear()
                    entry.update(candidate)
                    canonical_pairs.append((event, original, canonical))
                    changed_sidecar = True
                elif original != canonical:
                    skipped_owned += 1
                elif unknown:
                    skipped_owned += 1
            retained.append(entry)
        if retained:
            sidecar[event] = retained
        else:
            sidecar.pop(event, None)

    # Remove only obsolete legacy hooks with a matching APM ownership record.
    for event, legacy in removed_legacy:
        entries = settings_events.get(event, [])
        if not isinstance(entries, list):
            raise ValueError(f"settings.hooks.{event} must be an array")
        try:
            entries.remove(legacy)
            changed_settings = True
        except ValueError:
            pass
        if not entries:
            settings_events.pop(event, None)

    # The sidecar identifies which unmarked settings entry belongs to Ponytail.
    for event, original, canonical in canonical_pairs:
        entries = settings_events.get(event, [])
        for index, entry in enumerate(entries):
            if entry == original:
                entries[index] = copy.deepcopy(canonical)
                changed_settings = True

    writes = []
    if changed_settings:
        writes.append((settings_path, settings))
    if changed_sidecar:
        writes.append((sidecar_path, sidecar))
    backups: List[Tuple[Path, str]] = []
    try:
        for path, document in writes:
            fd, backup = tempfile.mkstemp(prefix=f".{path.name}.backup.", dir=path.parent)
            try:
                # Retain the original file for rollback if the paired update fails.
                with path.open("rb") as source, os.fdopen(fd, "wb") as target:
                    target.write(source.read())
                os.chmod(backup, stat.S_IMODE(path.stat().st_mode))
            except BaseException:
                try:
                    os.close(fd)
                except OSError:
                    pass
                os.unlink(backup)
                raise
            backups.append((path, backup))
            _atomic_json_write(path, document)
    except BaseException:
        for path, backup in reversed(backups):
            os.replace(backup, path)
        raise
    else:
        for _, backup in backups:
            os.unlink(backup)
    if skipped_owned:
        print(
            f"Warning: left {skipped_owned} edited Ponytail hook(s) unchanged because their ownership record did not match settings.",
            file=sys.stderr,
        )
    return int(changed_settings) + int(changed_sidecar)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude-dir", type=Path, default=Path.home() / ".claude")
    args = parser.parse_args()
    try:
        changed = normalize(args.claude_dir / "settings.json", args.claude_dir / "apm-hooks.json")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if changed:
        print("Normalized Ponytail hook commands in Claude settings and APM ownership data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
