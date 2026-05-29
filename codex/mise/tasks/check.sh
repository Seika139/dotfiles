#!/usr/bin/env bash

#MISE description="指定プロファイルが存在するかを確認し、なければエラーを返す"
#MISE depends=["check_env"]
#MISE quiet=true
#MISE hide=true
#USAGE flag "--prof <prof>" help="プロファイル名"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

PROFILE="$(codex_profile_or_default "${usage_prof:-}")"
printf "Using profile: \\033[36m%s\\033[0m\n" "$PROFILE"
if [ -z "$PROFILE" ]; then
  printf "%s\n" "❌ Error: DEFAULT_CODEX_PROFILE is not set in environment variables" >&2
  exit 1
fi

PROFILE_PATH="$(codex_profile_path "$ROOT_DIR" "$PROFILE")"

if [ ! -d "$PROFILE_PATH" ]; then
  {
    printf "%s\n" "❌ Error: Profile directory '$PROFILE_PATH' does not exist"
    printf "%s\n" "   Available profiles:"
    PROFILES_PATH="$(codex_profiles_path "$ROOT_DIR")"
    if [ -d "$PROFILES_PATH" ]; then
      for entry in "$PROFILES_PATH"/*; do
        [ -e "$entry" ] || continue
        printf "   - %s\n" "${entry##*/}"
      done
    else
      printf "%s\n" "   (No profiles directory found)"
    fi
  } >&2
  exit 1
fi
