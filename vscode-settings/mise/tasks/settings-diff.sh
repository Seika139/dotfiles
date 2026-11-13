#!/usr/bin/env bash

#MISE description="合成した settings.json とエディタの現在の settings.json の差分を表示する"
#MISE depends=["ensure_local_env"]
#USAGE flag "--prof <prof>" {
#USAGE   help "プロファイル名"
#USAGE }

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

resolve_profile
resolve_python
for editor in "${EDITORS[@]}"; do
  editor_path="$(editor_path_for "$editor")"
  printf "\n比較対象:\033[36m %s\033[0m\n" "$editor_path/settings.json"
  # 差分があると非 0 を返すが、表示が目的なので続行する
  "$PY" "$SETTINGS_PY" diff --profile "$PROFILE" --target "$editor_path/settings.json" || true
done
