#!/bin/bash

#MISE description="sqlite3 (agmsg の必須依存) が利用可能であることを確認する"
#MISE quiet=true
#MISE hide=true

# agmsg は bash + sqlite3 のみで動く message bus。install / 実行の両方で sqlite3 が要る。
# apm-available.sh / uv-available.sh と同じ作法の hidden ガード。

if ! command -v sqlite3 &>/dev/null; then
  printf "%b%s%b%s\n" "\033[1;31m" "✘ Error" "\033[0m" ": sqlite3 is not installed or not in PATH." >&2
  printf "%s\n" "  macOS: 標準で同梱" >&2
  printf "%s\n" "  Linux: sudo apt install sqlite3  (または同等のパッケージ)" >&2
  exit 1
fi
