#!/usr/bin/env bash

#MISE description="profile promptsをCodex command skillへ変換する"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

PROFILE="$(codex_profile_or_default "${usage_prof:-}")"
if [ -z "$PROFILE" ]; then
  printf "%s\n" "❌ Error: profile is not set" >&2
  exit 1
fi

PROFILE_PATH="$(codex_profile_path "$ROOT_DIR" "$PROFILE")"
if [ ! -d "$PROFILE_PATH" ]; then
  printf "❌ Error: Profile directory does not exist: %s\n" "$PROFILE_PATH" >&2
  exit 1
fi

SYNC_SCRIPT="${ROOT_DIR}/mise/scripts/sync_prompt_skills.py"
if [ ! -f "$SYNC_SCRIPT" ]; then
  printf "❌ Error: sync script does not exist: %s\n" "$SYNC_SCRIPT" >&2
  exit 1
fi

"$SYNC_SCRIPT" --profile-path "$PROFILE_PATH"
