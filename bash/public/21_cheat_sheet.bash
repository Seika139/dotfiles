#!/usr/bin/env bash

# 自分用のチートシートをまとめたファイルを見るためのコマンド集

# ファイルが存在する場合はその中身を出力する
function cat_file() {
  if [ -f "$1" ]; then
    while IFS= read -r line; do
      # echo はダブルクォートで囲わないと連続するスペースが1つになってしまう
      # See : https://maku77.github.io/linux/io/echo-spaces.html
      echo -e "$line"
    done <"$1"
  else
    echo "No file exists with name of $1"
  fi
}

# 文字に色をつけたファイルをlessで表示する
# 一旦 cat_fileを挟まないとうまく色がつかないのでこうしている
function less_color() {
  cat_file "$1" | less_lf
}

# ファイルを探して、選択したらそのパスを返す
function fp() {
  # --line-range :120 で行数が多いファイルは120行までしか読み込まないようにしている
  fd -u . | fzf \
    --preview '
      if [[ -f {} ]]; then
        bat --color=always --style=full --line-range :120 {}
      else
          eza --tree {}
      fi
  ' \
  --preview-window=right:50%
}

# fp で探したファイルを vscode で開く
function f() {
  local path
  path=$(fp)
  if [ -d "${path}" ]; then
    tree "${path}";
  elif  type code &>/dev/null; then
  code "${path}";
  fi
}

function hlp() {
  if type bat fd fzf &>/dev/null; then
    local target_dir="${DOTPATH}/docs/help/"
    local file

    # --with-nth を使うことで、内部では「フルパス」を保持しつつ、選択画面では「ファイル名だけ」を表示する
    # --delimiter / → 「/」で区切る
    # --with-nth -1 → 最後から1番目
    file=$(fd --type f . "$target_dir" | fzf \
      --with-nth -1 --delimiter / \
      --preview "bat --color=always --style=full --line-range :120 {}" \
      --preview-window=right:75%)

    # ファイルが選択されたら bat で開く
    if [ -n "$file" ]; then
      bat "$file"
    fi
  else
    printf "%s\n" "この機能を使うには bat, fzf, fd コマンドを導入する必要があります"
  fi
}

function hlp_curl() {
  open https://github.com/Seika139/library/blob/master/curl/index.md
}

#----------------------------------------------------------
# TODO
# コマンド履歴 p214
# ワイルドカード p39
#----------------------------------------------------------

hlp_find_large_dir() {
  if command -v bat >/dev/null 2>&1; then
    bat "${DOTPATH}/docs/linux/find_large_directory.md"
  else
    less "${DOTPATH}/docs/linux/find_large_directory.md"
  fi
}
