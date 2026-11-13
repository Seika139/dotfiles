#!/usr/bin/env bash

#MISE description="全プロファイルの settings.json (3 層) の重複キーとソート違反を検査する"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

resolve_python
rc=0
for dir in "${PROFILE_ROOT:-}"/*/; do
  "$PY" "$SETTINGS_PY" check --profile "$(basename "$dir")" || rc=1
done
if [ "$rc" != "0" ]; then
  echo "ソート違反は mise run sort で修正できます (重複キーは手で解消してください)" >&2
fi
exit "$rc"
