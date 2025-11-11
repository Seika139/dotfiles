#!/usr/bin/env bash

# Homebrew の bash-completion@2 を読み込む

completion_v2_path="/opt/homebrew/etc/profile.d/bash_completion.sh"
if [[ -f "$completion_v2_path" ]]; then
    source "$completion_v2_path"
    # [DEBUG] bash-completion 読み込み直後に関数が存在するか確認
    if type _comp_initialize &>/dev/null; then
        echo "✅ _comp_initialize is found immediately after sourcing."
    else
        echo "❌ _comp_initialize is NOT found immediately after sourcing."
    fi
else
    warn "Homebrew の bash-completion@2 が見つかりません: $completion_v2_path"
fi
