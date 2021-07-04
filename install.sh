#!/usr/bin/env bash

# とりあえずのインストーラ

# NOTE: 必ずホームディレクトリにクローンするものとする
ROOT="${HOME}/dotfiles"
if [ ! -e $ROOT ]; then
    exit 1
fi

# シンボリックリンクを貼る
ln -sfv "${ROOT}/.bash_profile" ~/
ln -sfv "${ROOT}/.bashrc" ~/
ln -sfv "${ROOT}/.gitconfig" ~/
ln -sfv "${ROOT}/.gitignore_global" ~/
ln -sfv "${ROOT}/.gitmessage" ~/

# ln コマンドのオプション
# -s : シンボリックリンク(無いとハードリンクになる)
# -i : 別名となるパス名が存在する時は確認する
# -f : 別名となるパス名が存在する時も強制実行する
# -v : 詳細を表示

#-------------------------------------
# 1. .gituser
#-------------------------------------

# 無い場合は作成する
file="${ROOT}/.gituser"
if [ ! -e $file ]; then
    echo ".gituser を作成してください"
    read -p "git name = " name
    read -p "git email = " email
    cat <<GITUSER >$file
[user]
	name = ${name}
	email = ${email}

GITUSER
    unset name email
fi

# シンボリックリンクを貼る
ln -sfv $file ~/
unset file
