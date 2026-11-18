#!/usr/bin/env bash

#MISE description="pre-commit hook を検証してインストールする"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  printf 'Git リポジトリ内で実行してください。\n' >&2
  exit 1
fi

if ! git config --global --includes --get-regexp '^secrets\.(patterns|providers)$' >/dev/null 2>&1; then
  printf '%s\n' "git-secrets の禁止パターンが未登録です。各PCの ~/.gitconfig.local に同じ secrets.patterns または secrets.providers を登録してください。" >&2
  exit 1
fi

mise install pre-commit python
if [[ "${OS:-}" == "Windows_NT" ]]; then
  mise run install-git-secrets
else
  mise install aqua:awslabs/git-secrets
fi

pre-commit validate-config

pre-commit install
