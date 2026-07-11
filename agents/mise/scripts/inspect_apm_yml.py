#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""apm.yml (+ optional private overlay) を解析し、status 表示用のフィールドを抽出する。

stdout に prefix-tagged な TSV を 1 行 1 件で出力する:

    target	<name>            base の targets
    apm-base	<pkg>           base の dependencies.apm から抽出した package 名
    apm-overlay	<pkg>           overlay の dependencies.apm から抽出した package 名
    apm-merged	<pkg>           base + overlay を dedup したあとの package 名

package 名抽出ルール: string form の ref または object form の path が
".../packages/<name>" 形式なら <name>、それ以外は入力を文字列化して返す。
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


def _name_from_path(path: str) -> str:
    head = path.split("#", 1)[0].replace("\\", "/").strip("/")
    if head.startswith("packages/"):
        return head.removeprefix("packages/").strip("/")
    if "/packages/" in head:
        return head.rsplit("/packages/", 1)[-1].strip("/")
    return head


def _pkg_name(ref) -> str:
    if isinstance(ref, str):
        return _name_from_path(ref)
    if isinstance(ref, dict) and isinstance(ref.get("path"), str):
        return _name_from_path(ref["path"])
    return yaml.safe_dump(ref, sort_keys=True, default_flow_style=True).strip()


def _apm_list(doc: dict) -> list:
    return ((doc.get("dependencies") or {}).get("apm")) or []


def _dedup(items) -> list:
    seen = set()
    out = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--overlay", type=Path)
    args = parser.parse_args()

    base = _load(args.base)
    overlay = _load(args.overlay) if args.overlay and args.overlay.is_file() else {}

    for tgt in base.get("targets") or []:
        print(f"target\t{tgt}")

    base_names = [_pkg_name(r) for r in _apm_list(base)]
    overlay_names = [_pkg_name(r) for r in _apm_list(overlay)]

    for n in base_names:
        print(f"apm-base\t{n}")
    for n in overlay_names:
        print(f"apm-overlay\t{n}")
    for n in _dedup(base_names + overlay_names):
        print(f"apm-merged\t{n}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
