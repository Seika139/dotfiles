#!/usr/bin/env bash

# プロンプトの色や表示内容の設定
# ref : https://qiita.com/hmmrjn/items/60d2a64c9e5bf7c0fe60
# ref : https://zenn.dev/kcabo/articles/555d9cc6dad0c3
# ref : https://qiita.com/zaburo/items/9194cd9eb841dea897a0
# ref : https://qiita.com/hf7777hi/items/7585c3aa5423a44eef35

# TODO : windowsでも大丈夫か確認

USER='\[\e[40;92m\]\u@\h'
TIME='\[\e[95m\]\t'
DIR='\[\e[96m\]\w\[\e[49m\]'
GIT="\[\e[1;32m\]$(__git_ps1 '(%s)')"
LAST='\[\e[0m\]\n\$ '
export PS1="${USER} ${TIME} ${DIR} ${GIT} ${LAST}"
unset USER TIME DIR GIT LAST
