#!/usr/bin/env bash

# 色付けヘルパー関数
# 基本色（ANSI 16色）
print_red() { printf '\e[31m%s\e[0m' "$*"; }
print_green() { printf '\e[32m%s\e[0m' "$*"; }
print_yellow() { printf '\e[33m%s\e[0m' "$*"; }
print_blue() { printf '\e[34m%s\e[0m' "$*"; }
print_magenta() { printf '\e[35m%s\e[0m' "$*"; }
print_cyan() { printf '\e[36m%s\e[0m' "$*"; }
# スタイル
print_dim() { printf '\e[2m%s\e[0m' "$*"; }
print_bold() { printf '\e[1m%s\e[0m' "$*"; }
# RGB カスタムカラー（引数: R G B テキスト）
print_rgb() {
  local r=$1 g=$2 b=$3
  shift 3
  printf '\e[38;2;%d;%d;%dm%s\e[0m' "$r" "$g" "$b" "$*"
}
# よく使うカスタムカラー
print_orange() { print_rgb 250 180 100 "$*"; }
print_soft_green() { print_rgb 150 255 200 "$*"; }
print_soft_blue() { print_rgb 160 190 255 "$*"; }
print_pink() { print_rgb 255 150 200 "$*"; }

codex_is_wsl() {
  [ "${IS_WSL:-false}" = "true" ]
}

codex_default_profile() {
  if codex_is_wsl; then
    printf "%s" "${WSL_CODEX_PROFILE:-}"
  else
    printf "%s" "${DEFAULT_CODEX_PROFILE:-}"
  fi
}

codex_profile_or_default() {
  local explicit_profile="${1:-}"
  if [ -n "$explicit_profile" ]; then
    printf "%s" "$explicit_profile"
  else
    codex_default_profile
  fi
}

codex_profiles_path() {
  local root_dir="$1"
  printf "%s/%s" "$root_dir" "${PROFILES_DIR:-profiles}"
}

codex_profile_path() {
  local root_dir="$1"
  local profile="$2"
  printf "%s/%s" "$(codex_profiles_path "$root_dir")" "$profile"
}

codex_os_name() {
  uname -s | tr '[:upper:]' '[:lower:]'
}

codex_python() {
  local candidate
  for candidate in python3 python; do
    if ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done
  printf "%s\n" "Python 3.11+ が必要です。python3 または python を PATH に追加してください。" >&2
  return 1
}
