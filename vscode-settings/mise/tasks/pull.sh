#!/usr/bin/env bash

#MISE description="エディタで変更した settings.json を 3 層 (shared / profile / local) へ書き戻す"
#MISE depends=["ensure_local_env"]
#USAGE flag "--prof <prof>" {
#USAGE   help "プロファイル名"
#USAGE }
#USAGE flag "--editor <editor>" {
#USAGE   help "取り込み元のエディタ"
#USAGE   default "vscode"
#USAGE   choices "vscode" "cursor" "agy"
#USAGE }
#USAGE flag "--dry-run" {
#USAGE   help "書き込まず、更新・追加・削除の一覧だけ表示する"
#USAGE }
#USAGE flag "--prune" {
#USAGE   help "エディタで削除されたキーを該当する層からも削除する"
#USAGE }
#USAGE flag "--local" {
#USAGE   help "新規キーを settings.local.json に入れる"
#USAGE }

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

resolve_profile
editor="${usage_editor:-vscode}"
if ! editor_path="$(editor_path_for "$editor")"; then
  printf "❌ 不明なエディタ: %s\n" "$editor"
  exit 1
fi
# 空・相対・// を含むパスは意図しない場所を読むため中断する
rc=0
check_editor_path "$editor_path" || rc=$?
if [ "$rc" = "2" ]; then
  printf "❌ エディタのパスが不正です (// を含む): '%s'\n" "$editor_path"
  exit 1
elif [ "$rc" != "0" ]; then
  printf "❌ エディタのパスが空または相対パスです: '%s'\n" "$editor_path"
  exit 1
fi

resolve_python
args=(pull --profile "$PROFILE" --target "$editor_path/settings.json")
if [ "${usage_dry_run:-}" = "true" ]; then
  args+=(--dry-run)
fi
if [ "${usage_prune:-}" = "true" ]; then
  args+=(--prune)
fi
if [ "${usage_local:-}" = "true" ]; then
  args+=(--local)
fi
"$PY" "$SETTINGS_PY" "${args[@]}"
