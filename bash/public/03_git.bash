#!/usr/bin/env bash

# git のコマンドの補完ツール(mac用)
# ref : https://qiita.com/NorsteinBekkler/items/a0622ee6a39d08d61b72
# ref : https://smootech.hatenablog.com/entry/2017/02/23/102531

# windowsのGitBashにも対応した

if executable brew; then
    for file in "git-prompt.sh" "git-completion.bash"; do
        full_path="$(brew --prefix)/etc/bash_completion.d/${file}"
        if [ -e "${full_path}" ]; then
            source "${full_path}"
        else
            warn "${full_path} が存在しません"
        fi
    done
    unset file full_path
elif is_msys; then
    full_path= "/c/Program Files/Git/etc/profile.d/git-prompt.sh"
    if [ ! -e ${full_path} ]; then
        warn "${full_path} が存在しません(違う場所にある可能性もあります)"
    fi
fi

# Gitブランチの状況を*+%で表示
GIT_PS1_SHOWDIRTYSTATE=true
GIT_PS1_SHOWUNTRACKEDFILES=true
GIT_PS1_SHOWSTASHSTATE=true
GIT_PS1_SHOWUPSTREAM=auto
