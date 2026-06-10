#!/usr/bin/env bash

#MISE description="現在のプロファイル設定と~/.codexの状態を確認"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

PROFILE="$(codex_profile_or_default "${usage_prof:-}")"
PROFILE_PATH="$(codex_profile_path "$ROOT_DIR" "$PROFILE")"

printf "%s\n" "🦄 Environment Check"
printf "os()                 =\\033[36m %s\\033[0m\n" "$(codex_os_name)"
printf "IS_WSL               =\\033[36m %s\\033[0m\n" "${IS_WSL:-false}"
printf "config_root          =\\033[36m %s\\033[0m\n" "$ROOT_DIR"
printf "Selected profile     =\\033[36m %s\\033[0m\n" "$PROFILE"

if [ ! -d "$PROFILE_PATH" ]; then
  printf "❌ Profile directory does not exist:\\033[36m %s\\033[0m\n" "$PROFILE_PATH"
  exit 1
fi

printf "\n📂 Original files and directories:\n"
# NOTE: prompts/ skills/ は APM 管理 (dotfiles/agents/) に移行済のためチェック対象外。
profile_targets=(AGENTS.md custom-config hooks.json)
for file in "${profile_targets[@]}"; do
  source="$PROFILE_PATH/$file"
  if [ -f "$source" ] || [ -d "$source" ]; then
    printf "%s\n" "   ✅ $source"
  else
    printf "\\033[31m%s\\033[0m\n" "   ❌ $source (missing)"
  fi
done

printf "\n⚙️ Config sources:\n"
for file in config.base.toml config.local.toml config.toml; do
  source="$PROFILE_PATH/$file"
  if [ -f "$source" ]; then
    if [ "$file" = "config.local.toml" ]; then
      printf "%s\n" "   ✅ $source (git-ignored local/private)"
    elif [ "$file" = "config.toml" ] && [ -f "$PROFILE_PATH/config.base.toml" ]; then
      printf "%s\n" "   ⚠️  $source (legacy; ignored because config.base.toml exists)"
    else
      printf "%s\n" "   ✅ $source"
    fi
  elif [ "$file" = "config.local.toml" ]; then
    printf "%s\n" "   ⭕ $source (optional)"
  elif [ "$file" = "config.toml" ] && [ -f "$PROFILE_PATH/config.base.toml" ]; then
    printf "%s\n" "   ⭕ $source (legacy optional)"
  else
    printf "\\033[33m%s\\033[0m\n" "   ❌ $source (missing)"
  fi
done

printf "\n⚙️ Runtime config in\\033[36m %s/.codex:\\033[0m\n" "$HOME"
config_target="${HOME}/.codex/config.toml"
render_script="${ROOT_DIR}/mise/scripts/render_config.py"
if [ -f "$PROFILE_PATH/config.base.toml" ] || [ -f "$PROFILE_PATH/config.toml" ] || [ -f "$PROFILE_PATH/config.local.toml" ]; then
  tmp_config="$(mktemp)"
  if "$render_script" --profile-path "$PROFILE_PATH" --output "$tmp_config"; then
    if [ -L "$config_target" ]; then
      printf "%s\n" "   ⚠️  $config_target is still a symlink. Run: mise run link --prof \"$PROFILE\""
    elif [ -f "$config_target" ]; then
      if "$render_script" --profile-path "$PROFILE_PATH" --same-as "$config_target"; then
        printf "%s\n" "   ✅ $config_target matches rendered profile config"
      else
        printf "%s\n" "   ⚠️  $config_target differs from rendered profile config"
        printf "\\033[36m%s\\033[0m\n" "         import runtime changes: mise run pull_config --prof \"$PROFILE\""
        printf "\\033[36m%s\\033[0m\n" "         re-render profile config: mise run link --prof \"$PROFILE\""
      fi
    else
      printf "\\033[33m%s\\033[0m\n" "   ❌ $config_target does not exist. Run: mise run link --prof \"$PROFILE\""
    fi
  else
    printf "\\033[31m%s\\033[0m\n" "   ❌ Failed to render profile config"
  fi
  rm -f "$tmp_config"
else
  printf "%s\n" "   ⚠️  No config sources in profile; existing $config_target is left untouched"
fi

printf "\n🔗 Symlinks in\\033[36m %s/.codex:\\033[0m\n" "$HOME"
# NOTE: prompts/ は APM 管理 (~/.codex/prompts/ は real dir) に移行済のためチェック対象外。
for file in "${profile_targets[@]}"; do
  target="${HOME}/.codex/$file"
  source="$PROFILE_PATH/$file"

  if [ ! -f "$source" ] && [ ! -d "$source" ]; then
    if [ -e "$target" ]; then
      printf "%s\n" "   ⚠️  $source (missing); existing $target is left untouched"
    else
      printf "\\033[33m%s\\033[0m\n" "   ❌ $target does not exist"
    fi
    continue
  fi

  if [ -L "$target" ]; then
    link_target="$(readlink "$target")"
    source_real="$(realpath "$source")"
    target_real="$(realpath "$target")"
    if [ "$target_real" = "$source_real" ]; then
      printf "%s\n" "   ✅ $source -> $link_target"
    else
      printf "%s\n" "   ⚠️  $source -> $link_target (不一致)"
    fi
  elif [ -f "$target" ] && [ -f "$source" ]; then
    if cmp -s "$source" "$target"; then
      printf "%s\n" "   ✅ $source -> $target (regular file copy matches)"
    else
      printf "%s\n" "   ❌ $file (通常ファイル、profile と内容不一致). Use the following command ↓"
      printf "\\033[36m%s\\033[0m\n" "         code '$source' '$target'"
    fi
  elif [ -d "$target" ] && [ -d "$source" ]; then
    if diff -qr "$source" "$target" >/dev/null 2>&1; then
      printf "%s\n" "   ✅ $source -> $target (regular directory copy matches)"
    else
      printf "%s\n" "   ❌ $file (通常ディレクトリ、profile と内容不一致). Use the following command ↓"
      printf "\\033[36m%s\\033[0m\n" "         code '$source' '$target'"
    fi
  else
    printf "\\033[33m%s\\033[0m\n" "   ❌ $target does not exist"
  fi
done

printf "\n🧩 APM-managed skills in\\033[36m %s/.codex/skills:\\033[0m\n" "$HOME"
# NOTE: APM 移行後は ~/.codex/skills/ は APM が real dir として書き込む。
#   profile から symlink するのは廃止 (旧コード残骸は本ファイル過去 commit を参照)。
#   詳細は dotfiles/agents/ 配下と migration-plan.md を参照。
if [ -d "${HOME}/.codex/skills" ]; then
  skill_count="$(find "${HOME}/.codex/skills" -mindepth 2 -name SKILL.md 2>/dev/null | wc -l | tr -d ' ')"
  printf "%s\n" "   ✅ $skill_count skill(s) deployed (managed by 'apm install -g')"
  printf "\\033[36m%s\\033[0m\n" "         詳細: cd ~/dotfiles/agents && mise run status"
else
  printf "\\033[33m%s\\033[0m\n" "   ❌ ${HOME}/.codex/skills does not exist. Run: cd ~/dotfiles/agents && mise run install"
fi

printf "\n%s\n" "💡 Commands:"
printf "%s\n" "   反映/更新: mise run link --prof \"$PROFILE\""
printf "%s\n" "   Codexが書いたconfigを取り込み: mise run pull_config --prof \"$PROFILE\""
printf "%s\n" "   プロファイル変更: mise run switch [--prof <profile-name>]"
printf "%s\n" "   APM-managed skills: cd ~/dotfiles/agents && mise run status"
