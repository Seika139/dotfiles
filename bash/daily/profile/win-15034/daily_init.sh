#!/usr/bin/env bash

(
  cd "${DOTPATH}" || true
  (cd scoop && mise run sync && mise run dump)
  (cd winget && mise run update && mise run dump)
  (cd claude && mise run status)
  (cd codex && mise run status)
)
