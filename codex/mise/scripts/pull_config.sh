#!/bin/bash

set -eu

if [ "${MISE_CONFIG_ROOT:-}" = "" ]; then
  MISE_CONFIG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi

PROFILES_DIR="${PROFILES_DIR:-profiles}"
local_toml="${MISE_CONFIG_ROOT}/mise.local.toml"

if [ "${IS_WSL:-}" = "" ]; then
  if [ "$(uname -s)" = "Linux" ] && [ -f /proc/version ] && grep -qi microsoft /proc/version; then
    IS_WSL=true
  else
    IS_WSL=false
  fi
fi

read_local_value() {
  key="$1"
  if [ -f "$local_toml" ]; then
    grep "^${key}" "$local_toml" 2>/dev/null | cut -d'"' -f2 || true
  fi
}

if $IS_WSL; then
  auto_detect_profile="${WSL_CODEX_PROFILE:-}"
  if [ -z "$auto_detect_profile" ]; then
    auto_detect_profile="$(read_local_value WSL_CODEX_PROFILE)"
  fi
else
  auto_detect_profile="${DEFAULT_CODEX_PROFILE:-}"
  if [ -z "$auto_detect_profile" ]; then
    auto_detect_profile="$(read_local_value DEFAULT_CODEX_PROFILE)"
  fi
fi

option_profile=""
while [ $# -gt 0 ]; do
  case "$1" in
  --prof)
    if [ $# -lt 2 ]; then
      printf "%s\n" "🚨 --prof requires a profile name." >&2
      exit 1
    fi
    option_profile="$2"
    shift 2
    ;;
  *)
    if [ -z "$option_profile" ] && [ "${1#-}" = "$1" ]; then
      option_profile="$1"
    fi
    shift
    ;;
  esac
done

PROFILE=$([ -n "$option_profile" ] && echo "$option_profile" || echo "$auto_detect_profile")

if [ -z "$PROFILE" ]; then
  printf "%s" "🚨 プロファイルが指定されていません。"
  printf "%s" "--prof オプションでプロファイルを指定するか、mise.local.toml に "
  printf "%s\n" "DEFAULT_CODEX_PROFILE または WSL_CODEX_PROFILE を設定してください。"
  exit 1
fi

PROFILE_PATH="${MISE_CONFIG_ROOT}/${PROFILES_DIR}/$PROFILE"
runtime_config="${HOME}/.codex/config.toml"
local_config="${PROFILE_PATH}/config.local.toml"

if [ ! -d "$PROFILE_PATH" ]; then
  printf "%s\n" "🚨 Profile directory does not exist: $PROFILE_PATH" >&2
  exit 1
fi

if [ ! -f "$runtime_config" ]; then
  printf "%s\n" "🚨 Runtime config does not exist: $runtime_config" >&2
  exit 1
fi

mkdir -p "$PROFILE_PATH"

if [ -f "$local_config" ] && ! cmp -s "$runtime_config" "$local_config"; then
  backup="${local_config}.backup.$(date +%Y%m%d_%H%M%S)"
  printf "%s\n" "   Existing local config backup: $local_config -> $backup"
  cp -p "$local_config" "$backup"
fi

cp -p "$runtime_config" "$local_config"
chmod 600 "$local_config"

printf "%s\n" "✅ Imported $runtime_config into $local_config"
printf "%s\n" "   This file is git-ignored. Move shareable settings to config.base.toml when needed."
