#!/usr/bin/env bash

#MISE description="現在のプロファイル設定と~/.codexの状態を比較"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"
#USAGE flag "--diff-with <file>" help="比較対象のファイル"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

PROFILE="$(codex_profile_or_default "${usage_prof:-}")"
PROFILE_PATH="$(codex_profile_path "$ROOT_DIR" "$PROFILE")"

render_script="${ROOT_DIR}/mise/scripts/render_config.py"

explicit_target="${usage_diff_with:-}"
config_target="${explicit_target:-${HOME}/.codex/config.toml}"

print_green "+ Only in $PROFILE_PATH"$'\n'
print_red "- Only in $config_target"$'\n'
print_cyan "~ Diff between $config_target -> $PROFILE_PATH"$'\n'

echo "以下が差分です:"

"$render_script" --profile-path "$PROFILE_PATH" --diff-with "$config_target"
