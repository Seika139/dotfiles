echo ' ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
echo ' ┃'
echo ' ┃ .bashrc has been Read'
echo ' ┃ type "hlp" if you want some help'
echo ' ┃'
echo ' ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

# 上で使ってる太線は http://bubuzuke.s7.xrea.com/ISO10646/ruled.html で手に入れた

# direnv
eval "$(direnv hook bash)"

# gitignore.io のコマンド
function gi() {
    curl -sL https://www.toptal.com/developers/gitignore/api/$@
    echo
}

# 自作helpのトップ

function hlp() {
    echo 'help service produced by Seika139 !'
    echo
    echo 'code ~/.bashrc : bashrcをVSCodeで開く'
    echo
    echo 'gh    : git に関する help'
    echo 'bh    : bash に関する help'
    echo 'fh    : find に関する help'
    echo 'curlh : curl に関する help (Githubに飛びます)'
}

<<comment
git関連のエイリアス
comment

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

function bh() {
    echo 'source ~/.bashrc : .bashrcを再読み込み'
    echo
    echo 'ctrl + a : カーソルを左端に移動'
    echo 'ctrl + e : カーソルを右端に移動'
    echo 'ctrl + u : カーソルから左側を削除'
    echo 'ctrl + k : カーソルから右側を削除'
    echo ''
    echo '以下の2つはカスタムで追加 : https://qiita.com/YumaInaura/items/e242d1426756f4da1bab'
    echo 'alt + ← : カーソルを1単語分左に移動'
    echo 'alt + → : カーソルを1単語分右に移動'
}

function fh() {
    echo 'find ~/.bashrc : ファイルを探す'
    echo '-type f : ファイルのみを対象とする'
    echo '-type d : ディレクトリのみを対象とする'
    echo
    echo '-not / ! : 否定'
    echo 'find /test ! -name "*.py"'
    echo
    echo '-and / -a : and検索'
    echo 'find /test -name "*.sh" -a -mtime -1'
    echo
    echo '-or / -o : or検索'
    echo 'find /test -name "*.dat" -o -name "*.sh"'
    echo
    echo 'ファイルの中のテキストで検索'
    echo 'find ~/cms/app -type f -print | xargs grep "environment"'
    echo
    echo 'knowledges 内にあるmdファイルで「primary」の文字が含まれるものを探す'
    echo 'find ~/knowledges/ -name "*.md" -a -type f -print | xargs grep "primary"'
    echo
    echo 'さらに .py のファイルからのみ検索したい場合'
    echo 'find * -type f -print | xargs grep "all" --include="*.py"'
    echo
    echo 'さらにjsファイルのうち一部のファイルを除いて検索したい場合'
    echo 'find . -not -name "*plugins.js" -not -name "*bootstrap.min.js" -type f -print | xargs grep "export" --include="*.js"'
}

function curlh() {
    open https://github.com/Seika139/library/blob/master/curl/index.md
}
