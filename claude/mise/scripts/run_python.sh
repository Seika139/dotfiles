#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  printf 'Usage: %s <script.py> [arguments... ]\n' "${0##*/}" >&2
  exit 2
fi

script_path="$1"
shift

python_command=()
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
    "$candidate" -I -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 6) else 1)' >/dev/null 2>&1; then
    python_command=("$candidate")
    break
  fi
done

if [[ ${#python_command[@]} -eq 0 ]] && command -v py >/dev/null 2>&1 &&
  py -3 -I -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 6) else 1)' >/dev/null 2>&1; then
  python_command=(py -3)
fi

if [[ ${#python_command[@]} -eq 0 ]]; then
  printf 'Python 3.6 or newer is required. Install it as python3, python, or py -3.\n' >&2
  exit 1
fi

python_platform="$("${python_command[@]}" -I -c 'import sys; print(sys.platform)' 2>/dev/null)"
case "$(uname -s)" in
  CYGWIN* | MINGW* | MSYS*)
    if [[ "$python_platform" == win32 ]]; then
      if ! command -v cygpath >/dev/null 2>&1; then
        printf 'cygpath is required to pass paths to Windows Python from this shell.\n' >&2
        exit 1
      fi
      script_path="$(cygpath -aw "$script_path")"
      arguments=("$@")
      for ((index = 0; index < ${#arguments[@]}; index++)); do
        case "${arguments[index]}" in
          --claude-dir | --cursor-dir | --source-mcp | --mcp-source)
            if ((index + 1 >= ${#arguments[@]})); then
              printf 'Missing path after %s.\n' "${arguments[index]}" >&2
              exit 2
            fi
            arguments[index + 1]="$(cygpath -aw "${arguments[index + 1]}")"
            index=$((index + 1))
            ;;
          --claude-dir=* | --cursor-dir=* | --source-mcp=* | --mcp-source=*)
            path_value="${arguments[index]#*=}"
            arguments[index]="${arguments[index]%%=*}=$(cygpath -aw "$path_value")"
            ;;
        esac
      done
      set -- "${arguments[@]}"
    fi
    ;;
esac

exec "${python_command[@]}" "$script_path" "$@"
