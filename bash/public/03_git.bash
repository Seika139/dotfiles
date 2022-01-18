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

function lighten_git_ps1() {
    function __git_ps1() {
        # ブランチ名 : symbolic-ref はブランチ名しか出せないが、タグなどにも対応している describe よりは若干高速。お好みで選択
        local branch_name="$(git symbolic-ref --short HEAD 2>/dev/null)"
        # "$(git describe --all 2> /dev/null | sed 's/heads\///' 2> /dev/null)"

        # ブランチ名がなければ Git リポジトリ配下ではないと見なす・何も出力せず中断する
        if [ -z "$branch_name" ]; then
            exit 0
        fi

        # どうしても git status 以降のパフォーマンスが出ない・ブランチ名だけ出して終わらせるバージョン
        # echo " [$branch_name]"  # 省略版と一目で分かるようにブラケットを使用
        # exit 0
        # アンコメントした場合以下はデッドコード

        # -z : 対象が空文字なら true (空文字でない時に true にするなら -n)
        if [ -z "$GIT_PS1_SHOWDIRTYSTATE" ] && [ -z "$GIT_PS1_SHOWUNTRACKEDFILES" ]; then
            # オプションが未指定の場合はブランチ名のみ出力して終了する
            echo " ($branch_name)"
            exit 0
        fi

        # 何度もコマンドを実行したくないので変数に結果を控えておく・ブランチ名は必ず表示させることでチェックする
        local status=$(git status --short --branch --ignore-submodules 2>/dev/null)

        # 正常に git status が動作していなければエラーと表明して中断する
        if [ -z "$status" ]; then
            echo ' (ERROR)'
            exit 0
        fi

        # git status --short コマンドの結果を基にプロンプト用記号を付与する
        local unstaged  # add 前のファイル (行頭にスペース1つ開けて M or D)
        local staged    # add 済のファイル (行頭に A or M or D)
        local untracked # 新規作成ファイル (行頭に ??)

        # Unstaged・Staged
        if [ -n "$GIT_PS1_SHOWDIRTYSTATE" ]; then
            # Unstaged
            if [ -n "$(echo "$status" | cut -c 2 | tr -dc 'ACDMRU')" ]; then
                unstaged='*'
            fi

            # Staged
            if [ -n "$(echo "$status" | cut -c 1 | tr -dc 'ACDMRU')" ]; then
                staged='+'
            fi
        fi

        # Untracked
        if [ -n "$GIT_PS1_SHOWUNTRACKEDFILES" ] && [ -n "$(echo "$status" | tr -dc '?')" ]; then
            untracked='%'
        fi

        # ステータス文字列を結合する
        local files_status="$unstaged$staged$untracked"

        # いずれかの記号があれば先頭にスペースを入れておく
        if [ -n "$files_status" ]; then
            files_status=" $files_status"
        fi

        echo "<$branch_name$files_status>"
        exit 0
    }
    export -f __git_ps1
}
