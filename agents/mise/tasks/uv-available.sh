#!/bin/bash

#MISE description="uv (Python ランタイム) が利用可能であることを確認する"
#MISE quiet=true
#MISE hide=true

# uv は profiles/private/apm.yml が存在するときのマージ処理 (PEP 723 inline
# metadata 経由で merge_apm_yml.py を実行) で必須。private overlay 未使用の PC
# でも依存上は要求するシンプル設計を採用 (apm-available.sh と同じ作法)。

if ! command -v uv &>/dev/null; then
  printf "%b%s%b%s\n" "\033[1;31m" "✘ Error" "\033[0m" ": uv is not installed or not in PATH." >&2
  printf "%s%b%s%b%s\n" "  See " "\033[1;34m" \
    "https://docs.astral.sh/uv/getting-started/installation/" "\033[0m" " to install uv:" >&2
  printf "%s\n" "    curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi
