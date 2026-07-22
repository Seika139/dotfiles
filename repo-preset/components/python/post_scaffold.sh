#!/usr/bin/env bash
# python コンポーネントの post_scaffold
#
# 呼び出し側が以下の環境変数を与えることを想定:
#   TARGET_DIR      : 生成先ディレクトリ（絶対パス）
#   COMPONENT_DIR   : このコンポーネントのソースディレクトリ
#   PROJECT_SLUG    : uv が受け入れる名前 (小文字+英数+ハイフン推奨)
#   OFFLINE         : 1 ならネット越しの操作をスキップ
#   DRY_RUN         : 1 なら実行せず「何をするか」を echo
#
# Python バージョンは mise.toml ([tools] python = "latest") 側で管理するため、
# uv init に --python は渡さない（uv が利用可能なインタプリタから解決する）。

set -euo pipefail

: "${TARGET_DIR:?}"
: "${COMPONENT_DIR:?}"
: "${PROJECT_SLUG:?}"
OFFLINE="${OFFLINE:-0}"
DRY_RUN="${DRY_RUN:-0}"

dim=$'\033[2m'; reset=$'\033[0m'
plan() { printf '%s    would: %s%s\n' "$dim" "$*" "$reset"; }

if ((DRY_RUN)); then
  plan "uv init --bare --name ${PROJECT_SLUG} ."
  if ((OFFLINE)); then
    plan "(offline) uv add --dev ... はスキップ"
  else
    plan "uv add --dev ruff mypy pytest"
  fi
  plan "append pyproject.overlay.toml to pyproject.toml"
  exit 0
fi

command -v uv >/dev/null || {
  printf 'uv が見つかりません。python コンポーネントには uv が必要です。\n' >&2
  exit 1
}

cd "$TARGET_DIR"

if [[ ! -f pyproject.toml ]]; then
  uv init --bare --vcs none --no-readme --no-pin-python \
    --name "$PROJECT_SLUG" \
    .
fi

# .python-version は mise.toml 側で管理するため作らない

if ((OFFLINE)); then
  printf '  (offline) dev deps の追加をスキップ\n'
else
  uv add --dev ruff mypy pytest
fi

# overlay を pyproject.toml に追記（冪等性のためマーカーでガード）
overlay="${COMPONENT_DIR}/pyproject.overlay.toml"
marker='# === post_scaffold: python overlay ==='
if [[ -f "$overlay" ]] && ! grep -qF "$marker" pyproject.toml; then
  {
    printf '\n%s\n' "$marker"
    cat "$overlay"
  } >>pyproject.toml
fi
