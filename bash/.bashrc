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

EOS

# 上で使ってる太線は http://bubuzuke.s7.xrea.com/ISO10646/ruled.html で手に入れた

fix_home_path() {
    # 現在のHOMEパスを取得
    local current_home="$HOME"

    # Windowsパス形式かチェック (C:\の形式)
    if [[ "$current_home" =~ ^[A-Za-z]:\\ ]]; then
        # ドライブレター取得
        local drive_letter="${current_home%%:*}"
        # 残りのパスを取得して\を/に変換
        local remaining_path="${current_home#*:}"
        # shellcheck disable=SC2001
        remaining_path=$(echo "$remaining_path" | sed 's;\\\+;/;g')

        # 新しいパスを組み立て
        local new_home="/${drive_letter,,}${remaining_path}"

        # $HOME を更新する
        echo "HOME path fixed: $HOME -> $new_home"
        export HOME="$new_home"
    else
        echo "HOME path is already in correct format: $HOME"
    fi
}

# それぞれのファイルで定義した設定を読み込む
DIRS=(
    "${BDOTDIR}/public"
    "${BDOTDIR}/private"
)

for dir in "${DIRS[@]}"; do
    # ディレクトリが存在することを確認する
    fix_home_path_flag=0
    if [[ ! -d "${dir}" ]]; then
        # fix_home_path をループ内で1度だけ実行する
        if [[ $fix_home_path_flag -eq 0 ]]; then
            fix_home_path
            fix_home_path_flag=1
            if [[ ! -d "${dir}" ]]; then
                echo "${dir} is not found"
                continue
            fi
        else
            echo "${dir} is not found"
            continue
        fi
    fi

    # .sh または .bash ファイルのみを検索して読み込む
    while IFS= read -r bashrc; do
        if [[ -f "${bashrc}" && "${bashrc}" =~ \.(sh|bash)$ ]]; then
            source "${bashrc}"
        fi
    done < <(find "${dir}" -type f)
done
unset DIRS dir bashrc fix_home_path_flag

cat <<EOS

Finish loading bashrc files
type "hlp" if you want some help

EOS
