#!/bin/bash

#MISE description="現在有効な VSCode 設定ファイルのパスを特定する関数を提供します。"
#MISE shell="bash -c"
#MISE quiet=true

# 現在有効な VSCode 設定ファイルのパスを特定する関数
get_vscode_settings_path() {
  # Git Bash では $USER が空で $USERNAME だけのことがある
  local user="${USER:-${USERNAME:-}}"
  [ -n "$user" ] || { echo "ユーザー名を特定できません (USER/USERNAME が空)" >&2; return 1; }
  local scoop_path="/c/Users/$user/scoop/persist/vscode/data/user-data/User/settings.json"
  local normal_path="/c/Users/$user/AppData/Roaming/Code/User/settings.json"

  # 1. 実行中のプロセスから判定
  local running_path
  running_path=$(wmic process where "name='Code.exe'" get commandline 2>/dev/null | grep -oP '(?<=--user-data-dir=)[^ ]+' | head -n 1)

  if [ -n "$running_path" ]; then
    # Windows形式のパスをUnix形式に変換して表示
    echo "$(cygpath -u "$running_path")/User/settings.json"
    return
  fi

  # 2. プロセスが動いていない場合は code コマンドの場所で判定
  if command -v code >/dev/null 2>&1; then
    if [[ $(which code) == *"scoop"* ]]; then
      echo "$scoop_path"
    else
      echo "$normal_path"
    fi
  else
    echo "VSCode is not installed or not in PATH" >&2
    return 1
  fi
}

settings_path="$(get_vscode_settings_path)" || exit 1
dirname "$settings_path"
