#!/bin/bash

#MISE description="環境変数がちゃんと設定されているか確認する"
#MISE quiet=true
#MISE hide=true

set -euo pipefail

if [ ! -e "{{config_root}}/mise.local.toml" ]; then
  {
    printf "%s\n" '[env]'
    printf "%s\n" 'DEFAULT_AGENTS_PROFILE=""'
    printf "%s\n" 'WSL_AGENTS_PROFILE=""'
  } >"{{config_root}}/mise.local.toml"
  printf "%s\n" "🚨 '{{config_root}}/mise.local.toml' に環境変数を設定する必要があります。"
  printf "%s\n" "🚨 必要な環境変数をデフォルトでセットしました。"
  printf "%s\n" "🚨 DEFAULT_AGENTS_PROFILE と WSL_AGENTS_PROFILE に適切なプロファイル名を設定してください。"
  exit 1
fi
if [ -z "${DEFAULT_AGENTS_PROFILE:-}" ]; then
  printf "%s\n" "🚨 'DEFAULT_AGENTS_PROFILE' を '{{config_root}}/mise.local.toml' に設定してください。"
  exit 1
fi
if [ -z "${WSL_AGENTS_PROFILE:-}" ]; then
  printf "%s\n" "🚨 'WSL_AGENTS_PROFILE' を '{{config_root}}/mise.local.toml' に設定してください。（wsl を利用しない場合でも何らかの値を入れてください）"
  exit 1
fi
