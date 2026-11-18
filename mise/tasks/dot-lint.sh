#!/usr/bin/env bash

#MISE description="lint（dprint + rumdl + markdownlint-cli2 + textlint + shfmt + shellcheck + tombi + yamllint）"
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
dprint check --allow-no-files
rumdl check .
markdownlint-cli2

# shfmt と shellcheck でチェックするファイル・ディレクトリのリスト
shell_files=(
  install.sh
  unlink.sh
  bash/
  mise/tasks/
  agents/mise/tasks/
)

print_blue "linting shell scripts with shfmt"$'\n'
find "${shell_files[@]}" -type f \
  \( -name "*.sh" -o -name "*.bash" \) -print0 |
  xargs -0 shfmt -d

print_blue "linting shell scripts with shellcheck"$'\n'
find "${shell_files[@]}" -type f \
  \( -name "*.sh" -o -name "*.bash" \) -print0 |
  xargs -0 shellcheck -x

print_blue "linting toml with tombi"$'\n'
# 走査範囲を絞るため、git 管理下（未追跡含む・ignore 除く）の toml だけを渡す
toml_files=()
while IFS= read -r f; do toml_files+=("$f"); done < <(git ls-files -co --exclude-standard -- "*.toml")
if [ "${#toml_files[@]}" -gt 0 ]; then
  tombi format --check --diff "${toml_files[@]}"
  tombi lint "${toml_files[@]}"
fi

print_blue "linting YAML files with yamllint"$'\n'
yamllint .

if [ "${usage_textlint:-}" = "true" ]; then
  print_blue "linting text files with textlint"$'\n'
  node node_modules/textlint/bin/textlint.js --config .textlintrc.yml .
fi
