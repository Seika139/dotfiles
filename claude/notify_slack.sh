#!/usr/bin/env bash
# Claude Code hook -> Slack Workflow Trigger 通知スクリプト
# stdin から hook の JSON を受け取り、Slack に通知を送る
#
# 環境変数:
#   SLACK_WEBHOOK_URL - Slack Workflow Trigger URL (必須)
#
# 使い方:
#   hook_event_name に応じてメッセージを生成する
#   - Stop: タスク完了通知
#   - Notification: 権限待ち等の通知

set -euo pipefail

if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
  exit 0
fi

input=$(cat)

event=$(echo "$input" | jq -r '.hook_event_name // empty')
cwd=$(echo "$input" | jq -r '.cwd // empty')
user_host="${USER}@$(hostname)"

case "$event" in
  Stop)
    message="実行中の claude が停止しました."$'\n'"${user_host} ${cwd}"
    ;;
  Notification)
    message="実行中の claude が許可を要求しています."$'\n'"${user_host} ${cwd}"
    ;;
  *)
    exit 0
    ;;
esac

payload=$(printf '{"message": "%s"}' "$message" | iconv -t utf-8)

curl -s -o /dev/null -X POST \
  -H "Content-type: application/json; charset=utf-8" \
  -d "$payload" \
  "$SLACK_WEBHOOK_URL"
