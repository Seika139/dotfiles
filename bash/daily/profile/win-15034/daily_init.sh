#!/usr/bin/env bash

emphasize_line() {
  printf "%b%s%b\n" "\\033[38;5;214m" "=== $1 ===" "\\033[0m"
}

if command -v volta &>/dev/null; then
  emphasize_line "volta"
  volta install node@latest @openai/codex@latest
fi

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
