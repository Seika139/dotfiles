#!/usr/bin/env bash

# Apply the environment for tools installed by mise to the current shell.
# Git Bash and Cygwin must use POSIX-converted shims instead of `mise env`:
# that command emits Windows PATH entries which can break Unix command lookup.
dotfiles_load_mise_environment() {
  local home_dir="$1"
  local shell_type="${2:-${OSTYPE:-}}"
  local mise_environment
  local mise_shims

  case "${shell_type}" in
  msys* | cygwin*)
    if ! command -v cygpath >/dev/null 2>&1; then
      printf 'cygpath is required to load mise tools in this shell.\n' >&2
      return 1
    fi

    mise_shims="$(cygpath -u "${LOCALAPPDATA:-${HOME}/AppData/Local}/mise/shims" 2>/dev/null)" || return 1
    if [[ ! -d "${mise_shims}" ]]; then
      (cd -- "${home_dir}" && mise reshim) || return $?
      mise_shims="$(cygpath -u "${LOCALAPPDATA:-${HOME}/AppData/Local}/mise/shims" 2>/dev/null)" || return 1
    fi
    if [[ ! -d "${mise_shims}" ]]; then
      printf 'mise shims directory is unavailable after installation: %s\n' "${mise_shims}" >&2
      return 1
    fi

    case ":${PATH}:" in
    *":${mise_shims}:"*) ;;
    *) export PATH="${mise_shims}:${PATH}" ;;
    esac
    ;;
  *)
    if ! mise_environment="$(cd -- "${home_dir}" && mise env -s bash)"; then
      printf 'Could not load the mise Bash environment after installing profile tools.\n' >&2
      return 1
    fi
    if ! eval "${mise_environment}"; then
      printf 'Could not apply the mise Bash environment after installing profile tools.\n' >&2
      return 1
    fi
    ;;
  esac
}
