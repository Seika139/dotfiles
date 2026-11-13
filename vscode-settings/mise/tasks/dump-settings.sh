#!/usr/bin/env bash

#MISE description="各種設定ファイルをエクスポートする"
#MISE depends=["ensure_local_env"]
#MISE hide=true
#USAGE arg "[editor]" {
#USAGE   help "対象エディタ"
#USAGE   choices "vscode" "cursor" "antigravity"
#USAGE   default "vscode"
#USAGE }
#USAGE flag "--prof <prof>" {
#USAGE   help "プロファイル名"
#USAGE }

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

resolve_profile
load_config_files
editor="${usage_editor:-vscode}"
if ! src_path="$(editor_path_for "$editor")"; then
  printf "  ❌ 不明なエディタ: %s\n" "$editor"
  exit 1
fi

printf "🛠️  エディタ設定を \033[36m%s\033[0m から \033[36m%s\033[0m にエクスポートします\n" "$src_path" "$PROFILE_DIR"
mkdir -p "$PROFILE_DIR"
for item in "${CONFIG_FILE_LIST[@]}"; do
  if [ "$item" = "settings.json" ]; then
    # 合成結果でプロファイルを上書きしないよう settings.json はコピーしない
    printf "  ⚠️  スキップ: settings.json は \033[36mmise run settings-diff\033[0m で差分を確認し、\033[36mmise run pull\033[0m で該当層へ書き戻してください\n"
    continue
  fi
  if [ -f "$src_path/$item" ] || [ -d "$src_path/$item" ]; then
    cp -r "$src_path/$item" "$PROFILE_DIR"
    printf "  ✅ エクスポート完了: \033[36m%s -> %s/%s\033[0m\n" "$src_path/$item" "$PROFILE_DIR" "$item"
  else
    printf "  ⚠️  スキップ: \033[36m%s\033[0m が見つかりません\n" "$src_path/$item"
  fi
done
