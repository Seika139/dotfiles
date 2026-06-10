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

set -uo pipefail

trap 'exit 0' ERR

if [[ -n "${1:-}" ]]; then
  export NOTIFY_TOOL_NAME="$1"
fi

if ! command -v jq >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
  exit 0
fi

load_slack_webhook_url() {
  if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
    return 0
  fi

  local secrets_file
  for secrets_file in \
    "${SECRETS_FILE:-}" \
    "${HOME}/dotfiles/bash/envs/00_secrets.bash"
  do
    if [[ -n "$secrets_file" && -f "$secrets_file" ]]; then
      # shellcheck disable=SC1090
      source "$secrets_file" >/dev/null 2>&1 || true
      if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        export SLACK_WEBHOOK_URL
        return 0
      fi
    fi
  done

  local settings_file
  for settings_file in \
    "${HOME}/.claude/settings.json" \
    "${HOME}/dotfiles/claude/profiles/${DEFAULT_CLAUDE_PROFILE:-win-15034}/settings.local.json"
  do
    if [[ -f "$settings_file" ]]; then
      SLACK_WEBHOOK_URL="$(jq -r '.env.SLACK_WEBHOOK_URL // empty' "$settings_file" 2>/dev/null || true)"
      if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        export SLACK_WEBHOOK_URL
        return 0
      fi
    fi
  done

  return 1
}

if ! load_slack_webhook_url; then
  exit 0
fi

input=$(cat)

event=$(echo "$input" | jq -r '.hook_event_name // empty' 2>/dev/null || true)
cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null || true)
user_host="${USER:-${USERNAME:-unknown}}@$(hostname)"
tool_name="${NOTIFY_TOOL_NAME:-claude}"

case "$event" in
  Stop)
    message="実行中の ${tool_name} が停止しました."$'\n'"${user_host} ${cwd}"
    ;;
  Notification)
    message="実行中の ${tool_name} が許可を要求しています."$'\n'"${user_host} ${cwd}"
    ;;
  *)
    exit 0
    ;;
esac

payload=$(jq -n --arg msg "$message" '{message: $msg}' 2>/dev/null || true)

if [[ -z "$payload" ]]; then
  exit 0
fi

if [[ "$(uname -o 2>/dev/null)" == "Msys" ]]; then
  echo "$payload" | curl -s -o /dev/null -X POST \
    -H "Content-type: application/json; charset=utf-8" \
    -d @- \
    "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
else
  curl -s -o /dev/null -X POST \
    -H "Content-type: application/json; charset=utf-8" \
    -d "$payload" \
    "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
fi

exit 0
