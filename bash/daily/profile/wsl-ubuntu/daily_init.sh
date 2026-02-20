#!/usr/bin/env bash

# --with-apt オプションで apt update/upgrade も実行する
WITH_APT=false
for arg in "$@"; do
  case "$arg" in
  --with-apt) WITH_APT=true ;;
  esac
done

if "$WITH_APT"; then
  echo "=== apt update && upgrade (mise 本体含む) ==="
  sudo apt update && sudo apt upgrade -y
fi

# mise 管理のツール
echo "=== mise ==="
mise upgrade

# Volta 管理のツール（volta list から動的に取得）
echo "=== volta ==="
volta list all --format plain | awk '
  /^runtime .* \(default\)/ { name=$2; sub(/@[^@]*$/, "", name); print name }
  /^package-manager /        { name=$2; sub(/@[^@]*$/, "", name); print name }
  /^package .* \(default\)/  { name=$2; sub(/@[^@]*$/, "", name); print name }
' | sort -u | while read -r pkg; do
  echo "volta install ${pkg}@latest"
  volta install "${pkg}@latest"
done

# uv 本体（pipx 経由でインストール）
echo "=== uv ==="
pipx upgrade uv

if ! "$WITH_APT"; then
  echo ""
  echo "apt のアップデートはスキップしました（mise 本体含む）。実行する場合:"
  echo "  sudo apt update && sudo apt upgrade -y"
fi
