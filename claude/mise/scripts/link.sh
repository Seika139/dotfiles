#!/bin/bash

#MISE description="指定プロファイルの設定を ~/.claude/ に同期する (settings.json はマージ書き出し / 他は symlink)"
#MISE depends=["check_env"]
#MISE shell="bash -c"
#MISE quiet=true

# ---------------------------------------------------------------------------
# 双方向同期モデル: dotfiles -> ~/.claude/ 方向の同期。
# 詳細は claude/docs/settings-sync.md を参照。
#
#   settings.json: dotfiles の settings.json + settings.local.json を jq で
#                  deep merge し、~/.claude/settings.json に実ファイルとして書き出す。
#                  CCWB の物理書き換えと共存するため symlink にしない。
#   settings.local.json: Claude Code が読まないため ~/.claude/ には配置しない。
#                        既存 symlink があれば削除する。
#   CLAUDE.md / commands / skills / rules / custom-config: 従来通り symlink。
# ---------------------------------------------------------------------------

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
CLAUDE_DIR="${HOME}/.claude"
mkdir -p "$CLAUDE_DIR"

printf "%s\n" "🦄 Linking Claude settings from profile: $PROFILE"

# ---------------------------------------------------------------------------
# settings.json: マージ書き出し方式
# ---------------------------------------------------------------------------
REPO_SETTINGS="$PROFILE_PATH/settings.json"
REPO_LOCAL="$PROFILE_PATH/settings.local.json"
SETTINGS_TARGET="$CLAUDE_DIR/settings.json"

if [ ! -f "$REPO_SETTINGS" ]; then
  printf "   ⚠️  Skipping missing file: \033[31m%s\033[0m\n" "$REPO_SETTINGS"
else
  # local が存在しなければ空オブジェクトとしてマージ
  if [ -f "$REPO_LOCAL" ] && [ -s "$REPO_LOCAL" ]; then
    LOCAL_INPUT="$REPO_LOCAL"
  else
    LOCAL_INPUT=<(echo '{}')
  fi

  MERGED=$(jq -s '.[0] * .[1]' "$REPO_SETTINGS" "$LOCAL_INPUT")

  # 既存ファイルがあり symlink でも実ファイルでもなければバックアップ
  if [ -L "$SETTINGS_TARGET" ]; then
    printf "%s\n" "   Removing existing symlink: $SETTINGS_TARGET"
    rm "$SETTINGS_TARGET"
  elif [ -f "$SETTINGS_TARGET" ]; then
    # 内容が一致していればスキップ、違えばバックアップ
    if diff -q <(echo "$MERGED" | jq --sort-keys .) <(jq --sort-keys . "$SETTINGS_TARGET") >/dev/null 2>&1; then
      printf "%s\n" "   ✅ $SETTINGS_TARGET (内容が一致、書き換え不要)"
    else
      backup="$SETTINGS_TARGET.backup.$(date +%Y%m%d_%H%M%S)"
      cp "$SETTINGS_TARGET" "$backup"
      printf "%s\n" "   💾 既存ファイルをバックアップ: $backup"
    fi
  fi

  # 書き出し (差分がない場合でも上書きはしない)
  if [ ! -f "$SETTINGS_TARGET" ] || ! diff -q <(echo "$MERGED" | jq --sort-keys .) <(jq --sort-keys . "$SETTINGS_TARGET") >/dev/null 2>&1; then
    echo "$MERGED" | jq --sort-keys . >"$SETTINGS_TARGET"
    printf "\033[36m   📝 Wrote: %s (merge)\033[0m\n" "$SETTINGS_TARGET"
  fi
fi

# ---------------------------------------------------------------------------
# settings.local.json: Claude Code が読まないため ~/.claude/ には配置しない
# 旧運用の symlink が残っていたら削除する
# ---------------------------------------------------------------------------
LOCAL_TARGET="$CLAUDE_DIR/settings.local.json"
if [ -L "$LOCAL_TARGET" ]; then
  printf "%s\n" "   🗑️  Removing legacy symlink: $LOCAL_TARGET (Claude Code does not read this path)"
  rm "$LOCAL_TARGET"
elif [ -f "$LOCAL_TARGET" ]; then
  backup="$LOCAL_TARGET.backup.$(date +%Y%m%d_%H%M%S)"
  printf "%s\n" "   💾 Moving stray file: $LOCAL_TARGET -> $backup"
  mv "$LOCAL_TARGET" "$backup"
fi

# ---------------------------------------------------------------------------
# その他: 従来通り symlink で配置
# ---------------------------------------------------------------------------
symlink_targets=(CLAUDE.md commands skills custom-config rules)

for file in "${symlink_targets[@]}"; do
  source="$PROFILE_PATH/$file"
  target="$CLAUDE_DIR/$file"

  if [ ! -e "$source" ]; then
    printf "   ⚠️  Skipping missing file: \033[31m%s\033[0m\n" "$source"
    continue
  fi

  # 既存リンク/ファイルの整理
  if [ -L "$target" ]; then
    rm "$target"
  elif [ -f "$target" ] || [ -d "$target" ]; then
    backup="$target.backup.$(date +%Y%m%d_%H%M%S)"
    printf "%s\n" "   💾 既存ファイル/ディレクトリをバックアップ: $target -> $backup"
    mv "$target" "$backup"
  fi

  printf "\033[36m  "
  ln -sfnv "$source" "$target"
  printf "\033[0m"
done

printf "%s\n" "✅ Linked Claude settings from profile '$PROFILE'"
