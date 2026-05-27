#!/bin/bash

#MISE description="指定プロファイルが存在するかを確認し、なければエラーを返す"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ "$IS_WSL" = "true" ]; then
  DEFAULT_PROFILE="${WSL_AGENTS_PROFILE:-}"
else
  DEFAULT_PROFILE="${DEFAULT_AGENTS_PROFILE:-}"
fi
PROFILE="${usage_prof:-$DEFAULT_PROFILE}"
printf "Using profile: \\033[36m%s\\033[0m\n" "$PROFILE"
if [ -z "$PROFILE" ]; then
  printf "%s\n" "❌ Error: DEFAULT_AGENTS_PROFILE is not set in environment variables" >&2
  exit 1
fi

PROFILE_PATH="${ROOT_DIR}/$PROFILES_DIR/$PROFILE"

if [ ! -d "$PROFILE_PATH" ]; then
  {
    printf "%s\n" "❌ Error: Profile directory '$PROFILE_PATH' does not exist"
    printf "%s\n" "   Available profiles:"
    if [ -d "${ROOT_DIR}/$PROFILES_DIR" ]; then
      ls -1 "${ROOT_DIR}/$PROFILES_DIR" | sed 's/^/   - /'
    else
      printf "%s\n" "   (No profiles directory found)"
    fi
  } >&2
  exit 1
fi

if [ ! -f "$PROFILE_PATH/apm.yml" ]; then
  printf "%s\n" "❌ Error: '$PROFILE_PATH/apm.yml' が見つかりません" >&2
  exit 1
fi
