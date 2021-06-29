#!/usr/bin/env bash

# とりあえずのインストーラ
# シンボリックリンクを貼る

ln -sfv "${PWD}/.bash_profile" ~/
ln -sfv "${PWD}/.bashrc" ~/
ln -sfv "${PWD}/.gitignore_global" ~/

# ln コマンドのオプション
# -s : シンボリックリンク(無いとハードリンクになる)
# -i : 別名となるパス名が存在する時は確認する
# -f : 別名となるパス名が存在する時も強制実行する
# -v : 詳細を表示
