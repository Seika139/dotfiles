#!/usr/bin/env bash

# VSCode の dotfiles 機能から install.sh を実行するための wrapper スクリプト
# install.sh は source で実行する必要があるため、このスクリプトが間に入る

set -euo pipefail

# dotfiles のルートディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 非対話モードを有効化（DevContainer 環境用）
export REMOTE_CONTAINERS=true

echo "🚀 dotfiles のインストールを開始します..."

# source で install.sh を実行
# shellcheck disable=SC1091
if [ -f "${SCRIPT_DIR}/install.sh" ]; then
  source "${SCRIPT_DIR}/install.sh"
  echo "✅ dotfiles のインストールが完了しました"
else
  echo "❌ エラー: ${SCRIPT_DIR}/install.sh が見つかりません"
  exit 1
fi
