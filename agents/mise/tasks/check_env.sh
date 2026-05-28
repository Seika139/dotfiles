#!/bin/bash

#MISE description="環境変数がちゃんと設定されているか確認する"
#MISE quiet=true
#MISE hide=true

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ ! -e "${ROOT_DIR}/mise.local.toml" ]; then
  {
    printf "%s\n" '[env]'
    printf "%s\n" 'DEFAULT_AGENTS_PROFILE=""'
  } >"${ROOT_DIR}/mise.local.toml"
  printf "%s\n" "🚨 '${ROOT_DIR}/mise.local.toml' に環境変数を設定する必要があります。"
  printf "%s\n" "🚨 必要な環境変数をデフォルトでセットしました。"
  printf "%s\n" "🚨 DEFAULT_AGENTS_PROFILE に適切なプロファイル名を設定してください。"
  exit 1
fi
if [ -z "${DEFAULT_AGENTS_PROFILE:-}" ]; then
  printf "%s\n" "🚨 'DEFAULT_AGENTS_PROFILE' を '${ROOT_DIR}/mise.local.toml' に設定してください。"
  exit 1
fi
