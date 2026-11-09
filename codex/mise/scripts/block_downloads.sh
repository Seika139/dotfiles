#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# Do not resolve mise shims against the untrusted session cwd (which may contain a mise.toml).
if ! cd -- "$SCRIPT_DIR"; then
  printf '%s\n' "Codex prompt blocked: cannot enter the trusted dotfiles directory." >&2
  exit 2
fi

# shellcheck disable=SC1091
if ! source "${SCRIPT_DIR}/../common.sh"; then
  printf '%s\n' "Codex prompt blocked: cannot load the Python resolver." >&2
  exit 2
fi

if ! PYTHON="$(codex_python)"; then
  printf '%s\n' "Codex prompt blocked: Python 3.11+ is unavailable in Codex's PATH." >&2
  exit 2
fi

"$PYTHON" -I "${SCRIPT_DIR}/block_downloads.py"
result=$?
if [ "$result" -eq 0 ]; then
  exit 0
fi
printf '%s\n' "Codex prompt blocked: Downloads guard returned non-zero status ($result)." >&2
exit 2
