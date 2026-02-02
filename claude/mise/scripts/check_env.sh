#!/bin/bash

#MISE description="現在有効な VSCode 設定ファイルのパスを特定する関数を提供します。"
#MISE shell="bash -c"
#MISE quiet=true
#MISE hide=true

set -eu

# ~/.claude ディレクトリが存在しない場合は作成する
if [ ! -d "${HOME}/.claude" ]; then
  mkdir -p "${HOME}/.claude"
fi

# 必要な環境変数があれば OK
if [ -n "${DEFAULT_CLAUDE_PROFILE:-}" ] && [ -n "${WSL_CLAUDE_PROFILE:-}" ]; then
  exit 0
fi

# 環境変数が設定されていない場合は、ホスト名や WSL 判定に基づいてデフォルト値を判定する
if $IS_WSL; then
  default_claude_profile="wsl-ubuntu"
  wsl_claude_profile="wsl-ubuntu"
else
  case $(hostname) in
  *"15034")
    default_claude_profile="win-15034"
    ;;
  *"15365")
    default_claude_profile="cg-m2-mac"
    ;;
  *"-2nd")
    default_claude_profile="hm-m1-mac"
    ;;
  *)
    default_claude_profile=""
    ;;
  esac
  wsl_claude_profile="wsl-ubuntu"
fi

local_toml="${MISE_CONFIG_ROOT}/mise.local.toml"

# mise.local.toml が存在しない場合は作成する
if [ ! -e "${local_toml}" ]; then
  {
    printf "%s\n" '[env]'
    printf "%s\n" "DEFAULT_CLAUDE_PROFILE = \"\""
    printf "%s\n" "WSL_CLAUDE_PROFILE = \"\""
  } >"${local_toml}"
  printf "%s\n" "🚨 '${local_toml}' を作成しました。"
fi

# 必要な環境変数が設定されていない場合は追記する
if [ -z "${DEFAULT_CLAUDE_PROFILE:-}" ]; then
  sed -i "s/^DEFAULT_CLAUDE_PROFILE.*/DEFAULT_CLAUDE_PROFILE = \"${default_claude_profile}\"/" "${local_toml}"
fi
if [ -z "${WSL_CLAUDE_PROFILE:-}" ]; then
  sed -i "s/^WSL_CLAUDE_PROFILE.*/WSL_CLAUDE_PROFILE = \"${wsl_claude_profile}\"/" "${local_toml}"
fi

# 最終的に必要な環境変数が設定されていない場合はエラーとする
if [[ -z "${DEFAULT_CLAUDE_PROFILE:-}" ]]; then
  if [[ -z "${default_claude_profile}" ]]; then
    printf "%s\n" "🚨 'DEFAULT_CLAUDE_PROFILE' を '${local_toml}' に設定してください。"
  else
    printf "%s\n" "🚨 'DEFAULT_CLAUDE_PROFILE' に '${default_claude_profile}' を設定しました。再実行したら正しく読み込まれます。"
  fi
fi
if [[ -z "${WSL_CLAUDE_PROFILE:-}" ]]; then
  if [[ -z "${wsl_claude_profile}" ]]; then
    printf "%s\n" "🚨 'WSL_CLAUDE_PROFILE' を '${local_toml}' に設定してください。"
  else
    printf "%s\n" "🚨 'WSL_CLAUDE_PROFILE' に '${wsl_claude_profile}' を設定しました。再実行したら正しく読み込まれます。"
  fi
fi
exit 1
