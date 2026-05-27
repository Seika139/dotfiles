#!/bin/bash

#MISE description="指定プロファイルの apm.yml に従い APM packages を user scope (~/.claude/skills, ~/.codex/skills 等) に install する"
#MISE depends=["check"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"

# 前提 (未検証): `apm install -g` は cwd の apm.yml を読んで `-g` 配備する。
# 違っていれば user 初回実行時に失敗が出るので、その時点で `apm install -g <pkg>` の
# ループ実装に切り替える。

if [ "$IS_WSL" = "true" ]; then
  DEFAULT_PROFILE="${WSL_AGENTS_PROFILE:-}"
else
  DEFAULT_PROFILE="${DEFAULT_AGENTS_PROFILE:-}"
fi
PROFILE="${usage_prof:-$DEFAULT_PROFILE}"
PROFILE_PATH="{{config_root}}/$PROFILES_DIR/$PROFILE"

if ! command -v apm &>/dev/null; then
  {
    printf "%s\n" "🚨 'apm' CLI が見つかりません。"
    printf "%s\n" "   インストール (mac/linux): curl -sSL https://aka.ms/apm-unix | sh"
    printf "%s\n" "   インストール (win):       irm https://aka.ms/apm-windows | iex"
  } >&2
  exit 1
fi

printf "%s\n" "🦄 Installing APM packages from profile: $PROFILE"
printf "   profile path: \\033[36m%s\\033[0m\n" "$PROFILE_PATH"

cd "$PROFILE_PATH"

if [ -f "apm.lock.yaml" ]; then
  apm install -g --frozen
else
  printf "%s\n" "ℹ️  apm.lock.yaml が無いため初回 install を実行 (lock を生成します)"
  apm install -g
fi

printf "%s\n" "✅ Installed APM packages from profile '$PROFILE' to user scope"
