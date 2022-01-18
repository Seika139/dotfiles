#!/usr/bin/env bash

# dotfileで作成したシンボリックリンクと ~/dotfiles を削除する

source bash/public/01_util.bash
yellow 'dotfiles およびホームディレクトリに作成したシンボリックリンクをすべて削除します'
read -p "$(yellow 'よろしいですか？ [y/N]: ')" ANS1
if [[ $ANS1 != [yY] ]]; then
    return 0
fi
unset ANS1
orange 'GitHubにあげていないファイルに関しては二度と復元できません'
read -p "$(orange 'それでもよろしいですか？ [y/N]: ')" ANS2
if [[ $ANS2 != [yY] ]]; then
    return 0
fi
unset ANS2

# $HOME のシンボリックリンクを削除する
LINKED_FILES=(
    ".bash_profile"
    ".gitconfig"
    ".gitconfig.local"
    ".gitignore_global"
    ".gitmessage"
)

for FILE in ${LINKED_FILES[@]}; do
    ABS_PATH=$(abs_path ${HOME}/${FILE})
    if [[ -L ${ABS_PATH} && $(readlink ${ABS_PATH}) = *dotfiles* ]]; then
        rm ${ABS_PATH}
    fi
done
unset LINKED_FILES FILE ABS_PATH

cd $HOME
rm -rf "${HOME}/dotfiles"
