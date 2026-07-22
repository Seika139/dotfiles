#!/usr/bin/env bash
# repo-preset: fzf の preview ペインに表示する内容を出力する
#
# 使い方: bash mise/scripts/repo-preset/preview.sh <component-name>
# fzf の --preview から `bash <path>/preview.sh {1}` の形で呼ばれる。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib.sh"

c_bold=$'\033[1m'
c_cyan=$'\033[36m'
c_yellow=$'\033[33m'
c_reset=$'\033[0m'

component="${1:-}"

if [[ -z "$component" ]]; then
  printf '(コンポーネント名が指定されていません)\n' >&2
  exit 1
fi

if [[ ! -d "${COMPONENTS_DIR}/${component}" ]]; then
  printf 'unknown component: %s\n' "$component" >&2
  exit 1
fi

printf '%s%s%s\n\n' "$c_bold" "$component" "$c_reset"

description="$(rp_meta_field "$component" DESCRIPTION)"
printf '%s\n' "$description"

depends=()
while IFS= read -r dep; do
  [[ -z "$dep" ]] && continue
  depends+=("$dep")
done < <(rp_depends_on "$component")

if [[ ${#depends[@]} -gt 0 ]]; then
  printf '\n%s依存:%s %s\n' "$c_cyan" "$c_reset" "${depends[*]}"
fi

# 推移的な閉包から、自身と常時入るもの(_common, pre-commit)を除いた
# 「この選択で追加で引き込まれるもの」を求める。
# rp_resolve_closure を command substitution で変数に受けて、
# 終了コード (存在しないコンポーネント時の非ゼロ) を検査できるようにする。
closure=()
closure_raw="$(rp_resolve_closure "$component")"
while IFS= read -r c; do
  [[ -z "$c" ]] && continue
  case "$c" in
  "$component" | _common | pre-commit) continue ;;
  esac
  closure+=("$c")
done <<<"$closure_raw"

if [[ ${#closure[@]} -gt 0 ]]; then
  printf '\n%s引き込み:%s %s\n' "$c_yellow" "$c_reset" "${closure[*]}"
fi
