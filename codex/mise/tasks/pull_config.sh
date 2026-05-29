#!/usr/bin/env bash

#MISE description="現在の~/.codex/config.tomlをプロファイルのconfig.local.tomlへ取り込む"
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

bash "${ROOT_DIR}/mise/scripts/pull_config.sh" "${args[@]}"
