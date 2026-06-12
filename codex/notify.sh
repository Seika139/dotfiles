#!/usr/bin/env bash
# Shared Codex notification wrapper for macOS, Linux, and WSL profiles.

set -euo pipefail

# Codex can invoke notify commands with a minimal PATH.
PATH="$HOME/.local/bin:$HOME/.local/share/mise/bin:$HOME/.local/share/mise/shims:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export PATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="${1:-}"
MESSAGE="Codex finished"
EVENT="Stop"
DEBUG_LOG="${CODEX_NOTIFY_DEBUG_LOG:-}"
JQ_CMD=()

log_debug() {
  [[ -n "$DEBUG_LOG" ]] || return 0
  {
    printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*"
  } >>"$DEBUG_LOG" 2>/dev/null || true
}

load_secrets() {
  [[ "${CODEX_NOTIFY_LOAD_SECRETS:-1}" != "0" ]] || return 0

  local bdotdir="${BDOTDIR:-$HOME/dotfiles/bash}"
  local secrets_file="${SECRETS_FILE:-$bdotdir/envs/00_secrets.bash}"
  [[ -f "$secrets_file" ]] || return 0

  # shellcheck disable=SC1090
  source "$secrets_file"
}

resolve_jq() {
  if ((${#JQ_CMD[@]} > 0)); then
    return 0
  fi

  if command -v mise >/dev/null 2>&1 &&
    mise -C "$SCRIPT_DIR" exec -q -- jq --version >/dev/null 2>&1; then
    JQ_CMD=(mise -C "$SCRIPT_DIR" exec -q -- jq)
    return 0
  fi

  if command -v jq >/dev/null 2>&1; then
    JQ_CMD=(jq)
    return 0
  fi

  return 1
}

run_jq() {
  resolve_jq || return 1
  "${JQ_CMD[@]}" "$@"
}

parse_message() {
  if [[ -z "$PAYLOAD" || "$PAYLOAD" == "{message}" ]]; then
    return 0
  fi

  if [[ "$PAYLOAD" == *'"approval-requested"'* ]]; then
    EVENT="Notification"
  fi

  local parsed=""
  # shellcheck disable=SC2016
  parsed="$(
    printf '%s' "$PAYLOAD" |
      run_jq -r '
        def nonempty_string:
          if type == "string" then gsub("^\\s+|\\s+$"; "") else "" end;

        try (
          (.["last-assistant-message"] | nonempty_string) as $last
          | if $last != "" then
              $last
            elif (.["input-messages"] | type) == "array" and (.["input-messages"] | length) > 0 then
              (.["input-messages"][-1] | if type == "string" then . else tojson end)
            elif (.type | nonempty_string) != "" then
              "Codex event: \(.type)"
            else
              tojson
            end
        ) catch empty
      ' 2>/dev/null || true
  )"

  if [[ -n "$parsed" ]]; then
    MESSAGE="$parsed"
  else
    MESSAGE="$PAYLOAD"
  fi
}

normalize_message() {
  MESSAGE="$(printf '%s' "$MESSAGE" | tr '\r\n' '  ' | tr -s '[:space:]' ' ')"
  MESSAGE="${MESSAGE:0:240}"
}

notify_with_terminal_notifier() {
  [[ "$(uname -s 2>/dev/null)" == "Darwin" ]] || return 1
  command -v terminal-notifier >/dev/null 2>&1 || return 1

  local title="${CODEX_NOTIFY_TITLE:-Codex}"
  local sound="${CODEX_NOTIFY_SOUND:-Glass}"
  local args=(-title "$title" -message "$MESSAGE")
  if [[ -n "$sound" ]]; then
    args+=(-sound "$sound")
  fi

  terminal-notifier "${args[@]}" >/dev/null 2>&1
}

notify_with_notify_send() {
  [[ "$(uname -s 2>/dev/null)" == "Linux" ]] || return 1
  command -v notify-send >/dev/null 2>&1 || return 1
  notify-send "${CODEX_NOTIFY_TITLE:-Codex}" "$MESSAGE" >/dev/null 2>&1
}

play_ringtone() {
  # 既定では MP3 を鳴らさない。CODEX_NOTIFY_RINGTONE=1 (true/on) で明示的に有効化する。
  case "${CODEX_NOTIFY_RINGTONE:-0}" in
  1 | true | on | yes) ;;
  *) return 0 ;;
  esac

  [[ "$(uname -s 2>/dev/null)" == "Darwin" ]] || return 1
  command -v afplay >/dev/null 2>&1 || return 1

  local ringtone_dir="${CODEX_NOTIFY_RINGTONES_DIR:-$HOME/dotfiles/codex/ringtones}"
  [[ -d "$ringtone_dir" ]] || return 1

  local -a candidates=()
  while IFS= read -r file; do
    [[ -n "$file" ]] && candidates+=("$file")
  done < <(find "$ringtone_dir" -maxdepth 1 -type f \( -iname '*.mp3' -o -iname '*.wav' \) -print 2>/dev/null)

  if ((${#candidates[@]} == 0)); then
    return 1
  fi

  local pick="${candidates[RANDOM % ${#candidates[@]}]}"
  # afplay -v は 1.0 が等倍。0.0〜1.0 で音量を絞れる。
  local volume="${CODEX_NOTIFY_RINGTONE_VOLUME:-0.1}"
  nohup afplay -v "$volume" "$pick" >/dev/null 2>&1 &
}

notify_local() {
  [[ "${CODEX_NOTIFY_LOCAL:-1}" != "0" ]] || return 0

  if ! notify_with_terminal_notifier && ! notify_with_notify_send; then
    log_debug "local notification unavailable"
  fi

  if ! play_ringtone; then
    log_debug "ringtone playback unavailable"
  fi
}

resolve_channel() {
  local channel="${CODEX_NOTIFY_CHANNEL:-auto}"
  case "$channel" in
  auto)
    if [[ -n "${AGENT_NOTIFY_DISCORD_WEBHOOK_URL:-${DISCORD_WEBHOOK_URL:-}}" && -z "${SLACK_WEBHOOK_URL:-}" ]]; then
      printf '%s\n' "discord"
    elif [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
      printf '%s\n' "slack"
    else
      printf '%s\n' "none"
    fi
    ;;
  *)
    printf '%s\n' "$channel"
    ;;
  esac
}

notify_with_webhook() {
  local channel="$1"
  local script=""

  case "$channel" in
  "" | none | off | false)
    return 0
    ;;
  slack)
    script="${CODEX_NOTIFY_SLACK_SCRIPT:-$HOME/dotfiles/claude/notify_slack.sh}"
    ;;
  discord)
    script="${CODEX_NOTIFY_DISCORD_SCRIPT:-$HOME/dotfiles/claude/notify_discord.sh}"
    ;;
  *)
    log_debug "unknown CODEX_NOTIFY_CHANNEL=$channel"
    return 0
    ;;
  esac

  [[ -x "$script" ]] || return 1

  local cwd="${PWD:-}"
  local title="${CODEX_NOTIFY_TITLE:-Codex}"
  if [[ "$EVENT" == "Notification" ]]; then
    title="${CODEX_NOTIFY_NOTIFICATION_TITLE:-${title} 通知}"
  fi

  # shellcheck disable=SC2016
  run_jq -n \
    --arg event "$EVENT" \
    --arg cwd "$cwd" \
    --arg title "$title" \
    --arg message "$MESSAGE" \
    '{hook_event_name: $event, cwd: $cwd, title: $title, message: $message}' |
    NOTIFY_TOOL_NAME="${CODEX_NOTIFY_TOOL_NAME:-Codex}" "$script"
}

main() {
  log_debug "notify.sh invoked with payload length=${#PAYLOAD}"

  parse_message
  normalize_message
  load_secrets
  notify_local

  local channel
  channel="$(resolve_channel)"
  if ! notify_with_webhook "$channel"; then
    log_debug "$channel notification unavailable or failed"
  fi

  log_debug "notify.sh completed event=$EVENT channel=$channel"
}

main "$@"
