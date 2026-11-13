#!/usr/bin/env bash

#MISE description="各種設定ファイルの同期状態を確認する"
#MISE depends=["ensure_local_env"]
#MISE hide=true
#USAGE flag "--prof <prof>" {
#USAGE   help "プロファイル名"
#USAGE }

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

resolve_profile
resolve_python
load_config_files

normalize_path() {
  local path="$1"
  # バックスラッシュをスラッシュに変換
  path="${path//\\//}"

  # Windows形式のドライブ文字 (C:) を POSIX形式 (/c) に変換
  if [[ "$path" =~ ^([A-Za-z]): ]]; then
    local drive="${BASH_REMATCH[1],,}" # 小文字化
    path="/$drive${path:2}"
  fi

  # 連続するスラッシュを単一に
  # shellcheck disable=SC2001
  path="$(echo "$path" | sed 's|//*|/|g')"

  # 末尾のスラッシュを削除（ルートディレクトリでない場合）
  if [[ "$path" != "/" ]]; then
    path="${path%/}"
  fi

  echo "$path"
}

PROFILE_DIR="$(normalize_path "${PROFILE_ROOT:-}")/$PROFILE"

for editor in "${EDITORS[@]}"; do
  editor_path="$(normalize_path "$(editor_path_for "$editor")")"
  printf "\nSettings for\033[36m %s\033[0m\n" "${editor_path/ /\\ /}"
  for item in "${CONFIG_FILE_LIST[@]}"; do
    expected_src="$PROFILE_DIR/$item"
    dest_file="$editor_path/$item"
    if [ "$item" = "settings.json" ]; then
      # 3 層合成した結果と意味的に比較する
      if [ -L "$dest_file" ]; then
        printf "  ⚠️  %s: symlink (旧方式)。mise run sync で実ファイルに置き換えます\n" "$item"
      elif [ ! -e "$dest_file" ]; then
        printf "  ❔ %s: Not exists\n" "$item"
      elif "$PY" "$SETTINGS_PY" diff --profile "$PROFILE" --target "$dest_file" >/dev/null; then
        printf "  ✅ %s: 合成結果と意味的に同一\n" "$item"
      else
        printf "  🚨 %s: 合成結果と異なります (mise run settings-diff で確認)\n" "$item"
      fi
    elif [ ! -e "$dest_file" ] && [ ! -L "$dest_file" ]; then
      printf "  ❔ %s: Not exists\n" "$item"
    elif [ -L "$dest_file" ]; then
      actual_src=$(readlink "$dest_file")
      if [ "$(normalize_path "$actual_src")" = "$(normalize_path "$expected_src")" ]; then
        printf "  ✅ %s <- %s\n" "$item" "$actual_src"
      else
        printf "  ❌ %s: Linked to a different source: %s\n" "$item" "$actual_src"
      fi
    else
      if [ -f "$dest_file" ] && [ -f "$expected_src" ]; then
        if diff -q "$dest_file" "$expected_src" >/dev/null; then
          printf "  ⚠️  %s: Same content but not a symlink\n" "$item"
        else
          printf "  🚨 %s: Different from profile\n" "$item"
        fi
      elif [ -d "$dest_file" ] && [ -d "$expected_src" ]; then
        if diff -r -q "$dest_file" "$expected_src" >/dev/null 2>&1; then
          printf "  ⚠️  %s: Same content but not a symlink\n" "$item"
        else
          printf "  🚨 %s: Different from profile\n" "$item"
        fi
      else
        printf "  🚨 %s: Not a symlink and cannot compare contents\n" "$item"
      fi
    fi
  done
done
