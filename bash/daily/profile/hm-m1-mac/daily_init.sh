#!/usr/bin/env bash

emphasize_line() {
  printf "%b%s%b\n" "\\033[38;5;214m" "=== $1 ===" "\\033[0m"
}

MISE_UPGRADE_STATUS=0
emphasize_line "mise profile tools"
(cd "$HOME" && mise upgrade node pnpm 'npm:@openai/codex') || MISE_UPGRADE_STATUS=$?

emphasize_line "apm"
apm self-update

(
  cd "${DOTPATH}" || true
  emphasize_line "brew"
  (cd brew && mise run sync && mise run dump)
  emphasize_line "claude"
  (cd claude && mise run status)
  emphasize_line "codex"
  (cd codex && mise run status)
)

exit "$MISE_UPGRADE_STATUS"
