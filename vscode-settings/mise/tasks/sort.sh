#!/usr/bin/env bash

#MISE description="settings.json の各層 (shared / profile / local) のトップレベルキーを昇順に並べ替える"
#MISE depends=["ensure_local_env"]
#USAGE flag "--prof <prof>" {
#USAGE   help "プロファイル名"
#USAGE }
#USAGE flag "--all" {
#USAGE   help "全プロファイルを対象にする"
#USAGE }
#USAGE flag "--dry-run" {
#USAGE   help "並べ替えが必要なファイルを表示するだけで書き込まない"
#USAGE }

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

resolve_python
profiles=()
if [ "${usage_all:-}" = "true" ]; then
  for dir in profiles/*/; do
    profiles+=("$(basename "$dir")")
  done
else
  resolve_profile
  # shellcheck disable=SC2153
  profiles+=("$PROFILE")
fi

files=()
if [ -f shared/settings.json ]; then
  files+=(shared/settings.json)
fi
for profile in "${profiles[@]}"; do
  for name in settings.json settings.local.json; do
    f="profiles/$profile/$name"
    if [ -f "$f" ]; then
      files+=("$f")
    fi
  done
done

if [ "${#files[@]}" = "0" ]; then
  echo "対象ファイルがありません"
  exit 0
fi

sort_args=()
if [ "${usage_dry_run:-}" = "true" ]; then
  sort_args+=(--dry-run)
fi
result="$("$PY" "$SETTINGS_PY" sort ${sort_args[@]+"${sort_args[@]}"} "${files[@]}")"
if [ -n "$result" ]; then
  echo "$result"
else
  echo "並べ替えは不要です"
fi

if [ "${usage_dry_run:-}" != "true" ]; then
  rc=0
  for profile in "${profiles[@]}"; do
    "$PY" "$SETTINGS_PY" check --profile "$profile" || rc=1
  done
  exit "$rc"
fi
