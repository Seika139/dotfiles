#!/usr/bin/env bash
# pre-commit コンポーネントの post_scaffold
#
# 環境変数:
#   TARGET_DIR : 生成先ディレクトリ（絶対パス）
#   OFFLINE    : 1 ならネット越しの操作をスキップ
#   DRY_RUN    : 1 なら実行せず「何をするか」を echo

set -euo pipefail

: "${TARGET_DIR:?}"
OFFLINE="${OFFLINE:-0}"
DRY_RUN="${DRY_RUN:-0}"

dim=$'\033[2m'; reset=$'\033[0m'
plan() { printf '%s    would: %s%s\n' "$dim" "$*" "$reset"; }

if ((DRY_RUN)); then
  plan "pre-commit install --install-hooks (pre-commit / pre-push)"
  plan "git secrets --install -f"
  plan "git secrets --register-aws"
  exit 0
fi

cd "$TARGET_DIR"

if command -v pre-commit >/dev/null; then
  if ((OFFLINE)); then
    pre-commit install
  else
    pre-commit install --install-hooks
  fi
else
  printf 'pre-commit が見つかりません。インストール後に `pre-commit install` を実行してください。\n' >&2
fi

if command -v git >/dev/null && git rev-parse --git-dir >/dev/null 2>&1; then
  if command -v git-secrets >/dev/null; then
    git secrets --install -f
    git secrets --register-aws
  else
    printf 'git-secrets が見つかりません。インストール後に `git secrets --install -f` と `git secrets --register-aws` を実行してください。\n' >&2
  fi
fi
