#!/usr/bin/env bash

fix_home_path() {
    # 現在のHOMEパスを取得
    local current_home="$HOME"
    # echo "Fixing HOME path. Current HOME: $current_home"

    # ホームディレクトリが異常な形式かをチェック（エスケープシーケンスを含む場合）
    if [[ "$current_home" == *"\\"* || "$current_home" == *"\\x"* ]]; then
        echo "HOME contains escape sequences, attempting to fix..."
        # ユーザー名を取得
        local username="${USER:-$(whoami)}"
        # OSを検出
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
            # Git Bashなどの環境向け修正
            local new_home="/c/Users/${username}"
            export HOME="$new_home"
            printf "HOME path fixed (escape fix):\033[36m %s\033[0m ->\033[36m %s\033[0m" "$current_home" "$new_home"
            return
        fi
    fi

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
        echo "HOME path fixed (Windows path): $current_home -> $new_home"
        export HOME="$new_home"
    else
        printf ""
        # 正常な形式の場合は何も出力しない
        # echo "HOME path format looks OK: $current_home"
    fi
}

# ホームディレクトリパスを起動時に修正
fix_home_path

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


# それぞれのファイルで定義した設定を読み込む
DIRS=(
    "${BDOTDIR}/public"
    "${BDOTDIR}/private"
)

for dir in "${DIRS[@]}"; do
    # ディレクトリが存在することを確認する
    if [[ ! -d "${dir}" ]]; then
        echo "${dir} is not found"
        continue
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
