#!/usr/bin/env bash

#MISE description="lint（rumdl + markdownlint-cli2 + textlint + shfmt + taplo）"
#MISE quiet=true
#USAGE flag "-t --textlint" {
#USAGE   help "textlintも実行する場合はこのフラグを指定してください（時間がかかる場合があります）"
#USAGE }

# 途中でエラーが出ても他のファイルのリントは続行するため、set -e は使用しない
set -uo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

for arg in "$@"; do
  case "$arg" in
  *)
    shift 1
    ;;
  esac
done

print_blue "linting Markdown files"$'\n'
rumdl check .
markdownlint-cli2

print_blue "linting shell scripts with shfmt"$'\n'
shfmt -d mise/tasks/**

print_blue "linting toml with taplo"$'\n'
RUST_LOG=warn taplo fmt --check --diff

if [ "${usage_textlint:-}" = "true" ]; then
  print_blue "linting text files with textlint"$'\n'
  node node_modules/textlint/bin/textlint.js --config .textlintrc.yml .
fi
