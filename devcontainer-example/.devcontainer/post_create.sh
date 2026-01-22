#!/bin/bash
set -Eeuo pipefail

echo "🚀 Setting up development environment..."

bash .devcontainer/check_git_config.sh

# # Git設定の確認と設定
# echo "🔧 Checking Git configuration..."
# # 改善版のcheck_git_config.shを実行（非対話モードの場合は環境変数から自動設定）
# if [ -f ".devcontainer/check_git_config.sh" ]; then
#   # CI環境や非対話モードでは入力をスキップ
#   if [ -t 0 ]; then
#     # 対話モード（TTYが利用可能）
#     bash .devcontainer/check_git_config.sh
#   else
#     # 非対話モード - 環境変数からの自動設定のみ試みる
#     bash .devcontainer/check_git_config.sh < /dev/null
#   fi
# else
#   echo "⚠️  .devcontainer/check_git_config.sh が見つかりませんでした。"
# fi

# uvキャッシュディレクトリのセットアップ
# echo "📁 Setting up uv cache directory..."
# sudo mkdir -p /home/vscode/.cache/uv
# sudo chown -R vscode:vscode /home/vscode/.cache

# ワークスペースと仮想環境の権限設定
echo "🔐 Setting up workspace permissions..."
# ワークスペースのマウント方式によっては chown が許可されないため、可否をプローブする
chown_probe="$(mktemp -p /workspaces .chown_probe.XXXXXX 2>/dev/null || true)"
if [[ -n "${chown_probe}" ]] && sudo chown vscode:vscode "${chown_probe}" 2>/dev/null; then
  rm -f "${chown_probe}"
  sudo chown -R vscode:vscode /workspaces
  chmod -R +w /workspaces 2>/dev/null || true
else
  rm -f "${chown_probe:-}" 2>/dev/null || true
  echo "⚠️  Workspace chown is not permitted on this mount. Skipping."
fi

# ホストからバインドしている ~/.claude ディレクトリの権限設定（失敗しても継続）
if ! sudo chown -R vscode:vscode /home/vscode/.claude 2>/dev/null; then
  echo "⚠️  /home/vscode/.claude の chown に失敗しました。権限変更をスキップします。"
fi

# echo "🔄 Resetting and initializing virtual environment..."
# mise trust -a

# echo "📦 Installing dependencies..."
# mise run fix-permissions
# mise run init

# echo "✅ Development environment setup completed!"
