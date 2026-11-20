#!/usr/bin/env bash

prune_mise() {
  local before after
  local root

  root=$(mise where 2>/dev/null | head -1)

  # macOS / Windows Git Bash 共通
  if [[ -z "$root" ]]; then
    root="$HOME"
  fi

  before=$(df -Pk "$root" | awk 'NR==2 {print $4}')
  mise prune --yes --tools || return 1
  after=$(df -Pk "$root" | awk 'NR==2 {print $4}')

  awk -v before="$before" -v after="$after" '
    BEGIN {
      printf "mise prune によるディスク空き容量の増加: %+.2f MiB\n",
        (after - before) / 1024
    }'
}
