#!/usr/bin/env bash
# Claude Code hook -> Discord webhook 通知スクリプト
# stdin から hook の JSON を受け取り、Discord に通知を送る
#
# 環境変数:
#   DISCORD_WEBHOOK_URL - Discord Webhook URL (必須)
#
# 使い方:
#   hook_event_name に応じてメッセージを生成する
#   - Stop: タスク完了通知
#   - Notification: 権限待ち等の通知

set -euo pipefail

if [[ -z "${DISCORD_WEBHOOK_URL:-}" ]]; then
  exit 0
fi

input=$(cat)

event=$(echo "$input" | jq -r '.hook_event_name // empty')
cwd=$(echo "$input" | jq -r '.cwd // empty')
user_host="${USER}@$(hostname -s)"

case "$event" in
  Stop)
    title="Claude Code タスク完了"
    description="実行中の Claude が停止しました。"
    color=3066993 # 緑
    ;;
  Notification)
    title=$(echo "$input" | jq -r '.title // "Claude Code 通知"')
    description=$(echo "$input" | jq -r '.message // ""')
    color=15105570 # オレンジ
    ;;
  *)
    exit 0
    ;;
esac

payload=$(jq -n \
  --arg title "$title" \
  --arg desc "$description" \
  --arg user_host "$user_host" \
  --arg cwd "$cwd" \
  --argjson color "$color" \
  '{
    embeds: [{
      title: $title,
      description: $desc,
      color: $color,
      fields: [
        { name: "User", value: $user_host, inline: true },
        { name: "Directory", value: $cwd, inline: true }
      ]
    }]
  }')

curl -s -o /dev/null -X POST \
  -H "Content-Type: application/json" \
  -d "$payload" \
  "$DISCORD_WEBHOOK_URL"
