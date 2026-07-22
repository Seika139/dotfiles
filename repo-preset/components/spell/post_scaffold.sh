#!/usr/bin/env bash
# spell コンポーネントの post_scaffold
#
# 呼び出し側が以下の環境変数を与えることを想定:
#   TARGET_DIR    : 生成先ディレクトリ（絶対パス）
#   COMPONENT_DIR : このコンポーネントのソースディレクトリ
#   OFFLINE       : 1 ならネット越しの操作をスキップ
#   DRY_RUN       : 1 なら実行せず「何をするか」を echo
#
# .cspell.json は project-words 辞書のみを参照しており、追加の
# @cspell/dict-* パッケージは不要なため cspell 本体のみを devDependency に追加する。

set -euo pipefail

: "${TARGET_DIR:?}"
: "${COMPONENT_DIR:?}"
OFFLINE="${OFFLINE:-0}"
DRY_RUN="${DRY_RUN:-0}"

dim=$'\033[2m'; reset=$'\033[0m'
plan() { printf '%s    would: %s%s\n' "$dim" "$*" "$reset"; }

if ((DRY_RUN)); then
  plan "pnpm add -D cspell"
  exit 0
fi

if ((OFFLINE)); then
  printf '  (offline) cspell の追加をスキップ\n'
  exit 0
fi

command -v pnpm >/dev/null || {
  printf 'pnpm が見つかりません。spell コンポーネントには pnpm が必要です。\n' >&2
  exit 1
}

cd "$TARGET_DIR"

pnpm add -D cspell
