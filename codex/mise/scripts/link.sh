#!/bin/bash

#MISE description="指定プロファイルの設定ファイルをシンボリックリンクする"
#MISE depends=["check_env"]
#MISE shell="bash -c"
#MISE quiet=true

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

main_targets=(AGENTS.md prompts custom-config)
render_config="${MISE_CONFIG_ROOT}/mise/scripts/render_config.py"
sync_prompt_skills="${MISE_CONFIG_ROOT}/mise/scripts/sync_prompt_skills.py"

printf "%s\n" "🦄 Linking Codex settings from profile: $PROFILE"

if [ -d "$PROFILE_PATH/prompts" ] && [ -f "$sync_prompt_skills" ]; then
  python3 "$sync_prompt_skills" --profile-path "$PROFILE_PATH"
fi

config_target="${CODEX_HOME}/config.toml"
if [ -f "$PROFILE_PATH/config.base.toml" ] || [ -f "$PROFILE_PATH/config.toml" ] || [ -f "$PROFILE_PATH/config.local.toml" ]; then
  tmp_config="$(mktemp)"
  python3 "$render_config" --profile-path "$PROFILE_PATH" --output "$tmp_config"

  if [ -L "$config_target" ]; then
    printf "%s\n" "   Replacing config symlink with generated file: $config_target"
    rm "$config_target"
  elif [ -f "$config_target" ]; then
    if python3 "$render_config" --profile-path "$PROFILE_PATH" --same-as "$config_target"; then
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

skills_source="${PROFILE_PATH}/skills"
skills_target="${CODEX_HOME}/skills"
mkdir -p "$skills_target"

for target in "$skills_target"/* "$skills_target"/.[!.]* "$skills_target"/..?*; do
  [ -e "$target" ] || continue
  [ -L "$target" ] || continue
  link_target="$(readlink "$target")"
  case "$link_target" in
  "$MISE_CONFIG_ROOT"/"$PROFILES_DIR"/*/skills/*)
    printf "%s\n" "   Removing existing profile skill symlink: $target"
    rm "$target"
    ;;
  esac
done

if [ -d "$skills_source" ]; then
  for source in "$skills_source"/*; do
    [ -d "$source" ] || continue
    [ -f "$source/SKILL.md" ] || continue

    skill_name="$(basename "$source")"
    target="${skills_target}/${skill_name}"

    if [ -L "$target" ]; then
      printf "\\033[36m  "
      ln -sfnv "$source" "$target"
      printf "\\033[0m"
    elif [ -e "$target" ]; then
      printf "   ⚠️  Skipping skill because target already exists: \\033[31m%s\\033[0m\n" "$target"
    else
      printf "\\033[36m  "
      ln -sfnv "$source" "$target"
      printf "\\033[0m"
    fi
  done
else
  printf "   ⚠️  Skipping missing skills directory: \\033[31m%s\\033[0m\n" "$skills_source"
fi

printf "%s\n" "✅ Linked Codex settings from profile '$PROFILE'"
