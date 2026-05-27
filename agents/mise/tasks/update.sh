#!/bin/bash

#MISE description="指定プロファイルの apm dependencies を最新 ref に更新し再 install する (lock 更新)"
#MISE depends=["check"]
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
PROFILE_PATH="${ROOT_DIR}/$PROFILES_DIR/$PROFILE"

if ! command -v apm &>/dev/null; then
  printf "%s\n" "🚨 'apm' CLI が見つかりません。" >&2
  exit 1
fi

printf "%s\n" "🦄 Updating APM packages from profile: $PROFILE"

cd "$PROFILE_PATH"
apm update --yes

printf "%s\n" "✅ Updated APM dependencies for profile '$PROFILE'"
printf "%s\n" "   次に 'mise run install' で user scope に反映してください"
