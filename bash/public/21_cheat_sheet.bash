#!/usr/bin/env bash

# 自分用のチートシートをまとめたファイルを見るためのコマンド集

# ファイルが存在する場合はその中身を出力する
function cat_file() {
    if [ -f $1 ]; then
        while IFS= read -r line; do
            # echo はダブルクォートで囲わないと連続するスペースが1つになってしまう
            # See : https://maku77.github.io/linux/io/echo-spaces.html
            echo -e "$line"
        done <$1
    else
        echo "No file exists with name of $1"
    fi
}

# 文字に色をつけたファイルをlessで表示する
# 一旦 cat_fileを挟まないとうまく色がつかないのでこうしている
function less_color() {
    cat_file $1 | less_lf
}

# 自作helpのトップ
function hlp() {
    less_lf ${DOTPATH}/docs/home.txt
}

function hlp_alias() {
    less_lf ${DOTPATH}/docs/linux/alias.txt
}

function hlp_curl() {
    open https://github.com/Seika139/library/blob/master/curl/index.md
}

function hlp_cursor() {
    less_lf ${DOTPATH}/docs/linux/cursor.txt
}

function hlp_find() {
    less_lf ${DOTPATH}/docs/linux/find.txt
}

function hlp_grep() {
    less_color ${DOTPATH}/docs/linux/grep.txt
}

function hlp_history() {
    less_lf ${DOTPATH}/docs/linux/history.txt
}

function hlp_less() {
    less_lf ${DOTPATH}/docs/linux/less.txt
}

function hlp_wc() {
    less_lf ${DOTPATH}/docs/linux/wc.txt
}

#----------------------------------------------------------
# TODO
# コマンド履歴 p214
# ワイルドカード p39
#----------------------------------------------------------
