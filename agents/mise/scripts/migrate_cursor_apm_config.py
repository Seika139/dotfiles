#!/usr/bin/env python3
"""Migrate legacy Cursor settings before APM writes user-scope config."""

import argparse
import copy
import json
import os
import stat
import sys
import tempfile
from pathlib import Path


LEGACY_CURSOR_EVENTS = ("UserPromptSubmit", "PreToolUse")
PONYTAIL_OWNERS = frozenset(("ponytail", "dietrichgebert/ponytail"))


def _read_json(path, label, optional=False):
    if path.is_symlink():
        raise ValueError("{} must not be a symlink: {}".format(label, path))
    if not path.exists():
        if optional:
            return None
        raise ValueError("{} does not exist: {}".format(label, path))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("cannot read {}: {}".format(label, path)) from error
    if not isinstance(data, dict):
        raise ValueError("{} must be a JSON object: {}".format(label, path))
    return data


def _plain_entry(entry):
    return {key: copy.deepcopy(value) for key, value in entry.items() if key != "_apm_source"}


def _atomic_write(path, data, mode):
    descriptor, temporary = tempfile.mkstemp(prefix=".{}.".format(path.name), dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.chmod(temporary, mode)
        os.replace(temporary, str(path))
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def merge_mcp_config(cursor_dir, source_path):
    source = _read_json(source_path, "dotfiles Cursor MCP config", optional=True)
    if source is None:
        return False
    source_servers = source.get("mcpServers", {})
    if not isinstance(source_servers, dict):
        raise ValueError("dotfiles mcpServers must be a JSON object")

    target_path = cursor_dir / "mcp.json"
    target = _read_json(target_path, "Cursor MCP config", optional=True)
    if target is None:
        target = copy.deepcopy(source)
        original_mode = stat.S_IMODE(source_path.stat().st_mode)
        changed = True
    else:
        target_servers = target.setdefault("mcpServers", {})
        if not isinstance(target_servers, dict):
            raise ValueError("Cursor mcpServers must be a JSON object")
        missing = {key: copy.deepcopy(value) for key, value in source_servers.items() if key not in target_servers}
        if not missing:
            return False
        target_servers.update(missing)
        original_mode = stat.S_IMODE(target_path.stat().st_mode)
        changed = True

    if changed:
        _atomic_write(target_path, target, original_mode)
    return changed


def remove_legacy_hooks(cursor_dir):
    hooks_path = cursor_dir / "hooks.json"
    sidecar_path = cursor_dir / "apm-hooks.json"
    document = _read_json(hooks_path, "Cursor hooks config", optional=True)
    if document is None:
        return False
    sidecar = _read_json(sidecar_path, "Cursor APM hook ownership data", optional=True)
    if sidecar is None:
        return False

    hooks = document.get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("Cursor hooks must be a JSON object")

    changed_hooks = False
    changed_sidecar = False
    warnings = 0
    for event in LEGACY_CURSOR_EVENTS:
        actual_entries = hooks.get(event, [])
        owned_entries = sidecar.get(event, [])
        if not isinstance(actual_entries, list) or not isinstance(owned_entries, list):
            raise ValueError("Cursor hook event {} must contain arrays".format(event))

        retained = []
        for ownership_entry in owned_entries:
            if not isinstance(ownership_entry, dict) or ownership_entry.get("_apm_source") not in PONYTAIL_OWNERS:
                retained.append(ownership_entry)
                continue
            plain = _plain_entry(ownership_entry)
            try:
                actual_entries.remove(plain)
            except ValueError:
                # Its absence may be a user deletion or an interrupted earlier
                # write. Without provenance that distinguishes those cases,
                # keep the ownership record and leave the live config alone.
                retained.append(ownership_entry)
                warnings += 1
            else:
                changed_hooks = True
                changed_sidecar = True

        if retained:
            sidecar[event] = retained
        else:
            sidecar.pop(event, None)
        if not actual_entries:
            hooks.pop(event, None)

    if changed_hooks:
        hooks_path_backup = hooks_path.read_bytes()
        hooks_mode = stat.S_IMODE(hooks_path.stat().st_mode)
        sidecar_backup = sidecar_path.read_bytes()
        sidecar_mode = stat.S_IMODE(sidecar_path.stat().st_mode)
        try:
            # Clear the invalid event in Cursor first. If the process is killed
            # before the sidecar write, a later run cannot distinguish that
            # stale record from an intentional user deletion. It keeps the
            # unmatched record and warns instead of pruning it automatically.
            _atomic_write(hooks_path, document, hooks_mode)
            if changed_sidecar:
                _atomic_write(sidecar_path, sidecar, sidecar_mode)
        except BaseException:
            _atomic_bytes(hooks_path, hooks_path_backup, hooks_mode)
            _atomic_bytes(sidecar_path, sidecar_backup, sidecar_mode)
            raise

    if warnings:
        print(
            "Warning: kept {} unmatched Ponytail Cursor hook ownership record{}; "
            "the corresponding live hook is missing or edited. This may reflect "
            "a user change or an interrupted migration; review manually because "
            "rerunning will not remove the record automatically.".format(
                warnings, "" if warnings == 1 else "s"
            ),
            file=sys.stderr,
        )
    return changed_hooks or changed_sidecar


def _atomic_bytes(path, data, mode):
    descriptor, temporary = tempfile.mkstemp(prefix=".{}.".format(path.name), dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, str(path))
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def migrate(cursor_dir, mcp_source):
    if cursor_dir.is_symlink() or not cursor_dir.is_dir():
        raise ValueError("Cursor config must be a real directory: {}".format(cursor_dir))
    mcp_changed = merge_mcp_config(cursor_dir, mcp_source)
    hooks_changed = remove_legacy_hooks(cursor_dir)
    return mcp_changed or hooks_changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cursor-dir", type=Path, required=True)
    parser.add_argument("--mcp-source", type=Path, required=True)
    args = parser.parse_args()
    try:
        changed = migrate(args.cursor_dir, args.mcp_source)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if changed:
        print("Migrated Cursor APM config and Ponytail hook ownership data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
