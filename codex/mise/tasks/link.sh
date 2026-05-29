#!/usr/bin/env bash

#MISE description="指定プロファイルの設定ファイルを~/.codexへ反映する"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

args=()
if [ -n "${usage_prof:-}" ]; then
  args+=(--prof "$usage_prof")
fi

bash "${ROOT_DIR}/mise/scripts/link.sh" "${args[@]}"
