#!/bin/bash

#MISE description="指定プロファイルの設定ファイルをシンボリックリンクする"
#MISE depends=["check_env"]
#MISE shell="bash -c"
#MISE quiet=true

set -eu

if [ "${MISE_CONFIG_ROOT:-}" = "" ]; then
  MISE_CONFIG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi

local_toml="${MISE_CONFIG_ROOT}/mise.local.toml"

if $IS_WSL; then
  auto_detect_profile="${WSL_CLAUDE_PROFILE:-}"
  if [ -z "${auto_detect_profile}" ]; then
    auto_detect_profile=$(grep '^WSL_CLAUDE_PROFILE' "${local_toml}" | cut -d'"' -f2)
  fi
else
  auto_detect_profile="${DEFAULT_CLAUDE_PROFILE:-}"
  if [ -z "${auto_detect_profile}" ]; then
    auto_detect_profile=$(grep '^DEFAULT_CLAUDE_PROFILE' "${local_toml}" | cut -d'"' -f2)
  fi
fi

# 引数を順番にチェック
option_profile=""
while [ $# -gt 0 ]; do
  case "$1" in
  --prof)
    option_profile="$2"
    shift 2 # --profile と その値(wsl) の2つ分進める
    ;;
  *)
    shift # 不明な引数は無視して次へ
    ;;
  esac
done

PROFILE=$([ -n "$option_profile" ] && echo "$option_profile" || echo "$auto_detect_profile")

if [ -z "$PROFILE" ]; then
  printf "%s" "🚨 プロファイルが指定されていません。"
  printf "%s" "--prof オプションでプロファイルを指定するか、mise.local.toml に "
  printf "%s\n" "DEFAULT_CLAUDE_PROFILE または WSL_CLAUDE_PROFILE を設定してください。"
  exit 1
fi

if command -v mise &>/dev/null; then
  cd "${MISE_CONFIG_ROOT}" && mise run check --prof "$PROFILE" || exit 1
fi

PROFILE_PATH="${MISE_CONFIG_ROOT}/${PROFILES_DIR:-profiles}/$PROFILE"

# シンボリックリンクを作成するターゲットファイル・ディレクトリのリスト
targets=(settings.json settings.local.json CLAUDE.md commands skills custom-config)

printf "%s\n" "🦄 Linking Claude settings from profile: $PROFILE"

# 既存のシンボリックリンクを削除（ファイルの場合は退避）
for file in "${targets[@]}"; do
  target="${HOME}/.claude/$file"
  if [ -L "$target" ]; then
    printf "%s\n" "   Removing existing symlink: $target"
    rm "$target"
  elif [ -f "$target" ]; then
    backup="${target}.backup.$(date +%Y%m%d_%H%M%S)"
    printf "%s\n" "   既存のファイルをバックアップしました: $target -> $backup"
    mv "$target" "$backup"
  elif [ -d "$target" ]; then
    backup="${target}.backup.$(date +%Y%m%d_%H%M%S)"
    printf "%s\n" "   既存のディレクトリをバックアップしました: $target -> $backup"
    mv "$target" "$backup"
  fi
done

# シンボリックリンク作成
for file in "${targets[@]}"; do
  source="$PROFILE_PATH/$file"
  target="${HOME}/.claude/$file"

  if [ -f "$source" ] || [ -d "$source" ]; then
    printf "\\033[36m  "
    ln -sfnv "$source" "$target"
    printf "\\033[0m"
  else
    printf "   ⚠️  Skipping missing file: \\033[31m%s\\033[0m\n" "$source"
  fi
done

printf "%s\n" "✅ Linked Claude settings from profile '$PROFILE'"
