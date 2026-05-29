#!/usr/bin/env bash

#MISE description="環境変数がちゃんと設定されているか確認する"
#MISE quiet=true
#MISE hide=true

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

if [ ! -d "${HOME}/.codex" ]; then
  mkdir -p "${HOME}/.codex"
fi

if [ -n "${DEFAULT_CODEX_PROFILE:-}" ] && [ -n "${WSL_CODEX_PROFILE:-}" ]; then
  exit 0
fi

if codex_is_wsl; then
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
  *"-2nd")
    default_codex_profile="hm-m1-mac"
    ;;
  *)
    default_codex_profile=""
    ;;
  esac
  wsl_codex_profile="wsl-ubuntu"
fi

local_toml="${ROOT_DIR}/mise.local.toml"

if [ ! -e "${local_toml}" ]; then
  {
    printf "%s\n" '[env]'
    printf "%s\n" "DEFAULT_CODEX_PROFILE = \"\""
    printf "%s\n" "WSL_CODEX_PROFILE = \"\""
  } >"${local_toml}"
  printf "%s\n" "🚨 '${local_toml}' を作成しました。"
fi

if [ -z "${DEFAULT_CODEX_PROFILE:-}" ]; then
  sed "s/^DEFAULT_CODEX_PROFILE.*/DEFAULT_CODEX_PROFILE = \"${default_codex_profile}\"/" \
    "${local_toml}" >"${local_toml}.tmp" &&
    mv "${local_toml}.tmp" "${local_toml}"
fi
if [ -z "${WSL_CODEX_PROFILE:-}" ]; then
  sed "s/^WSL_CODEX_PROFILE.*/WSL_CODEX_PROFILE = \"${wsl_codex_profile}\"/" \
    "${local_toml}" >"${local_toml}.tmp" &&
    mv "${local_toml}.tmp" "${local_toml}"
fi

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
