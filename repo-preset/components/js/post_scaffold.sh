#!/usr/bin/env bash
# js コンポーネントの post_scaffold
#
# 環境変数:
#   TARGET_DIR   : 生成先ディレクトリ
#   PROJECT_NAME : プロジェクト名（package.json に埋め込む）
#   DRY_RUN      : 1 なら実行せず「何をするか」を echo

set -euo pipefail

: "${TARGET_DIR:?}"
: "${PROJECT_NAME:?}"
DRY_RUN="${DRY_RUN:-0}"

dim=$'\033[2m'; reset=$'\033[0m'
plan() { printf '%s    would: %s%s\n' "$dim" "$*" "$reset"; }

if ((DRY_RUN)); then
  plan "pnpm init"
  plan "patch package.json (name=${PROJECT_NAME}, private=true)"
  exit 0
fi

command -v pnpm >/dev/null || {
  printf 'pnpm が見つかりません。js コンポーネントには pnpm が必要です。\n' >&2
  exit 1
}

cd "$TARGET_DIR"

if [[ ! -f package.json ]]; then
  pnpm init >/dev/null
fi

if command -v node >/dev/null; then
  PROJECT_NAME="$PROJECT_NAME" node -e '
    const fs = require("fs");
    const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
    pkg.name = process.env.PROJECT_NAME;
    pkg.private = true;
    delete pkg.main;
    fs.writeFileSync("package.json", JSON.stringify(pkg, null, 2) + "\n");
  '
fi
