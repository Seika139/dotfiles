#!/usr/bin/env bash
# repo-preset: 選択された領域コンポーネント名を改行区切りで stdout に出力する
#
# 実インストールは行わない(install.sh の責務)。install.sh から呼ばれ、
# 選択結果をコマンド置換で受け取る想定。
#
# 使い方:
#   bash select.sh --all
#   bash select.sh --components markdown,shell
#   bash select.sh              # TTY かつ fzf があれば対話選択
#
# 出力方針: 選択結果(コンポーネント名群)のみを stdout に出す。
# ログ/プロンプトは全て stderr に出す。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib.sh"

all=0
components_csv=""

while [[ $# -gt 0 ]]; do
  case "$1" in
  --all)
    all=1
    shift
    ;;
  --components)
    components_csv="${2:-}"
    shift 2
    ;;
  --components=*)
    components_csv="${1#--components=}"
    shift
    ;;
  *)
    printf 'select.sh: unknown option: %s\n' "$1" >&2
    exit 1
    ;;
  esac
done

if ((all)); then
  rp_selectable_components
  exit 0
fi

if [[ -n "$components_csv" ]]; then
  IFS=',' read -ra parts <<<"$components_csv"
  for part in "${parts[@]}"; do
    [[ -z "$part" ]] && continue
    printf '%s\n' "$part"
  done
  exit 0
fi

if [[ ! -t 0 ]]; then
  printf 'select.sh: TTY がありません。--all か --components を指定してください。\n' >&2
  exit 1
fi

if ! command -v fzf >/dev/null 2>&1; then
  printf 'select.sh: fzf が見つかりません。--all か --components を指定してください。\n' >&2
  exit 1
fi

# shellcheck disable=SC1091
source "${ROOT_DIR}/bash/public/61_fzf.bash"

options=()
while IFS= read -r name; do
  [[ -z "$name" ]] && continue
  description="$(rp_meta_field "$name" DESCRIPTION)"
  options+=("$(printf '%s\t%s' "$name" "$description")")
done < <(rp_selectable_components)

if [[ ${#options[@]} -eq 0 ]]; then
  printf 'select.sh: 選択可能なコンポーネントがありません。\n' >&2
  exit 1
fi

mapfile -t selected < <(
  select_multi \
    --prompt "導入するコンポーネントを選択 > " \
    --preview "bash '${SCRIPT_DIR}/preview.sh' {1}" \
    --preview-window 'right,55%,wrap' \
    -- "${options[@]}"
)

printf '%s\n' "${selected[@]}"
