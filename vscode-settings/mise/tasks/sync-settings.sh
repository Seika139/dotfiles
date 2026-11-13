#!/usr/bin/env bash

#MISE description="VS Code と Cursor の設定を同期する (settings.json は 3 層合成、他はシンボリックリンク)"
#MISE depends=["ensure_local_env"]
#MISE hide=true
#USAGE flag "--prof <prof>" {
#USAGE   help "プロファイル名"
#USAGE }
#USAGE flag "--force" {
#USAGE   help "既存の settings.json が合成結果と意味的に異なっていても、バックアップを残して上書きする"
#USAGE }

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

resolve_profile
FORCE="${usage_force:-}"
CONFLICT=0

require_profile_dir || exit 1
resolve_python
load_config_files

RENDERED="$(mktemp)"
trap 'rm -f "$RENDERED"' EXIT
"$PY" "$SETTINGS_PY" render --profile "$PROFILE" --output "$RENDERED" || exit 1

for editor in "${EDITORS[@]}"; do
  editor_path="$(editor_path_for "$editor")"
  # 空・相対パスだと意図しない場所 (cwd) に書き込むためスキップする
  rc=0
  check_editor_path "$editor_path" || rc=$?
  if [ "$rc" = "2" ]; then
    printf "\n⚠️  エディタのパスに空の要素があるためスキップします (ユーザー名が空?): \033[36m'%s'\033[0m\n" "$editor_path"
    CONFLICT=1
    continue
  elif [ "$rc" != "0" ]; then
    printf "\n⚠️  エディタのパスが空または相対パスのためスキップします: \033[36m'%s'\033[0m\n" "$editor_path"
    continue
  fi
  printf "\n設定適用先:\033[36m %s\033[0m\n" "${editor_path// /\\ }"
  if [ ! -d "$editor_path" ]; then
    mkdir -p "$editor_path"
  fi

  for item in "${CONFIG_FILE_LIST[@]}"; do
    src_item=$(realpath "$PROFILE_DIR/$item" 2>/dev/null || echo "")
    dest_item="$editor_path/$item"
    if [ "$item" = "settings.json" ]; then
      # 3 層合成した結果を実ファイルとして書く (symlink にするとプロファイルを上書きしてしまう)
      if [ -L "$dest_item" ]; then
        rm -f "$dest_item"
      fi
      if [ -e "$dest_item" ] && ! cmp -s "$RENDERED" "$dest_item" \
        && ! "$PY" "$SETTINGS_PY" diff --profile "$PROFILE" --target "$dest_item" >/dev/null; then
        if [ "$FORCE" = "true" ]; then
          backup="$dest_item.bak-$(date +%Y%m%d%H%M%S)"
          cp -p "$dest_item" "$backup"
          printf "  💾 バックアップを作成: \033[36m%s\033[0m\n" "$backup"
        else
          printf "  ❌ 既存の settings.json が合成結果と異なるため上書きしません: \033[36m%s\033[0m\n" "$dest_item"
          printf "     \033[36mmise run settings-diff\033[0m で差分を確認してください\n"
          printf "     旧方式の残骸 (symlink のコピー) などで不要なら \033[36mmise run sync -- --force\033[0m で上書きできます (バックアップを残します)\n"
          CONFLICT=1
          continue
        fi
      fi
      # 同じディレクトリの一時ファイルから mv して atomic に置き換える
      tmp_item="$(mktemp "$dest_item.tmp.XXXXXX")" || tmp_item=""
      if cp "$RENDERED" "$tmp_item" && mv -f "$tmp_item" "$dest_item"; then
        printf "  ✅ 合成して書き込み完了: \033[36m%s\033[0m\n" "$dest_item"
      else
        rm -f "$tmp_item"
        printf "  ❌ 書き込みに失敗しました: \033[36m%s\033[0m\n" "$dest_item"
        CONFLICT=1
      fi
    elif [ -z "$src_item" ] || [ ! -e "$src_item" ]; then
      printf "  ⚠️  スキップ: \033[36m%s\033[0m が見つかりません\n" "$PROFILE_DIR/$item"
    elif [ -e "$dest_item" ] && ! [ -L "$dest_item" ]; then
      printf "  既存のファイル/ディレクトリを発見: \033[36m%s\033[0m (シンボリックリンクでない)\n" "$dest_item"
      if diff -r -q "$src_item" "$dest_item" >/dev/null 2>&1; then
        printf "  ✅ 内容が同一です。シンボリックリンクに置き換えます: \033[36m%s\033[0m\n" "$PROFILE_DIR/$item"
        rm -rf "$dest_item"
        ln -snf "$src_item" "$dest_item"
      else
        printf "  ❌ 競合: 手動で解決してから再実行してください\n"
        printf "     プロファイル: \033[36m%s\033[0m != 既存: \033[36m%s\033[0m\n" "$PROFILE_DIR/$item" "$dest_item"
        CONFLICT=1
      fi
    else
      if ln -snf "$src_item" "$dest_item"; then
        printf "  ✅ リンク完了: \033[36m%s\033[0m\n" "$PROFILE_DIR/$item"
      else
        printf "  ❌ リンク失敗: \033[36m%s\033[0m\n" "$dest_item"
        CONFLICT=1
      fi
    fi
  done
done
if [ "$CONFLICT" != "0" ]; then
  printf "\n❌ 一部の設定ファイルを同期できませんでした。上のメッセージを確認してください。\n"
  exit 1
fi
printf "\n✅ 設定ファイルの同期が完了しました！\n"
