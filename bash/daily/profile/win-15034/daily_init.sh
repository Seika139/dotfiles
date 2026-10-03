#!/usr/bin/env bash

emphasize_line() {
  printf "%b%s%b\n" "\\033[38;5;214m" "=== $1 ===" "\\033[0m"
}

MISE_UPGRADE_STATUS=0
emphasize_line "mise profile tools"
(cd "$HOME" && mise upgrade node 'npm:@openai/codex' 'npm:aws-cdk' 'npm:@dotenvx/dotenvx' 'npm:@google/clasp' 'npm:@github/copilot' 'npm:ccusage' 'npm:typescript' 'npm:webpack' 'npm:webpack-cli') || MISE_UPGRADE_STATUS=$?

(
  cd "${DOTPATH}" || true
  if command -v scoop &>/dev/null; then
    emphasize_line "scoop"
    (cd scoop && mise run sync && mise run dump)
  fi
  if command -v winget &>/dev/null; then
    emphasize_line "winget"
    (cd winget && mise run update && mise run dump)
  fi
  if [ -e "${DOTPATH}/claude" ]; then
    emphasize_line "claude"
    (cd claude && mise run status)
  fi
  if [ -e "${DOTPATH}/codex" ]; then
    emphasize_line "codex"
    (cd codex && mise run status)
  fi
  if [ -d "${HOME}/programs/cyg-genai/.claude-template" ]; then
    cd "${HOME}/programs/cyg-genai/.claude-template" || true
    git pull origin main
  fi
)

exit "$MISE_UPGRADE_STATUS"
