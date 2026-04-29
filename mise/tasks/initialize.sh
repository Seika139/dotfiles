#!/usr/bin/env bash

#MISE description="brain instance の初期化（ディレクトリ作成、依存同期、index .env 作成）"
#MISE quiet=true
#MISE hide=true

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

print_blue "pnpm install"$'\n'
pnpm install
