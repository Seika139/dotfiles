#!/usr/bin/env bash

#MISE description="format を実行する（既定: Markdown のみ、--all/-a: Markdown + ruff + shfmt + taplo）"
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

print_blue "formatting Markdown files"$'\n'
rumdl check --fix .
markdownlint-cli2 --fix

print_blue "formatting shell scripts with shfmt"$'\n'
shfmt -w mise/tasks/**

print_blue "formatting toml with taplo"$'\n'
taplo fmt

print_blue "pnpm textlint --fix"$'\n'
pnpm textlint --fix --config .textlintrc.yml .
