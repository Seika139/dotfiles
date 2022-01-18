#!/usr/bin/env bash

# プロンプトの色や表示内容の設定
# ref : https://qiita.com/hmmrjn/items/60d2a64c9e5bf7c0fe60
# ref : https://zenn.dev/kcabo/articles/555d9cc6dad0c3
# ref : https://qiita.com/zaburo/items/9194cd9eb841dea897a0
# ref : https://qiita.com/hf7777hi/items/7585c3aa5423a44eef35

# Windows の GitBash だと __git_ps1 のせいでプロンプトの表示が遅いので軽くする
# ref : https://neos21.net/blog/2018/12/31-01.html

function light__git_ps1() {
    local branch_name="$(git symbolic-ref --short HEAD 2>/dev/null)"
    if [ -z "$branch_name" ]; then
        # ブランチ名がなければ Git リポジトリ配下ではないと見なし、何も出力せず中断する
        exit 0
    fi
    echo "[$branch_name]" # 省略版と一目で分かるようにブラケットを使用
}

function lighten_ps1() {
    local USER='\[\e[40;92m\]\u@\h'
    local TIME='\[\e[95m\]\t'
    local DIR='\[\e[96m\]\w\[\e[49m\]'
    local GIT='\[\e[1;32m\]`light__git_ps1`'
    local LAST='\[\e[0m\]\n\$ '
    export PS1="${USER} ${TIME} ${DIR} ${GIT} ${LAST}"
}

function normalize_ps1() {
    local USER='\[\e[40;92m\]\u@\h'
    local TIME='\[\e[95m\]\t'
    local DIR='\[\e[96m\]\w\[\e[49m\]'
    if executable __git_ps1; then
        local GIT='\[\e[1;32m\]`__git_ps1 "(%s)"`'
        # MEMO : $(__git_ps1 "(%s)") とすると win の GitBash でエラーになった
    else
        local GIT=""
        warn "__git_ps1 がありません。git-prompt.shが読み込まれていないようです。"
    fi
    local LAST='\[\e[0m\]\n\$ '
    export PS1="${USER} ${TIME} ${DIR} ${GIT} ${LAST}"
}

# 環境に応じて使用するプロンプトを変える
if is_msys; then
    lighten_ps1
else
    normalize_ps1
fi
