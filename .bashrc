#!/usr/bin/env bash

cat <<EOS
       )
    ／⌒⌒⌒ヽ                     ／⌒⌒⌒ヽ
   ﾉ ﾉﾉLL人ﾊ     きょう も     ((ﾉﾉ从从⭐️
  (_Cﾘﾟ‐ﾟﾉﾘ)     いちにち      ﾉ从ﾟヮﾟ人
  ﾉﾉ⊂)卯(つヽ    がんばろう   （(⊂ｿ辷ｿつ)
（( くzzzz> ))                  くzzzz>
     し∪                          し∪
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

.bashrc has been Read
type "hlp" if you want some help
EOS

# 上で使ってる太線は http://bubuzuke.s7.xrea.com/ISO10646/ruled.html で手に入れた

# less -M を常に有効化する
export LESS="-M"

#-------------------------------------
# 0. DOTFILES_ROOT
#-------------------------------------
# dotfilesのディレクトリを探す。
# このファイルがシンボリックリンクの場合は実体を参照する。
# Mac の readlink には -f オプション(再帰的な探索)がないため、
# 複数を経由したリンクだとうまく行かない。
#
# BASH_SOURCEは「呼び出されたファイル自身の絶対パス」でbashでしか使えない
# SEE: https://qiita.com/yudoufu/items/48cb6fb71e5b498b2532

if [ -L $BASH_SOURCE ]; then
    DOTFILES_ROOT=$(dirname $(readlink $BASH_SOURCE))
else
    DOTFILES_ROOT=$(dirname $BASH_SOURCE)
fi

#----------------------------------------------------------
# 1. 自分用のチートシートをまとめたファイルを見るためのコマンド集
#----------------------------------------------------------

# ファイルが存在する場合はその中身を出力する
function cat_file() {
    if [ -f $1 ]; then
        while IFS= read -r line; do
            echo -e $line
        done <$1
    else
        echo "No file exists with name of $1"
    fi
}

# 文字に色をつけたファイルをlessで表示する
# 一旦 cat_fileを挟まないとうまく色がつかないのでこうしている
function less_color() {
    cat_file $1 | less -R
}

# 自作helpのトップ
function hlp() {
    less ${DOTFILES_ROOT}/docs/home.txt
}

function hlp_less() {
    less ${DOTFILES_ROOT}/docs/linux/less.txt
}

function hlp_cursor() {
    less ${DOTFILES_ROOT}/docs/linux/cursor.txt
}

function hlp_find() {
    less ${DOTFILES_ROOT}/docs/linux/find.txt
}

function hlp_wc() {
    less ${DOTFILES_ROOT}/docs/linux/wc.txt
}

function hlp_curl() {
    open https://github.com/Seika139/library/blob/master/curl/index.md
}

#----------------------------------------------------------
# TODO
# コマンド履歴 p214
# ワイルドカード p39
#----------------------------------------------------------

#----------------------------------------------------------
# 2. direnv
#----------------------------------------------------------

eval "$(direnv hook bash)"

# gitignore.io のコマンド
function gi() {
    curl -sL https://www.toptal.com/developers/gitignore/api/$@
    echo
}

#----------------------------------------------------------
# 3. git関連のエイリアス
#----------------------------------------------------------

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
alias gl='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Cyan)%cd %C(Reset)%s %C(Blue)[%cn]%C(Red)%d" -10'
# git log … グラフ表示
alias glr='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Cyan)%cd %C(Reset)%s %C(Blue)[%cn]%C(Red)%d" --graph'
# git log … 修正ライン数が分かる
alias gll='git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"%C(Yellow)%h %C(Cyan)%cd %C(Reset)%s %C(Blue)[%cn]%C(Red)%d" --numstat'

alias gd='git diff'

alias gr='git remote'
alias grp='git remote prune origin'

alias gsl='git stash list'

function gh() {
    echo 'ssh-add ~/.ssh/id_rsa : sshキーを聞かれる時はこのコマンド'
    echo
    echo 'gi macOS,python >> */.gitignore'
    echo 'gitignore.ioで.gitignoreをお手軽に作成する'
    echo
    echo 'git diff >> gd'
    echo '--cached : addしたあとで差分を確認'
    echo '--stat   : ファイルの変更量を確認'
    echo '-w       : 改行コードや空白を無視'
    echo
    echo 'git remote >> gr'
    echo 'show origin            : remoteブランチを単純参照'
    echo 'prune --dry-run origin : remoteブランチでは削除されているが、ローカルに参照が残っているブランチを表示'
    echo 'prune origin >> grp    : すでに削除されているremoteブランチのローカル参照を削除してきれいにする'
    echo
    echo 'git log + option >> gl'
    echo 'gl  : git log をさらにシンプルに表示、直前10件'
    echo 'glr : グラフ表示'
    echo 'gll : ファイルごとの追加・削除行数を表示'
    echo '-- "*.vue" : vueファイルの変更があるコミットのみを対象にする'
    echo
    echo 'git stash (save)        : 変更をスタッシュにプッシュする'
    echo 'list >> gsl             : 退避した作業の一覧を見る'
    echo 'apply stash@{N}         : stash@{N}の作業をもとに戻す'
    echo 'apply stash@{N} --index : stageして退避した作業はstageされたまま戻る'
    echo 'drop stash@{N}          : stash@{N}の作業を消す stash@{N}を省略するとスタッシュの一番上を削除する'
    echo 'pop stash@{N}           : stash@{N}の作業をもとに戻すと同時に、退避作業の中から削除'
    echo 'clear                   : stashのリストを全て削除(要注意!)'
    echo
    echo 'git diff stash@{N}        : HEADとstashの差分を確認する'
    echo 'git diff stash@{N} [file] : ファイルの指定も可能'
    echo
    echo 'git remote -v           : 登録されているリモートリポジトリの確認'
    echo
    echo '--date=[option]                : git log や git stash list などで日付を表示するときに使う'
    echo 'local                           : Mon Nov 23 21:26:47 2020'
    echo 'iso-local                       : 2020-11-23 21:26:47 +0900'
    echo 'relative                        : 4 months ago'
    echo "format-local:'%Y/%m/%d %H:%M:%S : 2020/11/23 21:26:47 -> カスタム表示、localをつけないと世界標準時になりうる"
    echo
    echo 'git branch -D [branch_name]                       : ローカルのブランチを削除'
    echo 'git branch -m [old_branch_name] [new_branch_name] : ローカルのブランチ名を変更'
    echo 'git branch -m [new_branch_name]                   : 現在のローカルブランチ名を変更する'
    echo 'git push origin :[branch_name]                    : リモートのブランチを削除'
}
