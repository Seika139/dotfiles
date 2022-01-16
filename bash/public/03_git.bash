#!/usr/bin/env bash

# git のコマンドの補完ツール(mac用)
# ref : https://qiita.com/NorsteinBekkler/items/a0622ee6a39d08d61b72
# ref : https://smootech.hatenablog.com/entry/2017/02/23/102531

# TODO : windowsに対応

files=(
    "git-prompt.sh"
    "git-completion.bash"
)
if executable brew; then
    for file in "${files[@]}"; do
        full_path="$(brew --prefix)/etc/bash_completion.d/${file}"
        if [ -f "${full_path}" ]; then
            source "${full_path}"
        else
            warn "${full_path} が在りません"
        fi
    done
    unset file full_path
fi
unset files

# Gitブランチの状況を*+%で表示
GIT_PS1_SHOWDIRTYSTATE=true
GIT_PS1_SHOWUNTRACKEDFILES=true
GIT_PS1_SHOWSTASHSTATE=true
GIT_PS1_SHOWUPSTREAM=auto
