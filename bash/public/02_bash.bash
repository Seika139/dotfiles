#!/usr/bin/env bash

# Homebrew の bash-completion@2 を読み込む

completion_v2_path="/opt/homebrew/etc/profile.d/bash_completion.sh"
if command -v brew >/dev/null 2>&1; then
  if [[ -f "$completion_v2_path" ]]; then
    # shellcheck disable=SC1090
    source "$completion_v2_path"
  else
    [[ "${BDOTDIR_SHELL_IS_INTERACTIVE}" == "1" ]] && warn "Homebrew の bash-completion@2 が見つかりません: $completion_v2_path"
  fi
fi
