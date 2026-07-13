#!/usr/bin/env python3
"""Validate the minimal native Codex agent contract."""
import argparse
import sys
import tomllib
from pathlib import Path

REQUIRED = {"name", "description", "developer_instructions", "model", "model_reasoning_effort"}
READ_ONLY = {"architecture-reviewer", "cheap-researcher", "code-reviewer", "security-reviewer"}
ALLOWED_REASONING_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
ALLOWED_SANDBOX_MODES = {"read-only", "workspace-write", "danger-full-access"}


def validate(directory: Path) -> list[str]:
    errors = []
    for path in sorted(directory.glob("*.toml")):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"{path}: TOML を読み込めません: {exc}")
            continue
        missing = REQUIRED - data.keys()
        if missing:
            errors.append(f"{path}: 必須キー不足: {', '.join(sorted(missing))}")
        for key in ("name", "description", "developer_instructions", "model"):
            value = data.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{path}: {key} は空でない文字列にしてください")
        reasoning_effort = data.get("model_reasoning_effort")
        if not isinstance(reasoning_effort, str) or reasoning_effort not in ALLOWED_REASONING_EFFORTS:
            errors.append(
                f"{path}: model_reasoning_effort は {', '.join(sorted(ALLOWED_REASONING_EFFORTS))} のいずれかにしてください"
            )
        sandbox_mode = data.get("sandbox_mode")
        if sandbox_mode is not None and (not isinstance(sandbox_mode, str) or sandbox_mode not in ALLOWED_SANDBOX_MODES):
            errors.append(
                f"{path}: sandbox_mode は {', '.join(sorted(ALLOWED_SANDBOX_MODES))} のいずれかにしてください"
            )
        if data.get("name") != path.stem:
            errors.append(f"{path}: name はファイル名と一致させてください")
        if path.stem in READ_ONLY and sandbox_mode != "read-only":
            errors.append(f"{path}: 読み取り専用 agent は sandbox_mode = \"read-only\" にしてください")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    errors = validate(args.directory)
    for error in errors:
        print(f"❌ {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"agent definitions valid: {len(list(args.directory.glob('*.toml')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
