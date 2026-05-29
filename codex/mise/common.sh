#!/usr/bin/env bash

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
