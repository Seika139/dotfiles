#!/bin/bash

#MISE description="現在のプロファイル設定と install 状況を確認"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

PROFILE="${usage_prof:-${DEFAULT_AGENTS_PROFILE:-}}"
PROFILE_PATH="${ROOT_DIR}/$PROFILES_DIR/$PROFILE"
PRIVATE_PATH="${ROOT_DIR}/$PROFILES_DIR/private"
PRIVATE_YML="$PRIVATE_PATH/apm.yml"
PRIVATE_LOCK="$PRIVATE_PATH/apm.lock.yaml"
HAS_PRIVATE=false
if [ -f "$PRIVATE_YML" ]; then
  HAS_PRIVATE=true
fi

printf "%s\n" "🦄 Environment Check"
printf "OS                   =\\033[36m %s\\033[0m\n" "$(uname -s)"
printf "IS_WSL               =\\033[36m %s\\033[0m\n" "$IS_WSL"
printf "config_root          =\\033[36m %s\\033[0m\n" "${ROOT_DIR}"
printf "Selected profile     =\\033[36m %s\\033[0m\n" "$PROFILE"
printf "Profile path         =\\033[36m %s\\033[0m\n" "$PROFILE_PATH"
if [ "$HAS_PRIVATE" = "true" ]; then
  printf "Private overlay      =\\033[36m %s\\033[0m\n" "$PRIVATE_YML"
else
  printf "Private overlay      =\\033[2m (none)\\033[0m\n"
fi

if [ ! -d "$PROFILE_PATH" ]; then
  printf "❌ Profile directory does not exist:\\033[36m %s\\033[0m\n" "$PROFILE_PATH"
  exit 1
fi

printf "\n📂 apm.yml dependencies (base):\n"
if [ -f "$PROFILE_PATH/apm.yml" ]; then
  grep -E '^[[:space:]]*-[[:space:]]+' "$PROFILE_PATH/apm.yml" | sed 's/^/  /' || true
else
  printf "\\033[31m%s\\033[0m\n" "   ❌ apm.yml does not exist"
fi

if [ "$HAS_PRIVATE" = "true" ]; then
  printf "\n📂 apm.yml dependencies (private overlay):\n"
  grep -E '^[[:space:]]*-[[:space:]]+' "$PRIVATE_YML" | sed 's/^/  /' || true
fi

printf "\n🔒 apm.lock.yaml:\n"
if [ "$HAS_PRIVATE" = "true" ]; then
  if [ -f "$PRIVATE_LOCK" ]; then
    printf "   ✅ %s (gitignored)\n" "$PRIVATE_LOCK"
  else
    printf "\\033[33m%s\\033[0m\n" "   ⚠️ private overlay 有効だが lock 未生成 (run 'mise run install')"
  fi
elif [ -f "$PROFILE_PATH/apm.lock.yaml" ]; then
  printf "   ✅ %s\n" "$PROFILE_PATH/apm.lock.yaml"
else
  printf "\\033[33m%s\\033[0m\n" "   ⚠️ not generated yet (run 'mise run install')"
fi

printf "\n🌐 Installed at user scope:\n"
printf "   ~/.claude/skills/:\n"
ls -1 "$HOME/.claude/skills" 2>/dev/null | sed 's/^/     - /' || printf "     (none)\n"
printf "   ~/.codex/skills/:\n"
ls -1 "$HOME/.codex/skills" 2>/dev/null | sed 's/^/     - /' || printf "     (none)\n"
printf "   ~/.gemini/skills/:\n"
ls -1 "$HOME/.gemini/skills" 2>/dev/null | sed 's/^/     - /' || printf "     (none)\n"

printf "\n💡 Commands:\n"
printf "   install : mise run install [--prof <profile>]\n"
printf "   update  : mise run update  [--prof <profile>]\n"
printf "   list    : mise run list\n"
