#!/usr/bin/env bash
# WSL Ubuntu 用 Codex 通知スクリプト。Codex CLI から渡される JSON ペイロードを整形し、
# デスクトップ通知を表示するとともに任意の効果音を再生する。
set -euo pipefail

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
RINGTONE_DIR="${CODEX_NOTIFY_RINGTONES_DIR:-$HOME/dotfiles/codex/ringtones}"
VOLUME="${CODEX_NOTIFY_VOLUME:-0.3}"

# notify-send を使用してデスクトップ通知を表示
notify_with_notify_send() {
  command -v notify-send >/dev/null 2>&1 || return 1

  # WSL 環境では DISPLAY または WAYLAND_DISPLAY が必要
  if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    # WSL2 の場合、Windows 側のディスプレイに接続を試みる
    export DISPLAY="${DISPLAY:-:0}"
  fi

  if notify-send "$TITLE" "$MESSAGE" --urgency=normal 2>/dev/null; then
    log_debug "notify-send succeeded"
    return 0
  else
    local exit_code=$?
    log_debug "notify-send failed with exit=${exit_code}"
    return 1
  fi
}

# 音声再生（paplay または aplay を使用）
play_ringtone() {
  [[ -d "$RINGTONE_DIR" ]] || return 1

  local -a candidates=()
  while IFS= read -r file; do
    [[ -n "$file" ]] && candidates+=("$file")
  done < <(find "$RINGTONE_DIR" -maxdepth 1 -type f \( -iname '*.mp3' -o -iname '*.wav' -o -iname '*.ogg' \) -print 2>/dev/null)

  if ((${#candidates[@]} == 0)); then
    return 1
  fi

  local pick="${candidates[RANDOM % ${#candidates[@]}]}"
  log_debug "playing ringtone: $pick"

  # PulseAudio (paplay) を優先、なければ ALSA (aplay) を使用
  # mp3 の場合は mpv または ffplay を使用
  local ext="${pick##*.}"
  ext="${ext,,}"  # 小文字に変換

  if [[ "$ext" == "mp3" ]]; then
    if command -v mpv >/dev/null 2>&1; then
      nohup mpv --no-video --volume="$((${VOLUME%.*} * 100))" "$pick" >/dev/null 2>&1 &
      return 0
    elif command -v ffplay >/dev/null 2>&1; then
      nohup ffplay -nodisp -autoexit -volume "$((${VOLUME%.*} * 100))" "$pick" >/dev/null 2>&1 &
      return 0
    fi
  fi

  if command -v paplay >/dev/null 2>&1; then
    # paplay は wav/ogg のみ対応
    if [[ "$ext" == "wav" || "$ext" == "ogg" ]]; then
      nohup paplay "$pick" >/dev/null 2>&1 &
      return 0
    fi
  fi

  if command -v aplay >/dev/null 2>&1 && [[ "$ext" == "wav" ]]; then
    nohup aplay -q "$pick" >/dev/null 2>&1 &
    return 0
  fi

  log_debug "no suitable player found for $ext files"
  return 1
}

if ! notify_with_notify_send; then
  log_debug "notify-send unavailable or failed"
fi

if ! play_ringtone; then
  log_debug "ringtone playback unavailable"
fi

log_debug "notify.sh completed"
