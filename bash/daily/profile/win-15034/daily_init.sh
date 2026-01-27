#!/usr/bin/env bash

volta install node@latest @anthropic-ai/claude-code@latest @openai/codex@latest

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
  if [ -d "${DOTPATH}/programs/cyg-genai" ]; then
    cd ~/programs/cyg-genai/.claude-template || true
    git pull origin main
  fi
)
