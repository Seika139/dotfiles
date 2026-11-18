#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! git config --global --includes --get-regexp '^secrets\.(patterns|providers)$' >/dev/null 2>&1; then
  printf '%s\n' "git-secrets のグローバル設定がありません。各PCの ~/.gitconfig.local に secrets.patterns または secrets.providers を登録してください。" >&2
  exit 1
fi

exec git secrets --scan --cached --
