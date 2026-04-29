#!/usr/bin/env python3
"""Generate Codex command skills from profile prompt files.

Codex CLI currently loads custom reusable workflows from skills, not from
profile-level prompts. This script keeps Claude-style command prompt files as
the source material and exposes them as `$skill-name` command skills.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


MARKER_PREFIX = "<!-- codex-profile-generated-from-prompt:"
MAX_DESCRIPTION_LEN = 1024


def split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---"):
        return None, text

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            frontmatter = "".join(lines[1:index])
            body = "".join(lines[index + 1 :])
            return frontmatter, body

    return None, text


def extract_scalar(frontmatter: str | None, key: str) -> str | None:
    if not frontmatter:
        return None

    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$")
    for line in frontmatter.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        value = match.group(1).strip()
        if value in {">", "|", ">-", "|-"}:
            return None
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value.startswith(("'", '"'))
        ):
            value = value[1:-1]
        return " ".join(value.split())

    return None


def first_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        match = re.match(r"^\s{0,3}#\s+(.+?)\s*$", line)
        if match:
            return " ".join(match.group(1).split())
    return None


def skill_name_from_prompt(prompt_path: Path, prompts_dir: Path) -> str:
    rel = prompt_path.relative_to(prompts_dir).with_suffix("").as_posix()
    name = rel.replace("/", "-").replace("_", "-").lower()
    name = re.sub(r"[^a-z0-9-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "prompt-skill"


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def limit_description(value: str) -> str:
    value = " ".join(value.split())
    if len(value) <= MAX_DESCRIPTION_LEN:
        return value
    return value[: MAX_DESCRIPTION_LEN - 1].rstrip() + "…"


def generated_skill_body(
    *,
    skill_name: str,
    description: str,
    short_description: str,
    legacy_command: str,
    prompt_rel: str,
    prompt_body: str,
) -> str:
    return f"""---
name: {yaml_quote(skill_name)}
description: {yaml_quote(description)}
metadata:
  short-description: {yaml_quote(short_description)}
---

{MARKER_PREFIX} {prompt_rel} -->

# {skill_name}

この skill は Claude command `{legacy_command}` から変換した Codex 用 command skill です。

## Codex での呼び出し

Codex CLI では `{legacy_command}` ではなく、`${skill_name}` または `/skills` からこの skill を呼び出してください。
引数は `${skill_name}` の後ろに自然文として続けます。

```text
${skill_name} <arguments>
```

元 prompt 内の `$ARGUMENTS` や slash command 表記は、`${skill_name}` の後ろに書かれた引数として解釈してください。
Claude 専用の `allowed-tools` メタデータや `!` command interpolation は Codex では自動適用されないため、必要な情報は通常の shell command で確認してください。

## 元 prompt

{prompt_body.lstrip()}
"""


def sync_profile(profile_path: Path) -> tuple[int, int, int]:
    prompts_dir = profile_path / "prompts"
    skills_dir = profile_path / "skills"

    if not prompts_dir.is_dir():
        return (0, 0, 0)

    skills_dir.mkdir(parents=True, exist_ok=True)

    created_or_updated = 0
    skipped = 0
    unchanged = 0
    prompt_rel_paths: set[str] = set()

    for prompt_path in sorted(prompts_dir.rglob("*.md")):
        frontmatter, body = split_frontmatter(prompt_path.read_text())
        rel = prompt_path.relative_to(prompts_dir).with_suffix("").as_posix()
        legacy_command = "/" + rel
        skill_name = skill_name_from_prompt(prompt_path, prompts_dir)

        prompt_description = extract_scalar(frontmatter, "description")
        prompt_name = extract_scalar(frontmatter, "name")
        heading = first_heading(body)
        short_description = prompt_description or heading or prompt_name or legacy_command
        description = limit_description(
            f"{short_description}。Claude command {legacy_command} 相当を Codex CLI で実行する。"
        )

        target_dir = skills_dir / skill_name
        target_path = target_dir / "SKILL.md"
        prompt_rel = prompt_path.relative_to(profile_path).as_posix()
        prompt_rel_paths.add(prompt_rel)
        next_body = generated_skill_body(
            skill_name=skill_name,
            description=description,
            short_description=limit_description(short_description),
            legacy_command=legacy_command,
            prompt_rel=prompt_rel,
            prompt_body=body,
        )

        if target_path.exists():
            current = target_path.read_text()
            if MARKER_PREFIX not in current:
                skipped += 1
                continue
            if current == next_body:
                unchanged += 1
                continue

        target_dir.mkdir(parents=True, exist_ok=True)
        target_path.write_text(next_body)
        created_or_updated += 1

    for skill_path in sorted(skills_dir.glob("*/SKILL.md")):
        current = skill_path.read_text()
        prompt_rel = generated_prompt_rel(current)
        if prompt_rel is None or prompt_rel in prompt_rel_paths:
            continue

        skill_path.unlink()
        try:
            skill_path.parent.rmdir()
        except OSError:
            pass
        created_or_updated += 1

    return (created_or_updated, skipped, unchanged)


def generated_prompt_rel(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith(MARKER_PREFIX) or not line.endswith("-->"):
            continue
        return line[len(MARKER_PREFIX) : -3].strip()
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-path", type=Path, required=True)
    args = parser.parse_args()

    changed, skipped, unchanged = sync_profile(args.profile_path)
    print(
        "Synced prompt command skills: "
        f"{changed} changed, {unchanged} unchanged, {skipped} skipped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
