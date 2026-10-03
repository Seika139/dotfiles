#!/usr/bin/env bash

emphasize_line() {
  printf "%b%s%b\n" "\\033[38;5;214m" "=== $1 ===" "\\033[0m"
}

# --with-apt オプションで apt update/upgrade も実行する
WITH_APT=false
for arg in "$@"; do
  case "$arg" in
  --with-apt) WITH_APT=true ;;
  esac
done

if "$WITH_APT"; then
  emphasize_line "apt update && upgrade (mise 本体含む)"
  sudo apt update && sudo apt upgrade -y
fi

# mise 管理のツール
MISE_UPGRADE_STATUS=0
emphasize_line "mise"
MISE_UPGRADE_TIMEOUT="${MISE_UPGRADE_TIMEOUT:-300}"
(cd "$HOME" && timeout "$MISE_UPGRADE_TIMEOUT" mise upgrade) || {
  rc=$?
  MISE_UPGRADE_STATUS=$rc
  if [ "$rc" -eq 124 ]; then
    printf "%s\n" "mise upgrade: ${MISE_UPGRADE_TIMEOUT}秒でタイムアウトしました。"
  else
    printf "%s\n" "mise upgrade: 失敗しました (exit ${rc})。"
  fi
}

# uv 本体（pipx 経由でインストール）
emphasize_line "uv"
PIPX_UPGRADE_TIMEOUT="${PIPX_UPGRADE_TIMEOUT:-180}"
timeout "$PIPX_UPGRADE_TIMEOUT" pipx upgrade uv || {
  rc=$?
  if [ "$rc" -eq 124 ]; then
    printf "%s\n" "pipx upgrade uv: ${PIPX_UPGRADE_TIMEOUT}秒でタイムアウトしました。"
  else
    printf "%s\n" "pipx upgrade uv: 失敗しました (exit ${rc})。"
  fi
}

if command -v apm >/dev/null 2>&1; then
  emphasize_line "apm"
  APM_UPGRADE_TIMEOUT="${APM_UPGRADE_TIMEOUT:-180}"
  timeout "$APM_UPGRADE_TIMEOUT" apm self-update || {
    rc=$?
    if [ "$rc" -eq 124 ]; then
      printf "%s\n" "apm self-update: ${APM_UPGRADE_TIMEOUT}秒でタイムアウトしました。"
    else
      printf "%s\n" "apm self-update: 失敗しました (exit ${rc})。"
    fi
  }
fi

if ! "$WITH_APT"; then
  emphasize_line "apt"
  printf "%b%s%b%s\n" "\\033[33m" "⚠  apt のアップデートはスキップしました（mise 本体含む）。" "\\033[0m" "実行する場合:"
  printf "%b%s%b\n" "\\033[36m" "  sudo apt update && sudo apt upgrade -y" "\\033[0m"
fi

exit "$MISE_UPGRADE_STATUS"
