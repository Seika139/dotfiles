#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Render Codex hooks.json from profile-managed JSON fragments.

Merges <profile>/hooks.base.json + <profile>/hooks.local.json, and preserves
any `_apm_source` entries already present in the deploy target (so that
`apm install -g` written hooks are not dropped when we regenerate the file).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


def load_hooks(path: Path) -> dict[str, list[Any]]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as a JSON object")
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{path}: 'hooks' key must be an object")
    return hooks


def load_apm_entries(target: Path) -> dict[str, list[Any]]:
    """Extract `_apm_source` matcher groups from an existing deploy target.

    Symlinks are followed rather than skipped: legacy deployments pointed
    `target` at a profile-managed hooks.json into which `apm install -g`
    had already written `_apm_source` entries, and those must survive the
    first `mise run link` after migration. If the symlink target does not
    exist or is not valid JSON, treat it as empty and continue.
    """
    if not target.is_file():
        return {}
    try:
        hooks = load_hooks(target)
    except (ValueError, json.JSONDecodeError):
        return {}

    apm_hooks: dict[str, list[Any]] = {}
    for event, matcher_groups in hooks.items():
        if not isinstance(matcher_groups, list):
            continue
        kept = [group for group in matcher_groups if isinstance(group, dict) and "_apm_source" in group]
        if kept:
            apm_hooks[event] = kept
    return apm_hooks


def merge_hooks(*sources: dict[str, list[Any]]) -> dict[str, list[Any]]:
    merged: dict[str, list[Any]] = {}
    for source in sources:
        for event, matcher_groups in source.items():
            bucket = merged.setdefault(event, [])
            for group in matcher_groups:
                if group not in bucket:
                    bucket.append(group)
    return merged


def render(profile_path: Path, target: Path) -> dict[str, Any]:
    base = load_hooks(profile_path / "hooks.base.json")
    local = load_hooks(profile_path / "hooks.local.json")
    apm = load_apm_entries(target)
    return {"hooks": merge_hooks(base, local, apm)}


def write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(content)
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-path", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--same-as", type=Path)
    args = parser.parse_args()

    try:
        data = render(args.profile_path, args.target)
    except Exception as error:
        print(f"render_hooks.py: {error}", file=sys.stderr)
        return 1

    if args.same_as is not None:
        try:
            actual = json.loads(args.same_as.read_text(encoding="utf-8"))
        except Exception as error:
            print(f"render_hooks.py: {error}", file=sys.stderr)
            return 1
        return 0 if data == actual else 10

    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    if args.output is None:
        print(content, end="")
        return 0

    write_output(args.output, content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
