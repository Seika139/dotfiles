#!/usr/bin/env bash

if command -v volta &>/dev/null; then
  volta install node@latest @openai/codex@latest
fi

(
  cd "${DOTPATH}" || true
  if command -v scoop &>/dev/null; then
    (cd scoop && mise run sync && mise run dump)
  fi
  if command -v winget &>/dev/null; then
    (cd winget && mise run update && mise run dump)
  fi
  if [ -e "${DOTPATH}/claude" ]; then
    (cd claude && mise run status)
  fi
  if [ -e "${DOTPATH}/codex" ]; then
    (cd codex && mise run status)
  fi
  if [ -d "${HOME}/programs/cyg-genai/.claude-template" ]; then
    cd "${HOME}/programs/cyg-genai/.claude-template" || true
    git pull origin main
  fi
)
