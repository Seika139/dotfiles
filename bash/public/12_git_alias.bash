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

function gcl() {
    # $1 と $2 の共通祖先のコミットである $ancestor を探し
    # $1 と $ancestor、および $2 と $ancestor の差分を表示する
    # $3 以降の引数で検索する差分の範囲を絞り込むことができる
    if [[ $# -lt 2 ]]; then
        echo_yellow 'このエイリアスは最低2つの引数を必要とします'
        return 1
    fi

    # 2つのコミットの共通祖先
    local ancestor=$(git merge-base $1 $2)

    # $1 と $2 の コミットid
    local commit_id_a=$(git rev-parse $1)
    local commit_id_b=$(git rev-parse $2)

    # $1 と $2 のに対応するブランチ・タグの一覧
    local tags_a=$(git branch --points-at=$commit_id_a)
    local tags_b=$(git branch --points-at=$commit_id_b)
    tags_a=$(echo ${tags_a//'*'/} | sed 's/ +/ /')
    tags_b=$(echo ${tags_b//'*'/} | sed 's/ +/ /')

    if [[ ${ancestor} == ${commit_id_a} ]]; then
        local descendant=$commit_id_b
    fi
    if [[ ${ancestor} == ${commit_id_b} ]]; then
        local descendant=$commit_id_a
    fi

    if [[ $ancestor == $descendant ]]; then
        # 2つが同じコミットを指していた場合
        local tags_ancestor=$(git branch --points-at=$ancestor)
        tags_ancestor=$(echo ${tags_ancestor//'*'/} | sed 's/ +/ /')

        echo_yellow -n "${ancestor}"
        if [[ -n "${tags_ancestor}" ]]; then
            echo_red -n " (${tags_ancestor})"
        fi

        echo_cyan ' [SAME COMMIT]'
        return 0
    fi

    echo
    if [[ -n ${descendant} ]]; then
        # どちらかがもう一方の祖先だった場合

        local tags_ancestor=$(git branch --points-at=$ancestor)
        tags_ancestor=$(echo ${tags_ancestor//'*'/} | sed 's/ +/ /')
        local tags_descendant=$(git branch --points-at=$descendant)
        tags_descendant=$(echo ${tags_descendant//'*'/} | sed 's/ +/ /')

        echo_yellow -n "${ancestor}"
        if [[ -n "${tags_ancestor}" ]]; then
            echo_red -n " (${tags_ancestor})"
        fi
        echo_rgb -n 120 120 120 ' ________ '
        echo_yellow -n $descendant
        if [[ -n "${tags_descendant}" ]]; then
            echo_red " (${tags_descendant})"
        else
            echo
        fi

        echo
        echo_rgb 180 255 180 "git log --cc ${ancestor}..${descendant} -p ${@:3}"
        git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Magenta)%cd %C(Reset)%s %C(Cyan)[%cn]%C(Red)%d" --cc "${ancestor}".."${descendant}" -p "${@:3}"

    else
        # 両者のどちらとも同一でない祖先が存在する場合
        echo_rgb -n 180 180 100 "${ancestor}"
        echo_rgb -n 120 120 120 ' ________ '
        echo_yellow $commit_id_a
        if [[ -n "${tags_a}" ]]; then
            echo_red " (${tags_a})"
        else
            echo
        fi
        echo_rgb -n 120 120 120 "                                          \______ "
        echo_yellow -n $commit_id_b
        if [[ -n "${tags_b}" ]]; then
            echo_red " (${tags_b})"
        else
            echo
        fi

        # diff を表示するバージョン
        # echo_rgb 180 255 180 "git diff --histogram -w $1 $ancestor -- ${@:3}"
        # echo_rgb 180 255 180 "git diff --histogram -w $2 $ancestor -- ${@:3}"
        # git diff --histogram -w $1 $ancestor -- ${@:3}
        # git diff --histogram -w $2 $ancestor -- ${@:3}

        echo
        echo_rgb 180 255 180 "git log --cc ${ancestor}..${commit_id_a} -p ${@:3}"
        echo_rgb 180 255 180 "git log --cc ${ancestor}..${commit_id_b} -p ${@:3}"

        git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Magenta)%cd %C(Reset)%s %C(Cyan)[%cn]%C(Red)%d" --cc "${ancestor}".."${commit_id_a}" -p "${@:3}"
        git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Magenta)%cd %C(Reset)%s %C(Cyan)[%cn]%C(Red)%d" --cc "${ancestor}".."${commit_id_b}" -p "${@:3}"

    fi
}
