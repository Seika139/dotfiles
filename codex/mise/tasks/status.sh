#!/usr/bin/env bash

#MISE description="現在のプロファイル設定と~/.codexの状態を確認"
#MISE depends=["check_env", "dot-format"]
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
printf "os()               = "
print_cyan "$(codex_os_name)"$'\n'
printf "IS_WSL             = "
print_cyan "${IS_WSL:-false}"$'\n'
printf "config_root        = "
print_cyan "$ROOT_DIR"$'\n'
printf "Selected profile   = "
print_cyan "$PROFILE"$'\n'

if [ ! -d "$PROFILE_PATH" ]; then
  print_red "❌ Profile directory does not exist: $PROFILE_PATH"$'\n'
  exit 1
fi

echo ""
AGENTS_PATH="${ROOT_DIR}/agents"
AGENT_TARGET="${HOME}/.codex/agents"
printf "%s\n" "🤖 Agents:"
printf "%s" "  Native agents source: "
print_dim "$AGENTS_PATH"$'\n'
printf "%s" "  Native agents target: "
print_dim "$AGENT_TARGET"$'\n'
printf "%s\n" "  Native agents deployment: regular files (manifest-managed)"
PYTHON="$(codex_python)"
if "$PYTHON" "${ROOT_DIR}/mise/scripts/validate_agents.py" "$AGENTS_PATH" >/dev/null; then
  printf "%s\n" "   ✅ native agent definitions are valid"
else
  print_red "   ❌ native agent definitions are invalid"$'\n'
fi
if [ -L "$AGENT_TARGET" ]; then
  printf "%s\n" "   ❌ $AGENT_TARGET (symlink drift; mise run link --prof \"$PROFILE\")"
elif [ -d "$AGENT_TARGET" ]; then
  for source in "$AGENTS_PATH"/*.toml; do
    [ -f "$source" ] || continue
    name="$(basename "$source")"
    target="$AGENT_TARGET/$name"
    manifest="${HOME}/.codex/.codex-dotfiles-native-agents.manifest"
    managed=false
    if [ -f "$manifest" ] && tr -d '\r' <"$manifest" | grep -Fqx -- "$name"; then
      managed=true
    fi
    if [ "$managed" = true ] && [ -f "$target" ] && [ ! -L "$target" ] && cmp -s "$source" "$target"; then
      printf "%s" "    - "
      print_dim "$target"
      printf "%s\n" " (managed regular file matches)"
    elif [ "$managed" = true ] && { [ -e "$target" ] || [ -L "$target" ]; }; then
      printf "%s" "    ❌ "
      print_dim "$target"
      print_red " (managed drift; mise run link --prof \"$PROFILE\")"$'\n'
    elif [ -e "$target" ] || [ -L "$target" ]; then
      printf "%s" "    ⚠️  "
      print_dim "$target"
      printf "%s\n" " (unmanaged collision)"
    else
      printf "%s" "    ❌ "
      print_dim "$target"
      print_red " (missing; mise run link --prof \"$PROFILE\")"$'\n'
    fi
  done
else
  print_red "   ❌ $AGENT_TARGET does not exist; mise run link --prof \"$PROFILE\""$'\n'
fi

printf "\n📂 Original files and directories:\n"
# NOTE: prompts/ skills/ は APM 管理 (dotfiles/agents/) に移行済のためチェック対象外。
profile_targets=(AGENTS.md custom-config hooks.json)
for file in "${profile_targets[@]}"; do
  source="$PROFILE_PATH/$file"
  if [ -f "$source" ] || [ -d "$source" ]; then
    printf "   ✅ "
    print_dim "$source"$'\n'
  else
    print_red "   ❌ "
    print_dim "$source"
    print_red " (missing)"$'\n'
  fi
done

printf "\n⚙️  Config sources:\n"
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
    print_yellow "   ❌ $source (missing)"$'\n'
  fi
done

printf "\n⚙️  Runtime config in "
print_dim "$HOME/.codex:"$'\n'
config_target="${HOME}/.codex/config.toml"
render_script="${ROOT_DIR}/mise/scripts/render_config.py"
if [ -f "$PROFILE_PATH/config.base.toml" ] || [ -f "$PROFILE_PATH/config.toml" ] || [ -f "$PROFILE_PATH/config.local.toml" ]; then
  tmp_config="$(mktemp)"
  if "$render_script" --profile-path "$PROFILE_PATH" --output "$tmp_config"; then
    if [ -L "$config_target" ]; then
      printf "%s" "   ⚠️  "
      print_dim "$config_target"
      print_yellow " is still a symlink. Run: mise run link --prof \"$PROFILE\""$'\n'
    elif [ -f "$config_target" ]; then
      if "$render_script" --profile-path "$PROFILE_PATH" --same-as "$config_target"; then
        printf "%s\n" "   ✅ $config_target matches rendered profile config"
      else
        printf "%s" "   ⚠️  "
        print_dim "$config_target"
        print_yellow " differs from rendered profile config"$'\n'
        print_yellow "         import runtime changes: "
        print_cyan "mise run pull_config --prof \"$PROFILE\""$'\n'
        print_yellow "         re-render profile config: "
        print_cyan "mise run link --prof \"$PROFILE\""$'\n'
      fi
    else
      print_yellow "   ❌ $config_target does not exist. Run: mise run link --prof \"$PROFILE\""$'\n'
    fi
  else
    print_red "   ❌ Failed to render profile config"$'\n'
  fi
  rm -f "$tmp_config"
else
  printf "%s\n" "   ⚠️  No config sources in profile; existing $config_target is left untouched"
fi

printf "\n🔗 Profile files in "
print_dim "$HOME/.codex:"$'\n'
# NOTE: prompts/ は APM 管理 (~/.codex/prompts/ は real dir) に移行済のためチェック対象外。
for file in "${profile_targets[@]}"; do
  target="${HOME}/.codex/$file"
  source="$PROFILE_PATH/$file"

  if [ ! -f "$source" ] && [ ! -d "$source" ]; then
    if [ -e "$target" ]; then
      printf "%s\n" "   ⚠️  $source (missing); existing $target is left untouched"
    else
      print_yellow "   ❌ $target does not exist"$'\n'
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
    print_yellow "   ❌ $target does not exist"$'\n'
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
