#!/usr/bin/env bash

#MISE description="選択したプリセット（lint/format 設定・mise tasks 等）を現在の git repo に導入する"
#MISE raw=true
#USAGE flag "--target <dir>" help="導入先ディレクトリ (デフォルト: カレントディレクトリ)" default="."
#USAGE flag "--components <csv>" help="導入するコンポーネント名をカンマ区切りで指定 (省略時は対話 fzf にフォールバック)"
#USAGE flag "--all" help="選択可能な全コンポーネントを導入する"
#USAGE flag "--main-guard" help="main への commit/push を禁止する pre-commit の guard 版を採用する"
#USAGE flag "--dry-run" help="書き込みを一切行わず、予定を出力する"
#USAGE flag "--force" help="既存ファイルがあっても上書きする (デフォルトは skip)"
#USAGE flag "--offline" help="ネットが必要な処理 (mise install / uv add / pnpm add 等) をスキップする"
#USAGE flag "--no-install" help="ファイル生成のみ行い、mise install / post_scaffold の実行系をスキップする"
#USAGE flag "--github-user <name>" help="プレースホルダ {{github_user}} に使う値"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

args=(--target "${usage_target:-.}")

if [[ -n "${usage_components:-}" ]]; then
  args+=(--components "${usage_components}")
fi
if [[ "${usage_all:-false}" == "true" ]]; then
  args+=(--all)
fi
if [[ "${usage_main_guard:-false}" == "true" ]]; then
  args+=(--main-guard)
fi
if [[ "${usage_dry_run:-false}" == "true" ]]; then
  args+=(--dry-run)
fi
if [[ "${usage_force:-false}" == "true" ]]; then
  args+=(--force)
fi
if [[ "${usage_offline:-false}" == "true" ]]; then
  args+=(--offline)
fi
if [[ "${usage_no_install:-false}" == "true" ]]; then
  args+=(--no-install)
fi
if [[ -n "${usage_github_user:-}" ]]; then
  args+=(--github-user "${usage_github_user}")
fi

exec bash "${ROOT_DIR}/mise/scripts/repo-preset/install.sh" "${args[@]}"
