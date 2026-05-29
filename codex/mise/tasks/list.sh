#!/usr/bin/env bash

#MISE description="利用可能なプロファイル一覧を表示"
#MISE depends=["check_env"]
#MISE quiet=true

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

PROFILES_PATH="$(codex_profiles_path "$ROOT_DIR")"
CURRENT_PROFILE="$(codex_default_profile)"

printf "%s\n" "🦄 Available Codex Profiles:"
if [ -d "$PROFILES_PATH" ]; then
  for profile in "$PROFILES_PATH"/*; do
    if [ -d "$profile" ]; then
      profile_name="$(basename "$profile")"
      if [ "$profile_name" = "$CURRENT_PROFILE" ]; then
        printf "%s\n" "   ✅ $profile_name (current)"
      else
        printf "%s\n" "   ⭕ $profile_name"
      fi
    fi
  done
else
  printf "%s\n" "   (No profiles found)"
fi

if [ -n "$CURRENT_PROFILE" ]; then
  printf "\nCurrent profile:\\033[36m %s\\033[0m\n" "$CURRENT_PROFILE"
else
  printf "%s\n" "\n⚠️ No current profile set in DEFAULT_CODEX_PROFILE"
fi
