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

log_file="${CODEX_SLACK_HOOK_LOG:-${TMPDIR:-${TEMP:-/tmp}}/codex-slack-hook.log}"
log() {
  printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" >>"$log_file" 2>/dev/null || true
}

if [[ -n "${1:-}" ]]; then
  export NOTIFY_TOOL_NAME="$1"
fi

if ! command -v jq >/dev/null 2>&1; then
  log 'jq is not available'
  exit 0
fi
if ! command -v curl >/dev/null 2>&1; then
  log 'curl is not available'
  exit 0
fi

profile_dir=''
if [[ -n "${USERPROFILE:-}" && -d "${USERPROFILE}" ]]; then
  profile_dir="${USERPROFILE}"
elif [[ -n "${USERPROFILE:-}" ]] && command -v cygpath >/dev/null 2>&1; then
  profile_dir="$(cygpath -u "$USERPROFILE" 2>/dev/null || true)"
elif [[ -n "${HOME:-}" ]]; then
  profile_dir="$HOME"
fi

load_slack_webhook_url() {
  if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
    return 0
  fi

  local secrets_file
  for secrets_file in \
    "${SECRETS_FILE:-}" \
    "${profile_dir}/dotfiles/bash/envs/00_secrets.bash" \
    "${HOME:-}/dotfiles/bash/envs/00_secrets.bash"
  do
    if [[ -n "$secrets_file" && -f "$secrets_file" ]]; then
      # shellcheck disable=SC1090
      source "$secrets_file" >/dev/null 2>&1 || log 'failed to load secrets file'
      if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        export SLACK_WEBHOOK_URL
        return 0
      fi
    fi
  done

  local settings_file
  for settings_file in \
    "${profile_dir}/.claude/settings.json" \
    "${profile_dir}/dotfiles/claude/profiles/${DEFAULT_CLAUDE_PROFILE:-win-15034}/settings.local.json" \
    "${HOME:-}/.claude/settings.json" \
    "${HOME:-}/dotfiles/claude/profiles/${DEFAULT_CLAUDE_PROFILE:-win-15034}/settings.local.json"
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
  log 'SLACK_WEBHOOK_URL was not found'
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

curl_config() {
  printf '%s\n' \
    "url = \"${SLACK_WEBHOOK_URL}\"" \
    'request = "POST"' \
    'header = "Content-type: application/json; charset=utf-8"' \
    'connect-timeout = "10"' \
    'max-time = "30"'
}

# Keep both the webhook URL and payload out of curl's argv. Git for Windows
# curl cannot reliably consume a /dev/fd process substitution, so use a
# randomly named, short-lived config file for the URL and pass JSON on stdin.
curl_config_file="$(mktemp "${TMPDIR:-${TEMP:-/tmp}}/codex-slack-hook-config.XXXXXX" 2>/dev/null)" || {
  log 'could not create temporary curl config'
  exit 0
}
trap 'rm -f "$curl_config_file"' EXIT
curl_config >"$curl_config_file"

# Keep the response out of stdout. Some machines have a global curl config
# containing `output = "/dev/null"`; explicitly selecting a writable response
# file avoids curl exiting with code 23 while still allowing us to inspect the
# body when diagnosing an HTTP error.
response_file="$(mktemp "${TMPDIR:-${TEMP:-/tmp}}/codex-slack-hook-response.XXXXXX" 2>/dev/null)" || {
  log 'could not create temporary curl response file'
  exit 0
}
trap 'rm -f "$curl_config_file" "$response_file"' EXIT

http_status="$(printf '%s' "$payload" | curl --disable --silent --show-error \
  --config "$curl_config_file" --data-binary @- \
  --output "$response_file" --write-out '%{http_code}' 2>/dev/null)"

curl_status=$?
if [[ "$curl_status" -ne 0 || ! "$http_status" =~ ^2[0-9][0-9]$ ]]; then
  log "Slack request failed: curl_exit=${curl_status} http_status=${http_status:-unknown}"
  exit 0
fi

log "Slack request succeeded: event=${event:-unknown} curl_exit=0 http_status=${http_status}"
exit 0
