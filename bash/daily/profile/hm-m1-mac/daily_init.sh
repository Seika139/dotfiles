#!/usr/bin/env bash

volta install node@latest

(
  cd "${DOTPATH}" || true
  (cd brew && mise run sync && mise run dump)
  (cd claude && mise run status)
  (cd codex && mise run status)
)
