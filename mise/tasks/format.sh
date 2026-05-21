#!/usr/bin/env bash

#MISE description="format（rumdl + markdownlint-cli2 + textlint + shfmt + taplo）"
#MISE quiet=true
#USAGE flag "-t --textlint" {
#USAGE   help "textlintも実行する場合はこのフラグを指定してください（時間がかかる場合があります）"
#USAGE }

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
RUST_LOG=warn taplo fmt

if [ "${usage_textlint:-}" = "true" ]; then
  print_blue "formatting text files with textlint"$'\n'
  node node_modules/textlint/bin/textlint.js --fix --config .textlintrc.yml .
fi
