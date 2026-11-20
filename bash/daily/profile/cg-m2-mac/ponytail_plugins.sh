#!/usr/bin/env bash

DAILY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${DAILY_DIR}/.cache"
LOG_FILE="${LOG_DIR}/ponytail_plugins.log"

if ! mkdir -p "$LOG_DIR"; then
  printf 'Ponytail/plugin update: ログディレクトリを作成できません: %s\n' "$LOG_DIR" >&2
  exit 1
fi
if ! : >"$LOG_FILE"; then
  printf 'Ponytail/plugin update: ログファイルを作成できません: %s\n' "$LOG_FILE" >&2
  exit 1
fi

nohup bash "${DAILY_DIR}/common/update_agent_plugins.sh" >>"$LOG_FILE" 2>&1 </dev/null &
printf 'Claude/Codex plugin の更新をバックグラウンドで開始しました。ログ: %s\n' "$LOG_FILE"
