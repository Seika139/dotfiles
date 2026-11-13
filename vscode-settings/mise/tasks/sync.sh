#!/usr/bin/env bash

#MISE description="VS Code と Cursor の設定を同期し (settings.json は 3 層合成、他はシンボリックリンク)、拡張機能をインストールする"
#MISE depends=["ensure_local_env"]
#USAGE flag "--prof <prof>" {
#USAGE   help "プロファイル名"
#USAGE }
#USAGE flag "--force" {
#USAGE   help "既存の settings.json が合成結果と意味的に異なっていても、バックアップを残して上書きする"
#USAGE }

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

settings_args=()
ext_args=()
if [ "${usage_force:-}" = "true" ]; then
  settings_args+=(--force)
fi
if [ -n "${usage_prof:-}" ]; then
  settings_args+=(--prof "$usage_prof")
  ext_args+=(--prof "$usage_prof")
fi

rc=0
mise run sync-settings ${settings_args[@]+"${settings_args[@]}"} || rc=1
mise run sync-extensions ${ext_args[@]+"${ext_args[@]}"} || true
exit "$rc"
