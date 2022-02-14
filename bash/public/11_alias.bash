#!/usr/bin/env bash

# lessのオプション設定 SEE : https://qiita.com/delphinus/items/b04752bb5b64e6cc4ea9
export LESS="-g -i -M -R -S -W"

function less_lf() {
    # Linux は改行コードが LF だが windows は改行コードが CR + LFのため
    # windows で less を実行すると ^M がたくさん表示されることがある
    # そのための対応策
    if is_win; then
        sed s/^M//g $1 | less $LESS
    else
        less $LESS $1
    fi
}

# lsにデフォで色をつける
alias ls='ls -GF'
alias ll="ls -al"
export LSCOLORS=cxfxgxdxbxegedabagacad
# [Terminal.appでlsのファイル色を変える - by edvakf in hatena](https://edvakf.hatenadiary.org/entry/20080413/1208042916)
# [Terminalで「ls」したら「ls -G」が実行されるようにして、色も設定する。 - taoru's memo](https://taoru.hateblo.jp/entry/20120418/1334713778)

# grepの検索条件に該当する部分にデフォルトで色を付ける。GREP_OPTIONS は非推奨になったのでエイリアスで対応した
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
