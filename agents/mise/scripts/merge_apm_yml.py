#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""active profile の apm.yml に private overlay を重ねて stdout に出力する。

usage:
    uv run merge_apm_yml.py --base <path> [--overlay <path>]

base のキー順 / メタ情報 (name, version, targets 等) は保持し、
overlay からは dependencies.apm / dependencies.mcp のみ追記する。
overlay が存在しない・空のときは base をそのまま出力する。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SystemExit(f"❌ {path} のトップレベルが mapping ではありません")
    return data


def _merge_dep_list(base_list, overlay_list) -> list:
    seen = set()
    merged = []
    for item in (base_list or []) + (overlay_list or []):
        key = item if isinstance(item, str) else yaml.safe_dump(item, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def merge(base: dict, overlay: dict) -> dict:
    if not overlay:
        return base
    merged = dict(base)
    base_deps = base.get("dependencies") or {}
    overlay_deps = overlay.get("dependencies") or {}
    merged_deps = dict(base_deps)
    for key in ("apm", "mcp"):
        merged_deps[key] = _merge_dep_list(base_deps.get(key), overlay_deps.get(key))
    merged["dependencies"] = merged_deps
    return merged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--overlay", type=Path)
    args = parser.parse_args()

    base = _load(args.base)
    overlay = _load(args.overlay) if args.overlay and args.overlay.is_file() else {}
    result = merge(base, overlay)

    yaml.safe_dump(
        result,
        sys.stdout,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
