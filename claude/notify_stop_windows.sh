#!/usr/bin/env bash

set +e

if [[ -n "${1:-}" ]]; then
  export NOTIFY_TOOL_NAME="$1"
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ps_script="${script_dir}/notify_stop_windows.ps1"

if [[ ! -f "$ps_script" ]]; then
  exit 0
fi

if command -v cygpath >/dev/null 2>&1; then
  ps_script="$(cygpath -w "$ps_script" 2>/dev/null || printf '%s' "$ps_script")"
fi

if command -v pwsh.exe >/dev/null 2>&1; then
  pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "$ps_script" >/dev/null 2>&1
elif command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ps_script" >/dev/null 2>&1
fi

exit 0
