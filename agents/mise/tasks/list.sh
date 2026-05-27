#!/bin/bash

#MISE description="利用可能なプロファイル一覧を表示"
#MISE depends=["check_env"]
#MISE quiet=true

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

PROFILES_PATH="${ROOT_DIR}/$PROFILES_DIR"

if [ "$IS_WSL" = "true" ]; then
  CURRENT_PROFILE="${WSL_AGENTS_PROFILE:-}"
else
  CURRENT_PROFILE="${DEFAULT_AGENTS_PROFILE:-}"
fi

printf "%s\n" "🦄 Available Agents (APM) Profiles:"
if [ -d "$PROFILES_PATH" ]; then
  for profile in "$PROFILES_PATH"/*; do
    if [ -d "$profile" ]; then
      profile_name=$(basename "$profile")
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
  printf "%s\n" "\n⚠️ No current profile set in DEFAULT_AGENTS_PROFILE"
fi
