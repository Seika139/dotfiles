#!/bin/bash

#MISE description="指定プロファイルの設定ファイルをシンボリックリンクする"
#MISE depends=["check_env"]
#MISE shell="bash -c"
#MISE quiet=true

# ---------------------------------------------------------------------------
# APM との共存方針:
#   ~/.codex/skills/<name>/ が APM により実 dir として作られている場合、
#   このスクリプトは touch しない (skills セクションの "Skipping skill because
#   target already exists" 経路でスキップする)。
#   APM 専管 skill 名 (aws-auth / login-microsoft / spark-* 等) は dotfiles 側
#   profiles/<prof>/skills/ にも置かないことで衝突を避ける。
#   instructions primitive は現時点では APM で deploy しない前提のため
#   ~/.codex/AGENTS.md は symlink で問題ないが、instructions 導入時には
#   AGENTS.md も APM 専管にする必要がある。
# ---------------------------------------------------------------------------

set -eu

if [ "${MISE_CONFIG_ROOT:-}" = "" ]; then
  MISE_CONFIG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi

PROFILES_DIR="${PROFILES_DIR:-profiles}"
local_toml="${MISE_CONFIG_ROOT}/mise.local.toml"

if [ "${IS_WSL:-}" = "" ]; then
  if [ "$(uname -s)" = "Linux" ] && [ -f /proc/version ] && grep -qi microsoft /proc/version; then
    IS_WSL=true
  else
    IS_WSL=false
  fi
fi

read_local_value() {
  key="$1"
  if [ -f "$local_toml" ]; then
    grep "^${key}" "$local_toml" 2>/dev/null | cut -d'"' -f2 || true
  fi
}

if $IS_WSL; then
  auto_detect_profile="${WSL_CODEX_PROFILE:-}"
  if [ -z "$auto_detect_profile" ]; then
    auto_detect_profile="$(read_local_value WSL_CODEX_PROFILE)"
  fi
else
  auto_detect_profile="${DEFAULT_CODEX_PROFILE:-}"
  if [ -z "$auto_detect_profile" ]; then
    auto_detect_profile="$(read_local_value DEFAULT_CODEX_PROFILE)"
  fi
fi

option_profile=""
while [ $# -gt 0 ]; do
  case "$1" in
  --prof)
    if [ $# -lt 2 ]; then
      printf "%s\n" "🚨 --prof requires a profile name." >&2
      exit 1
    fi
    option_profile="$2"
    shift 2
    ;;
  *)
    if [ -z "$option_profile" ] && [ "${1#-}" = "$1" ]; then
      option_profile="$1"
    fi
    shift
    ;;
  esac
done

PROFILE=$([ -n "$option_profile" ] && echo "$option_profile" || echo "$auto_detect_profile")

if [ -z "$PROFILE" ]; then
  printf "%s" "🚨 プロファイルが指定されていません。"
  printf "%s" "--prof オプションでプロファイルを指定するか、mise.local.toml に "
  printf "%s\n" "DEFAULT_CODEX_PROFILE または WSL_CODEX_PROFILE を設定してください。"
  exit 1
fi

if [ "${CODEX_PROFILE_LINK_SKIP_MISE_CHECK:-}" != "true" ] && command -v mise &>/dev/null; then
  cd "$MISE_CONFIG_ROOT" && mise run check --prof "$PROFILE" || exit 1
fi

PROFILE_PATH="${MISE_CONFIG_ROOT}/${PROFILES_DIR}/$PROFILE"
CODEX_HOME="${HOME}/.codex"
mkdir -p "$CODEX_HOME"
agents_sync="${MISE_CONFIG_ROOT}/mise/scripts/sync_agents.sh"

# prompts / skills は APM 管理 (dotfiles/agents/) に移行済のため本スクリプトでは扱わない。
# `mise run install`@agents/ で ~/.codex/skills/ に直接配備される
# (codex は user-scope で prompts 非対応 — agents/ 側で codex 用 prompts は配備されない)。
main_targets=(AGENTS.md custom-config hooks.json)
render_config="${MISE_CONFIG_ROOT}/mise/scripts/render_config.py"

printf "%s\n" "🦄 Linking Codex settings from profile: $PROFILE"

config_target="${CODEX_HOME}/config.toml"
if [ -f "$PROFILE_PATH/config.base.toml" ] || [ -f "$PROFILE_PATH/config.toml" ] || [ -f "$PROFILE_PATH/config.local.toml" ]; then
  tmp_config="$(mktemp)"
  "$render_config" --profile-path "$PROFILE_PATH" --output "$tmp_config"

  if [ -L "$config_target" ]; then
    printf "%s\n" "   Replacing config symlink with generated file: $config_target"
    rm "$config_target"
  elif [ -f "$config_target" ]; then
    if "$render_config" --profile-path "$PROFILE_PATH" --same-as "$config_target"; then
      :
    else
      backup="${config_target}.backup.$(date +%Y%m%d_%H%M%S)"
      printf "%s\n" "   Runtime config backup: $config_target -> $backup"
      cp -p "$config_target" "$backup"
    fi
  elif [ -d "$config_target" ]; then
    printf "%s\n" "🚨 Cannot write config because target is a directory: $config_target" >&2
    rm -f "$tmp_config"
    exit 1
  fi

  mv "$tmp_config" "$config_target"
  chmod 600 "$config_target"
  printf "%s\n" "   Generated runtime config: $config_target"
else
  printf "   ⚠️  Skipping config; no config.base.toml, config.toml, or config.local.toml in: \033[31m%s\033[0m\n" "$PROFILE_PATH"
fi

for file in "${main_targets[@]}"; do
  source="$PROFILE_PATH/$file"
  target="${CODEX_HOME}/$file"
  if [ ! -f "$source" ] && [ ! -d "$source" ]; then
    continue
  fi

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

for file in "${main_targets[@]}"; do
  source="$PROFILE_PATH/$file"
  target="${CODEX_HOME}/$file"

  if [ -f "$source" ] || [ -d "$source" ]; then
    printf "\\033[36m  "
    ln -sfnv "$source" "$target"
    printf "\\033[0m"
  else
    printf "   ⚠️  Skipping missing file: \\033[31m%s\\033[0m\n" "$source"
  fi
done

printf "%s\n" "🧩 Installing native Codex agents as regular files"
bash "$agents_sync" "$MISE_CONFIG_ROOT" "$CODEX_HOME"

# skills 配備は APM 管理 (dotfiles/agents/) に移行済のため本スクリプトでは扱わない。
# ~/.codex/skills/ への配備は `mise run install`@agents/ が直接行う。
# 古い per-skill symlink (`dotfiles/codex/profiles/*/skills/<n>` を指すもの) が残っていれば
# 安全のため掃除する (clean migration from 旧モデル -> APM モデル)。
skills_target="${CODEX_HOME}/skills"
if [ -d "$skills_target" ]; then
  for target in "$skills_target"/* "$skills_target"/.[!.]* "$skills_target"/..?*; do
    [ -e "$target" ] || continue
    [ -L "$target" ] || continue
    link_target="$(readlink "$target")"
    case "$link_target" in
    "$MISE_CONFIG_ROOT"/"$PROFILES_DIR"/*/skills/*)
      printf "%s\n" "   🗑️  Removing legacy profile skill symlink: $target"
      rm "$target"
      ;;
    esac
  done
fi

printf "%s\n" "✅ Linked Codex settings from profile '$PROFILE'"
