#!/usr/bin/env bash

#MISE description="プロファイルを切り替えてシンボリックリンクを更新 (Usage: mise run switch [--prof <profile-name>])"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="切り替え先のプロファイル名"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

NEW_PROFILE="${usage_prof:-}"
if [ -z "$NEW_PROFILE" ]; then
  PROFILES_PATH="$(codex_profiles_path "$ROOT_DIR")"
  if [ ! -d "$PROFILES_PATH" ] || [ -z "$(ls -A "$PROFILES_PATH" 2>/dev/null)" ]; then
    printf "%s\n" "❌ Error: No profiles found in $PROFILES_PATH" >&2
    exit 1
  fi
  if command -v fzf >/dev/null 2>&1 && [ -t 0 ]; then
    NEW_PROFILE="$(find "$PROFILES_PATH" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort | fzf --prompt="Select Codex profile: " --height=~50% --reverse)"
    if [ -z "$NEW_PROFILE" ]; then
      printf "%s\n" "❌ cancelled."
      exit 1
    fi
  else
    {
      printf "%s\n" "❌ Error: profile name is required."
      printf "%s\n" "   Usage: mise run switch --prof <profile-name>"
      printf "%s\n" "   Available profiles:"
      find "$PROFILES_PATH" -mindepth 1 -maxdepth 1 -type d -printf '     - %f\n' | sort
    } >&2
    exit 1
  fi
fi

mise run check --prof "$NEW_PROFILE"

LOCAL_CONFIG="${ROOT_DIR}/mise.local.toml"
if codex_is_wsl; then
  {
    printf "%s\n" '[env]'
    printf "%s\n" "DEFAULT_CODEX_PROFILE = \"${DEFAULT_CODEX_PROFILE:-}\""
    printf "%s\n" "WSL_CODEX_PROFILE = \"$NEW_PROFILE\""
  } >"$LOCAL_CONFIG"
else
  {
    printf "%s\n" '[env]'
    printf "%s\n" "DEFAULT_CODEX_PROFILE = \"$NEW_PROFILE\""
    printf "%s\n" "WSL_CODEX_PROFILE = \"${WSL_CODEX_PROFILE:-}\""
  } >"$LOCAL_CONFIG"
fi

printf "%s\n" "🦄 Switching Codex profile to: $NEW_PROFILE"

mise run link --prof "$NEW_PROFILE"

printf "%s\n" "✅ Switched to profile '$NEW_PROFILE'"
printf "%s\n" "🔄 Please restart your shell or run 'mise env' to reload environment variables"
