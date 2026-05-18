#!/bin/bash

#MISE description="現在のプロファイル設定と ~/.claude/ の状態を確認する"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="profile name (defaults to DEFAULT_CLAUDE_PROFILE / WSL_CLAUDE_PROFILE)"

# ---------------------------------------------------------------------------
# settings.json は実ファイル運用 (claude/docs/settings-sync.md 参照)
# ~/.claude/settings.json と dotfiles の settings.json + settings.local.json
# のマージ結果を比較し、ドリフトの内容と方向性を表示する。
# ---------------------------------------------------------------------------

set -eu

if [ "${MISE_CONFIG_ROOT:-}" = "" ]; then
  MISE_CONFIG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi

# mise の {{ os() }} に近い語彙 (macos / linux / windows) を bash で算出する
detect_os() {
  case "$(uname -s)" in
  Darwin) echo "macos" ;;
  Linux) echo "linux" ;;
  MINGW* | MSYS* | CYGWIN*) echo "windows" ;;
  *) echo "unknown" ;;
  esac
}

# ---------------------------------------------------------------------------
# プロファイル解決
# ---------------------------------------------------------------------------
if [ "${IS_WSL:-false}" = "true" ]; then
  DEFAULT_PROFILE="${WSL_CLAUDE_PROFILE:-}"
else
  DEFAULT_PROFILE="${DEFAULT_CLAUDE_PROFILE:-}"
fi

# 引数解析 (link.sh / recover-settings.sh と同じパターン)
option_profile=""
while [ $# -gt 0 ]; do
  case "$1" in
  --prof)
    option_profile="$2"
    shift 2
    ;;
  *)
    shift
    ;;
  esac
done

# usage_prof は mise が #MISE usage から渡す環境変数
PROFILE="${option_profile:-${usage_prof:-}}"
PROFILE="${PROFILE:-$DEFAULT_PROFILE}"

PROFILE_PATH="${MISE_CONFIG_ROOT}/${PROFILES_DIR:-profiles}/$PROFILE"

# ---------------------------------------------------------------------------
# 環境チェック表示
# ---------------------------------------------------------------------------
printf "%s\n" "🦄 Environment Check"
printf "os()                 =\033[36m %s\033[0m\n" "$(detect_os)"
printf "IS_WSL               =\033[36m %s\033[0m\n" "${IS_WSL:-false}"
printf "config_root          =\033[36m %s\033[0m\n" "$MISE_CONFIG_ROOT"
printf "Selected profile     =\033[36m %s\033[0m\n" "$PROFILE"

if [ ! -d "$PROFILE_PATH" ]; then
  printf "❌ Profile directory does not exist:\033[36m %s\033[0m\n" "$PROFILE_PATH"
  exit 1
fi

# ---------------------------------------------------------------------------
# プロファイル下のファイル/ディレクトリ存在確認
# ---------------------------------------------------------------------------
printf "\n📂 Original files and directories:\n"
for file in settings.json settings.local.json CLAUDE.md commands skills custom-config rules; do
  source="$PROFILE_PATH/$file"
  if [ -f "$source" ] || [ -d "$source" ]; then
    printf "%s\n" "   ✅ $source"
  else
    printf "\033[31m%s\033[0m\n" "   ❌ $source (missing)"
  fi
done

# ---------------------------------------------------------------------------
# settings.json の同期状態 (実ファイル + マージ比較)
# ---------------------------------------------------------------------------
printf "\n📄 ~/.claude/settings.json (実ファイル運用):\n"
SETTINGS_TARGET="${HOME}/.claude/settings.json"
REPO_SETTINGS="$PROFILE_PATH/settings.json"
REPO_LOCAL="$PROFILE_PATH/settings.local.json"

if [ -L "$SETTINGS_TARGET" ]; then
  printf "\033[33m%s\033[0m\n" "   ⚠️  symlink になっています (新方針では実ファイル運用)。mise run link で修正してください。"
elif [ ! -f "$SETTINGS_TARGET" ]; then
  printf "\033[33m%s\033[0m\n" "   ❌ $SETTINGS_TARGET が存在しません。mise run link を実行してください。"
elif [ ! -f "$REPO_SETTINGS" ]; then
  printf "\033[31m%s\033[0m\n" "   ❌ $REPO_SETTINGS が存在しません。"
else
  # local が存在しなければ空 JSON 一時ファイルを使う (プロセス置換は変数経由で FD が閉じる罠があるため)
  if [ -f "$REPO_LOCAL" ] && [ -s "$REPO_LOCAL" ]; then
    LOCAL_INPUT="$REPO_LOCAL"
    CLEANUP_LOCAL_INPUT=""
  else
    LOCAL_INPUT="$(mktemp -t claude-status-local.XXXXXX)"
    printf '{}' >"$LOCAL_INPUT"
    CLEANUP_LOCAL_INPUT="$LOCAL_INPUT"
    trap 'rm -f "$CLEANUP_LOCAL_INPUT"' EXIT
  fi
  ACTUAL=$(jq --sort-keys . "$SETTINGS_TARGET")
  EXPECTED=$(jq -s --sort-keys '.[0] * .[1]' "$REPO_SETTINGS" "$LOCAL_INPUT")
  if [ "$ACTUAL" = "$EXPECTED" ]; then
    printf "%s\n" "   ✅ $SETTINGS_TARGET"
    printf "      (dotfiles 側の settings.json + settings.local.json のマージ結果と一致)\n"
  else
    printf "\033[33m%s\033[0m\n" "   ⚠️  $SETTINGS_TARGET (dotfiles と不一致)"
    printf "      凡例: \033[31m< 行頭\033[0m = ~/.claude/settings.json のみ、\033[32m> 行頭\033[0m = dotfiles マージ結果のみ\n"
    printf "      \033[2m──────────────────────────────────────────────\033[0m\n"
    diff --color=always <(echo "$ACTUAL") <(echo "$EXPECTED") | sed 's/^/      /' || true
    printf "      \033[2m──────────────────────────────────────────────\033[0m\n"
    # キー単位の差分を取り、純粋な追加・削除・値変更を区別してヒントを出し分ける
    actual_keys=$(jq -r '[paths(scalars)] | map(join(".")) | .[]' <(echo "$ACTUAL") | sort -u)
    expected_keys=$(jq -r '[paths(scalars)] | map(join(".")) | .[]' <(echo "$EXPECTED") | sort -u)
    only_in_actual=$(comm -23 <(echo "$actual_keys") <(echo "$expected_keys") | wc -l | tr -d ' ')
    only_in_expected=$(comm -13 <(echo "$actual_keys") <(echo "$expected_keys") | wc -l | tr -d ' ')
    printf "      \033[2m差分サマリ: ~/.claude/ のみのキー = %s 個、dotfiles のみのキー = %s 個\033[0m\n" "$only_in_actual" "$only_in_expected"
    if [ "$only_in_actual" -gt 0 ] && [ "$only_in_expected" -eq 0 ]; then
      printf "      \033[36m→ ~/.claude/ 側に新規キーあり (CCWB 等の外部書き換え)。mise run recover --prof \"$PROFILE\" で取り込み。\033[0m\n"
    elif [ "$only_in_actual" -eq 0 ] && [ "$only_in_expected" -gt 0 ]; then
      printf "      \033[36m→ dotfiles 側に新規キーあり (編集後 link 未実行)。mise run link --prof \"$PROFILE\" で反映。\033[0m\n"
    elif [ "$only_in_actual" -eq 0 ] && [ "$only_in_expected" -eq 0 ]; then
      printf "      \033[36m→ キー集合は同じだが値が異なる。どちらを正とするか判断後、recover (~/.claude/ を正) または link (dotfiles を正) を実行。\033[0m\n"
      printf "      \033[2m  外部値を取り込む: mise run recover --prof \"$PROFILE\"\033[0m\n"
      printf "      \033[2m  dotfiles の値で上書き: mise run link --prof \"$PROFILE\"\033[0m\n"
    else
      printf "      \033[33m→ 双方向に新規キーあり。recover/link を実行する前に変更内容を慎重に確認してください。\033[0m\n"
      printf "      \033[2m  外部変更を取り込む: mise run recover --prof \"$PROFILE\"\033[0m\n"
      printf "      \033[2m  dotfiles の変更を反映: mise run link --prof \"$PROFILE\"\033[0m\n"
    fi
  fi
fi

# ~/.claude/settings.local.json は Claude Code が読まないため使わない
# 旧運用の symlink/ファイルが残っていたら警告
if [ -L "${HOME}/.claude/settings.local.json" ] || [ -f "${HOME}/.claude/settings.local.json" ]; then
  printf "\033[33m%s\033[0m\n" "   ⚠️  ~/.claude/settings.local.json が残存しています (Claude Code は読まないパス)。mise run link で削除されます。"
fi

# ---------------------------------------------------------------------------
# その他は symlink で同期されているはず
# ---------------------------------------------------------------------------
printf "\n🔗 Symlinks in\033[36m %s/.claude:\033[0m\n" "$HOME"
for file in CLAUDE.md commands skills custom-config rules; do
  target="${HOME}/.claude/$file"
  source="$PROFILE_PATH/$file"

  if [ -L "$target" ]; then
    link_target=$(readlink "$target")
    # パスの正規化とマッチング (Windows / WSL 対応)
    if [ "$link_target" = "$source" ] || [[ "$link_target" == */"${source##*/}" ]] || [[ "$link_target" == *"\\${source##*/}" ]]; then
      printf "%s\n" "   ✅ $source -> $link_target"
    else
      printf "%s\n" "   ⚠️  $source -> $link_target (不一致)"
    fi
  elif [ -f "$target" ] || [ -d "$target" ]; then
    printf "%s\n" "   ❌ $file (通常ファイル/ディレクトリ、シンボリックリンクではない). Use the following command ↓"
    printf "\033[36m%s\033[0m\n" "         mise run link --prof \"$PROFILE\""
  else
    printf "\033[33m%s\033[0m\n" "   ❌ $target does not exist"
  fi
done

printf "\n💡 Commands:\n"
printf "   リンク作成/更新: mise run link --prof \"%s\"\n" "$PROFILE"
printf "   プロファイル変更: mise run switch [--prof <profile-name>]\n"
