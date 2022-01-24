#!/usr/bin/env bash

# lessのオプション設定 SEE : https://qiita.com/delphinus/items/b04752bb5b64e6cc4ea9
export LESS="-g -i -M -R -S -W"

function less_m() {
    # windows で ^M がたくさん表示される時につかう
    sed s/^M//g $1 | less $LESS
}

# lsにデフォで色をつける
alias ls='ls -GF'
alias ll="ls -al"
export LSCOLORS=cxfxgxdxbxegedabagacad
# [Terminal.appでlsのファイル色を変える - by edvakf in hatena](https://edvakf.hatenadiary.org/entry/20080413/1208042916)
# [Terminalで「ls」したら「ls -G」が実行されるようにして、色も設定する。 - taoru's memo](https://taoru.hateblo.jp/entry/20120418/1334713778)
