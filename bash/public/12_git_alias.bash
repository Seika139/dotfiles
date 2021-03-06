#!/usr/bin/env bash

# gitignore.io のコマンド
function gi() {
    curl -sL https://www.toptal.com/developers/gitignore/api/$@
    echo
}

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
GL='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Cyan)%cd %C(Reset)%s %C(Blue)[%cn]%C(Red)%d" -10'
alias gl="echo_yellow ${GL}; ${GL}"
unset GL

# git log … グラフ表示
GLR='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Cyan)%cd %C(Reset)%s %C(Blue)[%cn]%C(Red)%d" --graph'
alias glr="echo_yellow ${GLR}; ${GLR}"
unset GLR

# git log … 修正ライン数が分かる
GLL='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Cyan)%cd %C(Reset)%s %C(Blue)[%cn]%C(Red)%d" --numstat'
alias gll="echo_yellow ${GLL}; ${GLL}"
unset GLL

alias gd='git diff'

alias gr='git remote'
alias grp='git remote prune origin'

alias gsl='git stash list'

# 新しく作ったブランチをプッシュするのがめんどい時のコマンド
function gpsu() {
    branch_name=$(git symbolic-ref --short HEAD)
    echo_yellow "Executing alias : git push --set-upstream origin ${branch_name}"
    git push --set-upstream origin $branch_name
    unset branch_name
}

# .gitmessageを表示する
function gmsg() {
    less_color ${DOTPATH}/.gitmessage
}

function hlp_git() {
    less_color ${DOTPATH}/docs/git.txt
}
