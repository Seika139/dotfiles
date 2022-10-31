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
GL='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Magenta)%cd %C(Reset)%s %C(Cyan)[%cn]%C(Red)%d" -10'
alias gl="echo_yellow ${GL}; ${GL}"
unset GL

# git log … グラフ表示
GLR='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Magenta)%cd %C(Reset)%s %C(Cyan)[%cn]%C(Red)%d" --graph'
alias glr="echo_yellow ${GLR}; ${GLR}"
unset GLR

# git log … 修正ライン数が分かる
GLL='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Magenta)%cd %C(Reset)%s %C(Cyan)[%cn]%C(Red)%d" --numstat'
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

function tags_from_commit() {
    # git のコミットに対応するタグ・ブランチを取得する
    local tags=$(git branch -a --points-at=$1)
    echo $(echo ${tags//'*'/} | sed -e 's/->//' -e 's/ +/ /')
}

function commit_with_tags() {
    local tags=$(tags_from_commit $1)
    echo_yellow -n "$1"
    if [[ -n "${tags}" ]]; then
        echo_red -n " (${tags})"
    fi
}

function gcl() {

    if [[ $1 == '--help' ]]; then
        less <<EOS
usage: gcl commit1 commit2 [option] [path]

commit1 & commit2 : Commit object. Not only hash but also branch name and tags are supported.
option (optional) : Options for 'git log' are acceptable, such as --stat, --numstat
path   (optional) : Same usage as 'git log -p'
EOS
        return 0
    fi

    # $1 と $2 の共通祖先のコミットである $ancestor を探し
    # $1 と $ancestor、および $2 と $ancestor の差分を表示する
    # $3 以降の引数で検索する差分の範囲を絞り込むことができる

    if [[ $# -lt 2 ]]; then
        echo_yellow 'このエイリアスは最低2つの引数を必要とします'
        echo_yellow "See : gcl --help"
        return 1
    fi

    # 引数が適切なコミットを指していない場合を弾く
    for arg in $1 $2; do
        if [[ $(git show $arg | wc -l) -eq 0 ]]; then
            echo
            echo_red -n '不適切なコミット '
            echo_yellow "$arg"
            return 1
        fi
    done

    # 2つのコミットの共通祖先
    local ancestor=$(git merge-base $1 $2)

    # $1 と $2 の コミットハッシュ
    local commit_id_a=$(git rev-parse $1)
    local commit_id_b=$(git rev-parse $2)

    if [[ ${ancestor} == ${commit_id_a} ]]; then
        local descendant=$commit_id_b
    fi
    if [[ ${ancestor} == ${commit_id_b} ]]; then
        local descendant=$commit_id_a
    fi

    if [[ ${ancestor} == ${descendant} ]]; then
        # 2つが同じコミットを指していた場合
        echo -n $(commit_with_tags $ancestor)
        echo_cyan ' [SAME COMMIT]'
        return 0
    fi

    echo
    if [[ -n ${descendant} ]]; then
        # どちらかがもう一方の祖先だった場合
        echo -n $(commit_with_tags $ancestor)
        echo_rgb -n 120 120 120 ' ________ '
        echo $(commit_with_tags $descendant)
        echo
        echo_rgb 180 255 180 "git log --cc ${ancestor}..${descendant} ${@:3}"
        git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Magenta)%cd %C(Reset)%s %C(Cyan)[%cn]%C(Red)%d" --cc "${ancestor}".."${descendant}" "${@:3}"

    else
        # 両者のどちらとも同一でない祖先が存在する場合
        echo_rgb -n 180 180 100 "${ancestor}"
        echo_rgb -n 120 120 120 ' ________ '
        echo $(commit_with_tags $commit_id_a)
        echo_rgb -n 120 120 120 "                                          \______ "
        echo $(commit_with_tags $commit_id_b)

        # diff を表示するバージョン
        # echo_rgb 180 255 180 "git diff --histogram -w $1 $ancestor ${@:3}"
        # echo_rgb 180 255 180 "git diff --histogram -w $2 $ancestor ${@:3}"
        # git diff --histogram -w $1 $ancestor ${@:3}
        # git diff --histogram -w $2 $ancestor ${@:3}

        echo
        echo_rgb 180 255 180 "git log --cc ${ancestor}..${commit_id_a} ${@:3}"
        echo_rgb 180 255 180 "git log --cc ${ancestor}..${commit_id_b} ${@:3}"

        git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Magenta)%cd %C(Reset)%s %C(Cyan)[%cn]%C(Red)%d" --cc "${ancestor}".."${commit_id_a}" "${@:3}"
        git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Magenta)%cd %C(Reset)%s %C(Cyan)[%cn]%C(Red)%d" --cc "${ancestor}".."${commit_id_b}" "${@:3}"

    fi
}
