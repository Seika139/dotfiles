#!/usr/bin/env bash
# textlint コンポーネントの post_scaffold
#
# 環境変数:
#   TARGET_DIR : 生成先ディレクトリ
#   OFFLINE    : 1 ならネット越しの操作をスキップ
#   DRY_RUN    : 1 なら実行せず「何をするか」を echo
#
# node/pnpm 自体のセットアップは js コンポーネントの post_scaffold が担う。
# ここでは textlint 関連の devDependencies 追加のみを行う。

set -euo pipefail

: "${TARGET_DIR:?}"
OFFLINE="${OFFLINE:-0}"
DRY_RUN="${DRY_RUN:-0}"

dim=$'\033[2m'; reset=$'\033[0m'
plan() { printf '%s    would: %s%s\n' "$dim" "$*" "$reset"; }

if ((DRY_RUN)); then
  if ((OFFLINE)); then
    plan "(offline) pnpm add -D ... はスキップ"
  else
    plan "pnpm add -D textlint textlint-rule-preset-ja-technical-writing textlint-rule-preset-ja-spacing"
  fi
  exit 0
fi

command -v pnpm >/dev/null || {
  printf 'pnpm が見つかりません。textlint コンポーネントには pnpm が必要です。\n' >&2
  exit 1
}

cd "$TARGET_DIR"

if ((OFFLINE)); then
  printf '  (offline) dev deps の追加をスキップ\n'
else
  pnpm add -D \
    textlint \
    textlint-rule-preset-ja-technical-writing \
    textlint-rule-preset-ja-spacing
fi
