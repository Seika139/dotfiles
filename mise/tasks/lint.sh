#!/usr/bin/env bash

#MISE description="lint を実行する（既定: Markdown のみ、--all/-a: Markdown + ruff + shfmt + taplo）"
#MISE quiet=true

set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

for arg in "$@"; do
  case "$arg" in
  *)
    shift 1
    ;;
  esac
done

print_blue "Linting Markdown files"$'\n'
rumdl check .
markdownlint-cli2

print_blue "Lint shell scripts with shfmt"$'\n'
shfmt -d mise/tasks/**

print_blue "Lint toml with taplo"$'\n'
taplo fmt --check --diff
