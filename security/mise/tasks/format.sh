#!/bin/bash
#MISE description="コードのフォーマットを実行します"
#MISE shell="bash -c"
#MISE quiet=true

# shellcheck disable=SC1091

set -u

# ── Load common utilities ────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

# --- Shell ---
if command -v shfmt >/dev/null 2>&1; then
  info "Running shfmt..."
  find . -type f \( -name "*.sh" -o -name "*.bash" \) \
    -not -path "./.venv/*" \
    -not -path "*/node_modules/*" \
    -not -path "./.git/*" \
    -not -path "./.cache/*" \
    -print0 | xargs -0 shfmt -w -i 2 -ci
  info "shfmt formatting complete."
else
  error "shfmt is not installed; skipping shell script formatting."
fi
