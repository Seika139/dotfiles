#!/bin/bash

#MISE description="現在有効な VSCode 設定ファイルのパスを特定する関数を提供します。"
#MISE shell="bash -c"
#MISE quiet=true
#MISE hide=true

set -eu

# ~/.codex ディレクトリが存在しない場合は作成する
if [ ! -d "${HOME}/.codex" ]; then
  mkdir -p "${HOME}/.codex"
fi

# 必要な環境変数があれば OK
if [ -n "${DEFAULT_CODEX_PROFILE:-}" ] && [ -n "${WSL_CODEX_PROFILE:-}" ]; then
  exit 0
fi

# 環境変数が設定されていない場合は、ホスト名や WSL 判定に基づいてデフォルト値を判定する
if $IS_WSL; then
  default_codex_profile="wsl-ubuntu"
  wsl_codex_profile="wsl-ubuntu"
else
  case $(hostname) in
  *"15034")
    default_codex_profile="win-15034"
    ;;
  *"15365")
    default_codex_profile="cg-m2-mac"
    ;;
  *)
    default_codex_profile=""
    ;;
  esac
  wsl_codex_profile="wsl-ubuntu"
fi

local_toml="${MISE_CONFIG_ROOT}/mise.local.toml"

# mise.local.toml が存在しない場合は作成する
if [ ! -e "${local_toml}" ]; then
  {
    printf "%s\n" '[env]'
    printf "%s\n" "DEFAULT_CODEX_PROFILE = \"\""
    printf "%s\n" "WSL_CODEX_PROFILE = \"\""
  } >"${local_toml}"
  printf "%s\n" "🚨 '${local_toml}' を作成しました。"
fi

# 必要な環境変数が設定されていない場合は追記する
if [ -z "${DEFAULT_CODEX_PROFILE:-}" ]; then
  sed -i "s/^DEFAULT_CODEX_PROFILE.*/DEFAULT_CODEX_PROFILE = \"${default_codex_profile}\"/" "${local_toml}"
fi
if [ -z "${WSL_CODEX_PROFILE:-}" ]; then
  sed -i "s/^WSL_CODEX_PROFILE.*/WSL_CODEX_PROFILE = \"${wsl_codex_profile}\"/" "${local_toml}"
fi

# 最終的に必要な環境変数が設定されていない場合はエラーとする
if [[ -z "${DEFAULT_CODEX_PROFILE:-}" ]]; then
  if [[ -z "${default_codex_profile}" ]]; then
    printf "%s\n" "🚨 'DEFAULT_CODEX_PROFILE' を '${local_toml}' に設定してください。"
  else
    printf "%s\n" "🚨 'DEFAULT_CODEX_PROFILE' に '${default_codex_profile}' を設定しました。再実行したら正しく読み込まれます。"
  fi
fi
if [[ -z "${WSL_CODEX_PROFILE:-}" ]]; then
  if [[ -z "${wsl_codex_profile}" ]]; then
    printf "%s\n" "🚨 'WSL_CODEX_PROFILE' を '${local_toml}' に設定してください。"
  else
    printf "%s\n" "🚨 'WSL_CODEX_PROFILE' に '${wsl_codex_profile}' を設定しました。再実行したら正しく読み込まれます。"
  fi
fi
