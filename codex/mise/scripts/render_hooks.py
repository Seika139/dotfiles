#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Render Codex hooks.json from profile-managed JSON fragments.

Merges <profile>/hooks.base.json + <profile>/hooks.local.json, and preserves
external matcher groups already present in the deploy target (e.g. hooks an
`apm install -g` package writes directly into the deploy target). Ponytail
commands already managed by the active profile are removed from the preserved
target so stale APM commands cannot shadow or duplicate them. Exact duplicates
between remaining sources are deduped by `merge_hooks`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


PONYTAIL_HOOK_FILES = {
    "ponytail-activate.js",
    "ponytail-mode-tracker.js",
    "ponytail-subagent.js",
}
PONYTAIL_DIRECT_COMMAND = re.compile(
    r'^node "[^"\r\n]*[\\/]\.codex[\\/]hooks[\\/]ponytail[\\/]hooks[\\/]'
    r'(ponytail-(?:activate|mode-tracker|subagent)\.js)"$',
    re.IGNORECASE,
)


def ponytail_hook_file(command: str) -> str | None:
    """Identify current APM, normalized APM, and obsolete local Ponytail commands."""
    for hook_file in PONYTAIL_HOOK_FILES:
        raw = (
            "node -e \"require(require('path').join(process.env.CLAUDE_PLUGIN_ROOT"
            ".split(String.fromCharCode(92)).join('/'), 'hooks/"
            f"{hook_file}'))\""
        )
        legacy = (
            "node -e \"require(require('node:path').join(process.env.CLAUDE_PLUGIN_ROOT"
            ".replaceAll(String.fromCharCode(92), '/'), 'hooks/"
            f"{hook_file}'))\""
        )
        canonical = (
            "node -e \"const p=require('path'),o=require('os');"
            "process.env.CLAUDE_PLUGIN_ROOT=p.join(o.homedir(),'.apm','apm_modules',"
            "'DietrichGebert','ponytail');"
            f"require(p.join(process.env.CLAUDE_PLUGIN_ROOT,'hooks/{hook_file}'))\""
        )
        if command in {raw, legacy, canonical}:
            return hook_file
    match = PONYTAIL_DIRECT_COMMAND.fullmatch(command)
    return match.group(1) if match else None


def remove_profile_managed_ponytail_hooks(
    external: dict[str, list[Any]], profile_sources: list[dict[str, list[Any]]]
) -> dict[str, list[Any]]:
    """Drop only external Ponytail hooks already supplied by the active profile."""
    managed: dict[str, set[str]] = {}
    for source in profile_sources:
        for event, groups in source.items():
            for group in groups:
                for hook in group.get("hooks", []):
                    command = hook.get("command")
                    if isinstance(command, str):
                        hook_file = ponytail_hook_file(command)
                        if hook_file:
                            managed.setdefault(event, set()).add(hook_file)

    for event, groups in list(external.items()):
        retained_groups = []
        for group in groups:
            group_hooks = group.get("hooks")
            if not isinstance(group_hooks, list):
                retained_groups.append(group)
                continue
            retained_hooks = [
                hook
                for hook in group_hooks
                if not (
                    isinstance(hook.get("command"), str)
                    and ponytail_hook_file(hook["command"]) in managed.get(event, set())
                )
            ]
            if retained_hooks:
                group["hooks"] = retained_hooks
                retained_groups.append(group)
            elif not group_hooks:
                retained_groups.append(group)
        if retained_groups:
            external[event] = retained_groups
        else:
            external.pop(event, None)
    return external


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
    for event, matcher_groups in hooks.items():
        if not isinstance(matcher_groups, list):
            raise ValueError(f"{path}: hooks.{event} must be an array, got {type(matcher_groups).__name__}")
        for index, group in enumerate(matcher_groups):
            if not isinstance(group, dict):
                raise ValueError(
                    f"{path}: hooks.{event}[{index}] must be an object, got {type(group).__name__}"
                )
            group_hooks = group.get("hooks")
            if group_hooks is None:
                continue
            if not isinstance(group_hooks, list):
                raise ValueError(
                    f"{path}: hooks.{event}[{index}].hooks must be an array, got {type(group_hooks).__name__}"
                )
            for hook_index, hook in enumerate(group_hooks):
                if not isinstance(hook, dict):
                    raise ValueError(
                        f"{path}: hooks.{event}[{index}].hooks[{hook_index}] must be an object, "
                        f"got {type(hook).__name__}"
                    )
    return hooks


def load_apm_entries(target: Path) -> dict[str, list[Any]]:
    """Return matcher groups already present in an existing deploy target.

    A group here may duplicate something hooks.base.json/hooks.local.json
    also declares (harmless: `merge_hooks`'s dedup collapses it), or it may
    have been written by something outside this profile (e.g. `apm install
    -g` deploying a package's own hooks fragment straight into the deploy
    target). It's preserved so regenerating the file doesn't drop it. Packages
    are not expected to tag what they write, so this is not a tag lookup.
    Profile-managed Ponytail entries are removed separately.

    Symlinks are followed rather than skipped: legacy deployments pointed
    `target` at a profile-managed hooks.json into which `apm install -g`
    had already written entries, and those must survive the first
    `mise run link` after migration. If the symlink target does not exist,
    treat it as empty and continue. A target that fails to parse as JSON is
    also treated as empty (e.g. a dangling symlink). A target that parses
    but has a malformed hooks structure is likewise treated as empty, but
    warns on stderr first: silently dropping it would erase every
    externally-managed hook the target currently holds, not just the
    malformed part.
    """
    if not target.is_file():
        return {}
    try:
        return load_hooks(target)
    except json.JSONDecodeError:
        return {}
    except ValueError as error:
        print(f"render_hooks.py: warning: ignoring malformed {target}: {error}", file=sys.stderr)
        return {}


def merge_hooks_with_attribution(
    named_sources: list[tuple[str, dict[str, list[Any]]]],
) -> tuple[dict[str, list[Any]], dict[str, list[Any]]]:
    """Merge hook sources in order, deduplicating exact-duplicate matcher groups.

    Returns the merged hooks plus, for each named source, the list of groups it
    actually contributed post-dedup (a group already contributed by an earlier
    source is attributed there, not to later sources that repeat it).
    """
    merged: dict[str, list[Any]] = {}
    contributed: dict[str, list[Any]] = {name: [] for name, _ in named_sources}
    for name, source in named_sources:
        for event, matcher_groups in source.items():
            bucket = merged.setdefault(event, [])
            for group in matcher_groups:
                if group not in bucket:
                    bucket.append(group)
                    contributed[name].append(group)
    return merged, contributed


def merge_hooks(*sources: dict[str, list[Any]]) -> dict[str, list[Any]]:
    merged, _ = merge_hooks_with_attribution([(str(index), source) for index, source in enumerate(sources)])
    return merged


def render(profile_path: Path, target: Path) -> dict[str, Any]:
    base = load_hooks(profile_path / "hooks.base.json")
    local = load_hooks(profile_path / "hooks.local.json")
    apm = remove_profile_managed_ponytail_hooks(load_apm_entries(target), [base, local])
    return {"hooks": merge_hooks(base, local, apm)}


def _render_source_label(value: Any) -> str:
    """Render `_apm_source` as a single display-safe line.

    Non-string values, and strings containing newlines or other control
    characters, are rendered via `json.dumps` so a hostile value can't break
    the one-entry-per-line breakdown display.
    """
    if isinstance(value, str) and value.isprintable():
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def format_sources(profile_path: Path, target: Path) -> list[str]:
    """Describe what hooks.base.json / hooks.local.json / apm each contributed.

    Counts reflect what actually survives `merge_hooks`'s dedup, not raw entries
    per file: a group already contributed by an earlier source (e.g. present in
    both base and local, or duplicated within base itself) is not double-counted
    against later sources.
    """
    base_path = profile_path / "hooks.base.json"
    local_path = profile_path / "hooks.local.json"
    base = load_hooks(base_path)
    local = load_hooks(local_path)
    apm = remove_profile_managed_ponytail_hooks(load_apm_entries(target), [base, local])

    _, contributed = merge_hooks_with_attribution(
        [
            ("hooks.base.json", base),
            ("hooks.local.json", local),
            ("apm", apm),
        ]
    )

    lines: list[str] = []
    for filename, source_path in (("hooks.base.json", base_path), ("hooks.local.json", local_path)):
        if source_path.is_file():
            lines.append(f"{filename}: {len(contributed[filename])} entries")
        else:
            lines.append(f"{filename}: (not present)")

    apm_counts: dict[str, int] = {}
    for group in contributed["apm"]:
        # Packages are not expected to tag what they write; only report a
        # `_apm_source` breakdown for the groups that happen to carry one.
        label = f"_apm_source={_render_source_label(group['_apm_source'])}" if "_apm_source" in group else "untracked by profile"
        apm_counts[label] = apm_counts.get(label, 0) + 1

    if apm_counts:
        for label in sorted(apm_counts):
            lines.append(f"apm ({label}): {apm_counts[label]} entries")
    else:
        lines.append("apm: (not present)")

    return lines


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
    parser.add_argument("--list-sources", action="store_true", help="print the composition breakdown and exit")
    args = parser.parse_args()

    if args.list_sources:
        try:
            for line in format_sources(args.profile_path, args.target):
                print(line)
        except Exception as error:
            print(f"render_hooks.py: {error}", file=sys.stderr)
            return 1
        return 0

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
