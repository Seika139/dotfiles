#!/usr/bin/env bash

# Homebrew の bash-completion@2 を読み込む

completion_v2_path="/opt/homebrew/etc/profile.d/bash_completion.sh"
if [[ -f "$completion_v2_path" ]]; then
    source "$completion_v2_path"
else
    warn "Homebrew の bash-completion@2 が見つかりません: $completion_v2_path"
fi
