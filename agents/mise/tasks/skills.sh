#!/bin/bash

#MISE description="Claude / Agents にある skill を一覧・閲覧"
#MISE quiet=true

set -euo pipefail

CLAUDE_SKILLS_DIR="${HOME}/.claude/skills"
AGENTS_SKILLS_DIR="${HOME}/.agents/skills"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}")"

show_skill_file() {
  local label="$1"
  local file="$2"
  local skill_dir="${file%/SKILL.md}"

  printf '\033[1m[%s] %s\033[0m\n' "$label" "$file"
  if [ -f "$file" ]; then
    if command -v bat >/dev/null 2>&1; then
      bat --color=always --style=full --paging=never "$file"
    else
      cat "$file"
    fi
  elif [ -d "$skill_dir" ]; then
    printf '%s\n' "SKILL.md がありません。"
  else
    printf '%s\n' "skill はありません。"
  fi
}

show_skill() {
  local name="$1"

  show_skill_file "Claude" "${CLAUDE_SKILLS_DIR}/${name}/SKILL.md"
  printf '\n'
  show_skill_file "Agents" "${AGENTS_SKILLS_DIR}/${name}/SKILL.md"
}

# fzf の preview 用に同じスクリプトを再実行する。
if [ "${1:-}" = "--preview" ]; then
  if [ -n "${2:-}" ]; then
    show_skill "$2"
  fi
  exit 0
fi

if ! command -v fzf >/dev/null 2>&1; then
  printf '%s\n' "このタスクを使うには fzf をインストールし、PATH に追加してください。" >&2
  exit 1
fi

skill_names=()
for skills_dir in "$CLAUDE_SKILLS_DIR" "$AGENTS_SKILLS_DIR"; do
  [ -d "$skills_dir" ] || continue
  for skill_dir in "$skills_dir"/*; do
    [ -d "$skill_dir" ] || continue
    skill_names+=("${skill_dir##*/}")
  done
done

if [ "${#skill_names[@]}" -eq 0 ]; then
  printf '%s\n' "Claude / Agents の skills ディレクトリに skill がありません。"
  exit 0
fi

sorted_skill_names=()
while IFS= read -r skill_name; do
  [ -n "$skill_name" ] || continue
  sorted_skill_names+=("$skill_name")
done < <(printf '%s\n' "${skill_names[@]}" | LC_ALL=C sort -u)
skill_names=("${sorted_skill_names[@]}")

candidates=()
for name in "${skill_names[@]}"; do
  claude_skill_dir="${CLAUDE_SKILLS_DIR}/${name}"
  agents_skill_dir="${AGENTS_SKILLS_DIR}/${name}"
  missing_locations=""

  if [ -d "$claude_skill_dir" ]; then
    claude_status=$'\033[32m✓\033[0m'
    if [ ! -f "${claude_skill_dir}/SKILL.md" ]; then
      missing_locations="Claude"
    fi
  else
    claude_status=$'\033[31m✘\033[0m'
  fi

  if [ -d "$agents_skill_dir" ]; then
    agents_status=$'\033[32m✓\033[0m'
    if [ ! -f "${agents_skill_dir}/SKILL.md" ]; then
      if [ -n "$missing_locations" ]; then
        missing_locations+=", "
      fi
      missing_locations+="Agents"
    fi
  else
    agents_status=$'\033[31m✘\033[0m'
  fi

  missing_note=""
  if [ -n "$missing_locations" ]; then
    missing_note=$'\033[33mSKILL.mdなし ('"${missing_locations}"$')\033[0m'
  fi

  candidates+=("${claude_status}"$'\t'"${agents_status}"$'\t'"${name}"$'\t'"${missing_note}"$'\t'"${name}")
done

preview_command="$(printf '%q --preview {5}' "$SCRIPT_PATH")"
if selected="$(printf '%s\n' "${candidates[@]}" | fzf \
  --ansi \
  --delimiter=$'\t' \
  --with-nth='1,2,3,4' \
  --header='Claude  Agents  スキル名  (Enter: 表示、Esc: 終了)' \
  --preview "$preview_command" \
  --preview-window='right:65%:wrap')"; then
  selected_name="${selected##*$'\t'}"
  if [ -n "$selected_name" ]; then
    printf '\n'
    show_skill "$selected_name"
  fi
else
  fzf_status=$?
  if [ "$fzf_status" -eq 1 ] || [ "$fzf_status" -eq 130 ]; then
    exit 0
  fi
  exit "$fzf_status"
fi
