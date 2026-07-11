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
