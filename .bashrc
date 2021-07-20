#!/usr/bin/env bash

cat <<EOS
       )
    ／⌒⌒⌒ヽ                     ／⌒⌒⌒ヽ
   ﾉ ﾉﾉLL人ﾊ     きょう も     ((ﾉﾉ从从⭐️
  (_Cﾘﾟ‐ﾟﾉﾘ)     いちにち      ﾉ从ﾟヮﾟ人
  ﾉﾉ⊂)卯(つヽ    がんばろう   （(⊂ｿ辷ｿつ)
（( くzzzz> ))                  くzzzz>
     し∪                          し∪
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

.bashrc has been Read
type "hlp" if you want some help

EOS

# 上で使ってる太線は http://bubuzuke.s7.xrea.com/ISO10646/ruled.html で手に入れた

# lessのオプション設定 SEE : https://qiita.com/delphinus/items/b04752bb5b64e6cc4ea9
export LESS="-g -i -M -R -S -W"

# lsにデフォで色をつける
alias ls='ls -GF'
alias ll="ls -al"

#-------------------------------------
# 0. DOTFILES_ROOT
#-------------------------------------
# dotfilesのディレクトリを探す。
# このファイルがシンボリックリンクの場合は実体を参照する。
# Mac の readlink には -f オプション(再帰的な探索)がないため、
# 複数を経由したリンクだとうまく行かない。
#
# BASH_SOURCEは「呼び出されたファイル自身の絶対パス」でbashでしか使えない
# SEE: https://qiita.com/yudoufu/items/48cb6fb71e5b498b2532

if [ -L $BASH_SOURCE ]; then
    DOTFILES_ROOT=$(dirname $(readlink $BASH_SOURCE))
else
    DOTFILES_ROOT=$(dirname $BASH_SOURCE)
fi

#----------------------------------------------------------
# 1. 自分用のチートシートをまとめたファイルを見るためのコマンド集
#----------------------------------------------------------

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
    cat_file $1 | less -R
}

# 自作helpのトップ
function hlp() {
    less ${DOTFILES_ROOT}/docs/home.txt
}

function hlp_alias() {
    less ${DOTFILES_ROOT}/docs/linux/alias.txt
}

function hlp_curl() {
    open https://github.com/Seika139/library/blob/master/curl/index.md
}

function hlp_cursor() {
    less ${DOTFILES_ROOT}/docs/linux/cursor.txt
}

function hlp_find() {
    less ${DOTFILES_ROOT}/docs/linux/find.txt
}

function hlp_history() {
    less ${DOTFILES_ROOT}/docs/linux/history.txt
}

function hlp_less() {
    less ${DOTFILES_ROOT}/docs/linux/less.txt
}

function hlp_wc() {
    less ${DOTFILES_ROOT}/docs/linux/wc.txt
}

#----------------------------------------------------------
# TODO
# コマンド履歴 p214
# ワイルドカード p39
#----------------------------------------------------------

#----------------------------------------------------------
# 2. direnv
#----------------------------------------------------------

eval "$(direnv hook bash)"

# gitignore.io のコマンド
function gi() {
    curl -sL https://www.toptal.com/developers/gitignore/api/$@
    echo
}

#----------------------------------------------------------
# 3. git関連のエイリアス
#----------------------------------------------------------

alias g="git"
# gだけの時でも補完が効くようにする
# TODO completeについてはまだわかって無いことが多い
complete -o bashdefault -o default -o nospace -F __git_wrap__git_main g

# git branch
alias gb='git branch'
# リモートも表示する
alias gba='git branch -a'
# git status --short --branch の略。省略表記しつつブランチ名も確認できる
alias gs='git status -sb'
# git add
alias ga='git add'
# git commit
alias gc='git commit'
# git log … シンプル表示・10件のみ表示
alias gl='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Cyan)%cd %C(Reset)%s %C(Blue)[%cn]%C(Red)%d" -10'
# git log … グラフ表示
alias glr='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Cyan)%cd %C(Reset)%s %C(Blue)[%cn]%C(Red)%d" --graph'
# git log … 修正ライン数が分かる
alias gll='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Cyan)%cd %C(Reset)%s %C(Blue)[%cn]%C(Red)%d" --numstat'

alias gd='git diff'

alias gr='git remote'
alias grp='git remote prune origin'

alias gsl='git stash list'

# 新しく作ったブランチをプッシュするのがめんどい時のコマンド
function gp_set() {
    branch_name=$(git symbolic-ref --short HEAD)
    git push --set-upstream origin $branch_name
    unset branch_name
}

function hlp_git() {
    less_color ${DOTFILES_ROOT}/docs/git.txt
}

#----------------------------------------------------------
# 4. history関連
#----------------------------------------------------------
# SEE : https://takuya-1st.hatenablog.jp/entry/20090828/1251474360
# SEE : https://qiita.com/bezeklik/items/56a597acc2eb568860d7

export HISTCONTROL=ignoreboth
# ignorespace(空白文字で始まる行を保存しない) と ignoredups(ひとつ前の履歴エントリと一致する行を保存しない) の両方
export HISTSIZE=5000                                        # historyの履歴を増やす
export HISTTIMEFORMAT='%F %T '                              # 日時を前に追加
export HISTIGNORE='history:pwd:cd *:ls:ll:w:top:df *:hlp_*' # 保存しないコマンド
