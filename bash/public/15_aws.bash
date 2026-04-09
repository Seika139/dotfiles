#!/usr/bin/env bash

# AWS プロファイルを fzf で選択して AWS_PROFILE 環境変数にセットする
# 静的認証情報（AWS_ACCESS_KEY_ID 等）が存在すると AWS_PROFILE より優先されるため、
# プロファイル選択時に unset する
awsp() {
  local profile
  profile=$(aws configure list-profiles | fzf --prompt="AWS Profile> " --height=40% --reverse)
  if [[ -n "$profile" ]]; then
    unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_SECURITY_TOKEN
    export AWS_PROFILE="$profile"
    echo "AWS_PROFILE=$profile (静的認証情報を unset しました)"
  fi
}

# AWS_PROFILE をリセットする
awsp-clear() {
  unset AWS_PROFILE
  echo "AWS_PROFILE をリセットしました"
}
