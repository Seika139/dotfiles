#!/usr/bin/env bash

# dotfileで作成したシンボリックリンクと ~/dotfiles を削除する

source bash/public/01_util.bash

if [[ $BASH_SOURCE == "$0" ]]; then
    # ref: https://qiita.com/kawaz/items/e909ae05ea67c60abb0e
    warn "このコマンドは source uninstall.sh で実行してください"
    exit
fi

echo_yellow 'dotfiles およびホームディレクトリに作成したシンボリックリンクをすべて削除します'
read -p "$(echo_yellow 'よろしいですか？ [y/N]: ')" ANS1
if [[ $ANS1 != [yY] ]]; then
    info "アンインストールをキャンセルしました"
    return 0
fi
unset ANS1
echo_orange 'GitHubにあげていないファイルに関しては二度と復元できません'
read -p "$(echo_orange 'それでもよろしいですか？ [y/N]: ')" ANS2
if [[ $ANS2 != [yY] ]]; then
    info "アンインストールをキャンセルしました"
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
