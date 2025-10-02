#!/usr/bin/env bash

# dotfileで作成したシンボリックリンクと ~/dotfiles を削除する

# dotfiles のルートディレクトリを取得
DOTFILES_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/" && pwd)"

util_bash="$DOTFILES_ROOT/bash/public/01_util.bash"
if [ ! -e "${util_bash}" ]; then
    echo "No such file ${util_bash}"
    exit 1
else
    # shellcheck source=/dev/null
    source "${util_bash}"
fi

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    # ref: https://qiita.com/kawaz/items/e909ae05ea67c60abb0e
    warn "このコマンドは source uninstall.sh で実行してください"
    exit
fi

echo_yellow 'dotfiles およびホームディレクトリに作成したシンボリックリンクをすべて削除します'
read -r -p "$(echo_yellow 'よろしいですか？ [y/N]: ')" ANS1
if [[ $ANS1 != [yY] ]]; then
    info "アンインストールをキャンセルしました"
    return 0
fi
unset ANS1

echo_orange 'GitHubにあげていないファイルに関しては二度と復元できません'
read -r -p "$(echo_orange 'それでもよろしいですか？ [y/N]: ')" ANS2
if [[ $ANS2 != [yY] ]]; then
    info "アンインストールをキャンセルしました"
    return 0
fi
unset ANS2

echo_red '保存していない場合に private フォルダに入っているファイルの復元が絶望的になります'
read -r -p "$(echo_red 'それでもよろしいですか？ [y/N]: ')" ANS3
if [[ $ANS3 != [yY] ]]; then
    info "アンインストールをキャンセルしました"
    return 0
fi
unset ANS3

# $HOME のシンボリックリンクを削除する
LINKED_FILES=(
    ".bash_profile"
    ".gitconfig"
    ".gitconfig.local"
    ".gitignore_global"
    ".gitmessage"
    ".cursor"
)

for FILE in "${LINKED_FILES[@]}"; do
    ABS_PATH=$(abs_path "${HOME}/${FILE}")
    if [[ -L "${ABS_PATH}" && $(readlink "${ABS_PATH}") = *dotfiles* ]]; then
        rm "${ABS_PATH}"
    fi
done
unset LINKED_FILES FILE ABS_PATH

# Claude 設定のシンボリックリンクを削除する
CLAUDE_LINKED_FILES=(
    ".claude/settings.json"
    ".claude/settings.local.json"
    ".claude/CLAUDE.md"
    ".claude/commands"
)

for FILE in "${CLAUDE_LINKED_FILES[@]}"; do
    ABS_PATH=$(abs_path "${HOME}/${FILE}")
    if [[ -L "${ABS_PATH}" && $(readlink "${ABS_PATH}") = *dotfiles* ]]; then
        echo "Removing Claude symlink: ${ABS_PATH}"
        rm "${ABS_PATH}"
    fi
done
unset CLAUDE_LINKED_FILES

cd "${HOME}" && rm -rf "${HOME}/dotfiles"
