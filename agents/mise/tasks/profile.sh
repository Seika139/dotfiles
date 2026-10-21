#!/bin/bash

#MISE description="プロファイルに関連する操作（list, check）を実行する"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE arg "[subcommand]" help="実行するサブコマンド" {
#USAGE   choices "profile-check" "profile-list"
#USAGE }
#USAGE flag "--prof <prof>" help="プロファイル名"

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=mise/common.sh
# shellcheck disable=SC1901
source "${ROOT_DIR}/mise/common.sh"

SELECTED_PROFILE="${usage_prof:-}"

PROFILE_OPERATIONS=(
  $'profile-check\t指定プロファイルが存在するかを確認し、なければエラーを返す'
  $'profile-list\t利用可能なプロファイルの一覧を表示する'
)

subcommand_or_fail() {
  local value="$1"
  case "$value" in
  profile-check | profile-list)
    printf "%s\n" "$value"
    ;;
  "")
    if [ -t 0 ]; then
      select_one --prompt "サブコマンドを選択 > " -- "${PROFILE_OPERATIONS[@]}"
      return
    fi
    print_red "[Error] サブコマンドを指定してください: profile-check / profile-list"$'\n' >&2
    exit 1
    ;;
  *)
    print_red "[Error] Unknown Subcommand '$value'"$'\n' >&2
    exit 1
    ;;
  esac
}

subcommand="$(subcommand_or_fail "${usage_subcommand:-}")"

case "$subcommand" in
profile-check)
  if [ -z "$SELECTED_PROFILE" ]; then
    mise run profile-check
  else
    mise run profile-check --prof "$SELECTED_PROFILE"
  fi
  ;;
profile-list)
  mise run profile-list
  ;;
*)
  print_red "[Error] Unknown Subcommand '$subcommand'"$'\n' >&2
  exit 1
  ;;
esac
