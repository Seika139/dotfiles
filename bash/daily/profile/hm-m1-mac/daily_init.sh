#!/usr/bin/env bash

emphasize_line() {
  printf "%b%s%b\n" "\\033[38;5;214m" "=== $1 ===" "\\033[0m"
}

emphasize_line "volta"
volta install node@latest

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
