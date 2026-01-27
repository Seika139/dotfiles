#!/usr/bin/env bash
# macOS 用 Codex 通知スクリプト。Codex CLI から渡される JSON ペイロードを整形し、
# 通知センターへ表示するとともに任意の効果音を再生する。
set -euo pipefail

# Codex 側の環境で PATH が最小構成になるケースがあるため、通知に必要なパスを明示的に追加。
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export PATH

PAYLOAD="${1:-}"
MESSAGE="Codex finished"
DEBUG_LOG="${CODEX_NOTIFY_DEBUG_LOG:-}"

log_debug() {
  [[ -n "$DEBUG_LOG" ]] || return 0
  {
    printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*"
  } >>"$DEBUG_LOG" 2>/dev/null || true
}

log_debug "notify.sh invoked with payload length=${#PAYLOAD}"

if [[ -n "$PAYLOAD" && "$PAYLOAD" != "{message}" ]]; then
  PARSED="$(
    CODEX_NOTIFY_INPUT="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json
import os

payload = os.environ.get("CODEX_NOTIFY_INPUT", "")
if not payload:
    raise SystemExit

try:
    data = json.loads(payload)
except Exception:
    print(payload)
    raise SystemExit

def as_text(value):
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return ""

text = as_text(data.get("last-assistant-message"))

if not text:
    messages = data.get("input-messages")
    if isinstance(messages, list) and messages:
        candidate = messages[-1]
        if isinstance(candidate, str):
            text = candidate.strip()
        else:
            try:
                text = json.dumps(candidate, ensure_ascii=False)
            except Exception:
                text = str(candidate)

if not text:
    value = data.get("type")
    if isinstance(value, str) and value.strip():
        text = f"Codex event: {value}"

if not text:
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

print(text)
PY
  )"

  if [[ -n "${PARSED:-}" ]]; then
    MESSAGE="$PARSED"
  else
    MESSAGE="$PAYLOAD"
  fi
elif [[ -n "$PAYLOAD" && "$PAYLOAD" != "{message}" ]]; then
  MESSAGE="$PAYLOAD"
fi

log_debug "resolved message='${MESSAGE}'"

# 改行や余分な空白を除去し、マルチバイトを壊さないよう Python で長さ制限する。
MESSAGE="$(printf '%s' "$MESSAGE" | tr '\r\n' '  ' | tr -s '[:space:]' ' ')"
MESSAGE="$(
  CODEX_NOTIFY_MESSAGE="$MESSAGE" python3 <<'PY' | tr -d '\n'
import os
text = os.environ.get("CODEX_NOTIFY_MESSAGE", "")
print(text[:240], end="")
PY
)"

TITLE="${CODEX_NOTIFY_TITLE:-🌎 Codex}"
SOUND="${CODEX_NOTIFY_SOUND:-Glass}"
RINGTONE_DIR="${CODEX_NOTIFY_RINGTONES_DIR:-$HOME/dotfiles/codex/ringtones}"

notify_with_terminal_notifier() {
  command -v terminal-notifier >/dev/null 2>&1 || return 1

  local args=(-title "$TITLE" -message "$MESSAGE")
  if [[ -n "$SOUND" ]]; then
    args+=(-sound "$SOUND")
  fi

  # `if ! cmd; then ... fi` だと `$?` が 0 になってしまうため、正方向で判定して
  # 失敗時のみ exit code を記録する。失敗時の usage ノイズを抑えるために標準出力・
  # 標準エラーは捨て、ログにだけ詳細を残す。
  if terminal-notifier "${args[@]}" >/dev/null 2>&1; then
    log_debug "terminal-notifier succeeded with exit=0"
    return 0
  else
    local exit_code=$?
    log_debug "terminal-notifier failed with exit=${exit_code}"
    return 1
  fi
}

play_ringtone() {
  command -v afplay >/dev/null 2>&1 || return 1
  [[ -d "$RINGTONE_DIR" ]] || return 1

  local -a candidates=()
  while IFS= read -r file; do
    [[ -n "$file" ]] && candidates+=("$file")
  done < <(find "$RINGTONE_DIR" -maxdepth 1 -type f \( -iname '*.mp3' -o -iname '*.wav' \) -print 2>/dev/null)

  if ((${#candidates[@]} == 0)); then
    return 1
  fi

  local pick="${candidates[RANDOM % ${#candidates[@]}]}"
  nohup afplay "$pick" >/dev/null 2>&1 &
}

if ! notify_with_terminal_notifier; then
  log_debug "terminal-notifier unavailable or failed"
fi

if ! play_ringtone; then
  log_debug "ringtone playback unavailable"
fi

log_debug "notify.sh completed"
