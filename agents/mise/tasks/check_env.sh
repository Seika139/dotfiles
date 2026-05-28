#!/bin/bash

#MISE description="環境変数がちゃんと設定されているか確認する"
#MISE quiet=true
#MISE hide=true

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ ! -e "${ROOT_DIR}/mise.local.toml" ] || ! grep -q '^DEFAULT_AGENTS_PROFILE' "${ROOT_DIR}/mise.local.toml"; then
  # dotfiles 共通で設定される active profile が存在すればそれをデフォルトで設定する
  active_profile="${DOTPATH:-$HOME/dotfiles}/.active-profile"
  default_profile=""
  if [ -e "${active_profile}" ] && [ -e "${ROOT_DIR}/profiles/$(<"$active_profile")" ]; then
    default_profile=$(<"$active_profile")
  fi
  {
    printf "%s\n" '[env]'
    printf "%s\n" "DEFAULT_AGENTS_PROFILE = \"${default_profile}\""
  } >"${ROOT_DIR}/mise.local.toml"

  if [ -z "${default_profile}" ]; then
    printf "%s\n" "🚨 '${ROOT_DIR}/mise.local.toml' に環境変数を設定する必要があります。"
    printf "%s\n" "🚨 DEFAULT_AGENTS_PROFILE に適切なプロファイル名を設定してください。"
    exit 1
  else
    printf "%s\n" "🚨 '${ROOT_DIR}/mise.local.toml' の環境変数を ${active_profile} から設定しました。"
    printf "%s\n" "🚨 もう一度同じタスクを実行してみてください。"
    exit 1
  fi
fi

if [ -z "${DEFAULT_AGENTS_PROFILE:-}" ]; then
  printf "%s\n" "🚨 'DEFAULT_AGENTS_PROFILE' を '${ROOT_DIR}/mise.local.toml' に設定してください。"
  exit 1
fi
